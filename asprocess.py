#!/usr/bin/python3
"""
This module enables an existing class to be instantiated in a new process (multi-procesing process) so it can run
autonomously.

The existing class does not need to be changed or be aware that this is happening.

A stub class, which inherits from runAsProcess in this module, is required, this acts as a stub, and should provide 
stub methods that the originating process' code can call as if the class were a normal in-process class.

Any exceptions in the new process are passed back through the pipe to be handled in the originating process, currently
just be printing relevant information.

Function calls - which return objects - are run synchronously - that is the calling process waits for a response from
the new process and returns the result.

Calls with no return objects will return immediately - they do not wait for the remote end.

There is no capability for callbacks or other notifications from new process in this version.
"""
from multiprocessing import Pipe, Process
import select
import importlib
import os, sys, traceback
import logger
import time

def classrunner(wrappedModuleName, wrappedClassName, ticktime, procend, kwargs):
    try:
        tmod=importlib.import_module(wrappedModuleName)
        cls=getattr(tmod, wrappedClassName)
    except ImportError as i:
        procend.send(('ImportError', 'failed ' + i.msg, -1))
        time.sleep(.5)
        return
    except AttributeError:
        procend.send(('ClassError', 'failed to find class ' + wrappedClassName.__repr__(), -1))
        time.sleep(.5)
        return
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        procend.send(('Moduleerror', str(exc_type) + '\n' + str(exc_value) + '\n' + ''.join(traceback.format_tb(exc_traceback)), -1))
        time.sleep(.5)
        return
    try:
        ci=cls() if kwargs is None else cls(**kwargs)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        procend.send(('ConstructionError', str(exc_type) + '\n' + str(exc_value) + '\n' + ''.join(traceback.format_tb(exc_traceback)), -1))
        time.sleep(.5)
        return
    procend.send(('OK',type(ci).__name__, -1))
    nexttime=time.time()+ticktime
    while True:
        delay=nexttime-time.time()
        while delay>0:
            r,w,e=select.select([procend],[],[], delay)
            if r:
                mname, sync, rid, kwargs = procend.recv()
                try:
                    f=getattr(ci, mname)
                except AttributeError:
                    procend.send(('NoMethod', mname,rid))
                    f=None
                if not f is None:
                    if sync:
                        try:
                            resp=f(**kwargs)
                            procend.send(('OK', resp, rid))
                        except:
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            procend.send(('MethodException', 
                                str(exc_type) + '\n' + str(exc_value) + '\n' + ''.join(traceback.format_tb(exc_traceback)), rid))
                    else:
                        x=17/0
                delay=nexttime-time.time()
        else:
            ci.ticker()
            nexttime+=ticktime

class runAsProcess(logger.logger):
    """
    This class provides a wrapper to run a class which uses polling ( a ticker) as a separate process, using a pair of pipes to communicate.
    
    Inherit from this class to implement any of the methods that need to be available via the pipes, it can then act as a stub 
    for the 'real' class which will be running in a new multithreading process.
    
    These methods can be synchronous (in which case the local thread is held until a response is received) - or asynchronous in which case 
    the request is sent off and the method returns immediately.
    
    (TODO) The new process, running the wrapped class, can also send notifications back to this class which will in turn call methods the inheriting
    class should provide.
    
    Pipes are used as this is a 1:1 relationship, and it will allow an easy move to using sockets if a remote solution is later needed.
    """
    def __init__(self, wrappedModuleName, wrappedClassName, ticktime, procName=None,
            locallogging={'logtypes':(('life',{'filename':'stdout'}),)}, **kwargs):
        """
        fires up a process which will create the wrapped class
        """
        self.stubendpipe, procendpipe = Pipe()
        self.proc=Process(target=classrunner, name=procName,
                args=(wrappedModuleName, wrappedClassName, ticktime, procendpipe), kwargs=kwargs)
        self.msgInCount = 0
        self.msgOutCount = 0
        self.proc.start()
        self.laststatus, self.startinf, self.lastoutid = self.stubendpipe.recv()
        self.running=self.laststatus=='OK' and self.lastoutid==-1
        if 'name' in locallogging:
            super().__init__(**locallogging)
        else:
            super().__init__(name='stub for %s.%s' % (wrappedModuleName, wrappedClassName), **locallogging)

    def logCreate(self):
        """
        override instance create message with a better message
        """
        if self.running:
            self.log(ltype='life', otype=type(self).__name__, lifemsg='created remote process %s as instance of %s' % (self.proc.name, self.startinf))
        else:
            self.log(ltype='life', otype=type(self).__name__, lifemsg='Process failed to initialise class (%s): %s' % (self.laststatus, self.startinf))

    def runOnProc(self, method, sync, **kwargs):
        if self.running:
            self.stubendpipe.send((method, sync, self.msgOutCount, kwargs))
            if sync:
                rid=self.msgOutCount
                self.msgOutCount+=1
                instatus, inresponse, outid = self.stubendpipe.recv()
                if outid==rid:
                    if instatus=='OK':
                        return inresponse
                    else:
                        print('response from remote: %s' % instatus)
                        print(inresponse)
                else:
                    print('message id mismatch, expected %d got %d' % (rid, outid))
            else:
                self.msgOutCount+=1
        else:
            x=17/0

    def stubend(self):
        self.proc.join(timeout=4)
        if self.proc.is_alive():
            self.log(ltype='life', otype=type(self).__name__, lifemsg='process still running - get out the big chopper')
            self.proc.terminate()
            self.proc.join(timeout=4)
            if self.proc.is_alive():
                self.log(ltype='life', otype=type(self).__name__, lifemsg='process still running - I give up')
            else:
                self.log(ltype='life', otype=type(self).__name__, lifemsg='process gone now!')
        else:
            self.log(ltype='life', otype=type(self).__name__, lifemsg='process has completed')