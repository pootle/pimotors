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

def classrunner(wrappedClassName, ticktime, procend, kwacktimeout=None, timeoutfunction=None, **kwargs):
    """
    This function is the target for a thread. It runs the wrapped class with a ticker function.
    
    wrappedClassName : hierarchic name of target class - see logger.makeClassInstance for details.
    
    ticktime         : period to use for the ticker function
    
    procend          : pipe like object for communication back to originating object

    kwacktimeout     : provide keep awake monitor, that checks for incoming calls and resets a timer....
                        if None, no monitoring
                        else inactivity period that triggers call to wrapped  class function

    timeoutfunction  : name of the member function to call if inactivity timeout
    
    kwargs           : dict with keyword args to instantiate the class
    
    """
    ci=logger.makeClassInstance(wrappedClassName, **kwargs)
    procend.send(('OK',type(ci).__name__, -1))
    waittime=0
    cpustart=time.process_time()
    clockstart=time.time()
    lastincoming=clockstart
    nexttime=clockstart+ticktime
    running=True
    tickcount=0
    print('using timeout %3.1f to call %s, tick is %3.2f' % (0 if kwacktimeout is None else kwacktimeout, str(timeoutfunction), ticktime))
    while running:
        delay=nexttime-time.time()
        while delay>0:
            pstart=time.time()
#            if tickcount < 50:
#                print('delay is %2.2f' % delay)
            r,w,e=select.select([procend],[],[], delay)
            tnow=time.time()
            waittime+=(tnow-pstart)
            if r:
                lastincoming=tnow
                mname, sync, rid, kwargs = procend.recv()
                print('reseting lastincoming for ' + sync)
                if mname is None:
                    if sync=='k':
                        pass # trivial no-op just to reset the keep awake timer
                    if sync=='x':
                        procend.send(('OK',
                            {   'elapsed' : time.time()-clockstart,
                                'cputime' : time.process_time()-cpustart,
                                'idletime': waittime,
                                'ticks'   : tickcount},
                            rid))
                    elif sync=='e':
                        running=False
                else:
                    try:
                        f=getattr(ci, mname)
                    except AttributeError:
                        procend.send(('NoMethod', '>'+str(mname)+'>', rid))
                        f=None
                    if not f is None:
                        if sync in ('s', 'e', 'a'):
                            try:
                                resp=f(**kwargs)
                                if sync=='s':
                                    procend.send(('OK', resp, rid))
                            except:
                                exc_type, exc_value, exc_traceback = sys.exc_info()
                                procend.send(('MethodException', 
                                    str(exc_type) + '\n' + str(exc_value) + '\n' + ''.join(traceback.format_tb(exc_traceback)), rid))
                            if sync == 'e':
                                running=False
                        else:
                            x=17/0
            delay=nexttime-time.time()
        else:
            if not kwacktimeout is None and time.time()>(lastincoming+kwacktimeout):
                tmeth=getattr(ci, timeoutfunction)
                print('timeout calls', tmeth)
                tmeth()
                lastincoming=time.time()+3
#            else:
#                print('zzzzzzzzzzzzz', kwacktimeout, (lastincoming+kwacktimeout)-time.time())
            ci.ticker()
            tickcount+=1
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
    def __init__(self, wrappedClassName, ticktime, procName=None,
            locallogging={'logtypes':(('life',{'filename':'stdout'}),)}, **kwargs):
        """
        fires up a process which will create the wrapped class
        """
        self.stubendpipe, procendpipe = Pipe()
        self.proc=Process(target=classrunner, name=procName,
                args=(wrappedClassName, ticktime, procendpipe), kwargs=kwargs)
        self.msgInCount = 0
        self.msgOutCount = 0
        self.proc.start()
        self.laststatus, self.startinf, self.lastoutid = self.stubendpipe.recv()
        self.running=self.laststatus=='OK' and self.lastoutid==-1
        if 'name' in locallogging:
            super().__init__(**locallogging)
        else:
            super().__init__(name='stub for %s' % (wrappedClassName), **locallogging)

    def logCreate(self):
        """
        override instance create message with a better message
        """
        if self.running:
            self.log(ltype='life', otype=type(self).__name__, lifemsg='created remote process %s as instance of %s' % (self.proc.name, self.startinf))
        else:
            self.log(ltype='life', otype=type(self).__name__, lifemsg='Process failed to initialise class (%s): %s' % (self.laststatus, self.startinf))

    def runOnProc(self, method, sync, **kwargs):
        """
        stub methods call this to send info through the pipe to run the 'real' version of the method.
        
        method  : the name of the method to run
        
        sync    : 's' to run the method synchronously and return and results to the caller
                  'a' to run method asynchronously and return immediately
                  'e' to shut down the remote process by exiting the control loop and thus the process
                      the closedown method of the class can be run if 'method' not None (plus any kwargs...)    
        """
        if self.running:
            self.stubendpipe.send((method, sync, self.msgOutCount, kwargs))
            rid=self.msgOutCount
            self.msgOutCount+=1
            if sync=='s':
                instatus, inresponse, outid = self.stubendpipe.recv()
                if outid==rid:
                    if instatus=='OK':
                        return inresponse
                    else:
                        print('response from remote: %s' % instatus)
                        print(inresponse)
                else:
                    print('message id mismatch, expected %d got %d' % (rid, outid))
            elif sync=='a':
                pass
            elif sync=='e':
                self.stubend()
            else:
                raise ValueError('unknown sync value %s' % sync)
        else:
            x=17/0

    def sendkwac(self):
        if self.running:
            print('webserve sending kwac')
            self.stubendpipe.send((None,'k',self.msgOutCount,None))
            self.msgOutCount+=1

    def getProcessStats(self):
        self.stubendpipe.send((None, 'x', self.msgOutCount, None))
        rid=self.msgOutCount
        self.msgOutCount+=1
        instatus, inresponse, outid = self.stubendpipe.recv()
        if instatus=='OK' and outid==rid:
            return inresponse
        else:
            print('================', instatus, outid, rid, inresponse)
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