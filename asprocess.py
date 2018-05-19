#!/usr/bin/python3
"""
This module enables an existing class to be instantiated in a new process (multi-procesing process) so it can run
autonomously.

The existing class does not need to be changed or be aware that this is happening.

The existing class is expected either to be running some sort of polling system, or triggering on other events. In either case
it must not block for significant periods of time, either in its own execution, or when processing the requests from the stub class. 

A stub class, which inherits from runAsProcess in this module, is required, this acts as a stub, and should provide 
stub methods that the originating process' code can call as if the class were a normal in-process class.

Any exceptions in the new process are passed back through the pipe to be handled in the originating process, currently
just be printing relevant information.

Function calls - which return objects - are run synchronously - that is the calling process waits for a response from
the new process and returns the result.

Calls with no return objects will return immediately - they do not wait for the remote end.

There is a very simple 1-of mechanism for notifications back.
"""
from multiprocessing import Pipe, Process
import select
import importlib
import os, sys, traceback
import logger
import time

def classrunner(wrappedClassName, ticktime, procend, kwacktimeout=None, timeoutfunction=None, monitortime=None, **kwargs):
    """
    This function is the target for a new process. It runs the wrapped class,calling method ticker every ticktime.
    
    wrappedClassName : hierarchic name of target class - see logger.makeClassInstance for details.
    
    ticktime         : period to use for the ticker function
    
    procend          : pipe like object for communication back to originating object

    kwacktimeout     : provide keep awake monitor, that checks for incoming calls and resets a timer....
                        if None, no monitoring
                        else inactivity period that triggers call to wrapped  class function

    timeoutfunction  : name of the member function to call if inactivity timeout

    monitortime      : time in seconds at which we will report process performance stats
    
    kwargs           : dict with keyword args to instantiate the class
    
    """
    def sendback(tupleish):
#        print('sending from asprocess', tupleish[0], tupleish[2])
        procend.send(tupleish)

    ci=logger.makeClassInstance(wrappedClassName, **kwargs)
    print("classrunner using", type(ci).__name__)
    sendback(('OK',type(ci).__name__, -2))
    waittime=0                      # the time spent waiting in select
    msgtime=0                       # the time spent processing messages
    tickertime=0                    # the time spent in the tick handler
    cpustart=time.process_time()
    clockstart=time.perf_counter()
    lastincoming=clockstart         # last time we got a message = used for the keep awake timout
    nexttime=clockstart+ticktime
    if not monitortime is None:
        assert isinstance(monitortime, (float, int)) and .5 <= monitortime < 61
        intvlwaitstart=0
        intvlcpustart=cpustart
        intvlclockstart=clockstart
        intvlnexttime=intvlclockstart+monitortime
        intvltickstart=0
        intvlmsgtime=0
        intvltickertime=0
        intvltickerticks=[]
    running=True
    tickcount=0
    print('using timeout %3.1f to call %s, tick is %3.2f' % (0 if kwacktimeout is None else kwacktimeout, str(timeoutfunction), ticktime))
    loopstartat=time.perf_counter()
    trackdelays=[]
    trackselectcalls=0
    tracktickercalls=0
    while running:
        delay=nexttime-loopstartat
        trackdelays.append(delay)
        if delay>0:
            r,w,e=select.select([procend],[],[], delay)
            trackselectcalls += 1
            tnow=time.perf_counter()
            sleeptime=tnow-loopstartat
            waittime+=sleeptime
            if r:
                lastincoming=tnow
                mname, sync, rid, kwargs = procend.recv()
                if sync=='k':  # trivial no-op used to reset keep awake timer for example
                    pass
                elif sync=='x': # send stats on total process run time
                    sendback(('OK',
                        {   'elapsed' : time.perf_counter()-clockstart,
                            'cputime' : time.process_time()-cpustart,
                            'idletime': waittime,
                            'ticks'   : tickcount,
                            'rid'     : rid},
                        rid))
                elif sync=='e':
                    running=False
                else:
                    try:
                        f=getattr(ci, mname)
                    except AttributeError:
                        sendback(('NoMethod', '>'+str(mname)+'>', rid))
                        f=None
                    if not f is None:
                        if sync in ('s', 'a'):
                            try:
                                resp=f(**kwargs)
                                if sync=='s':
                                    sendback(('OK', resp, rid))
                            except:
                                exc_type, exc_value, exc_traceback = sys.exc_info()
                                sendback(('MethodException', 
                                    str(exc_type) + '\n' + str(exc_value) + '\n' + ''.join(traceback.format_tb(exc_traceback)), rid))
#                                raise
                        else:
                            sendback(('CommandException', sync, rid))
                loopstartat=time.perf_counter()
                msgtime += (loopstartat-tnow)
            else:
                loopstartat=time.perf_counter()
        else:
            tracktickercalls+=1
            ci.ticker()
            tnow=time.perf_counter()
            thistick=tnow-loopstartat
            tickertime += tnow-loopstartat
            if not kwacktimeout is None and tnow>(lastincoming+kwacktimeout):
                tmeth=getattr(ci, timeoutfunction)
                tmeth()
                lastincoming=tnow+3
            if not monitortime is None:
                if False:
#                if tnow > intvlnexttime:
                    print('select called %d times, ticker called %d times' % (trackselectcalls, tracktickercalls))
                    print(', '.join(['%4.3f' % x for x in trackdelays]))
                    trackselectcalls=0
                    tracktickercalls=0
                    trackdelays.clear()
                    proctime=time.process_time()
                    sendback(('OK',
                        {   'tstamp'    : tnow,
                            'interval'  : tnow-intvlclockstart,
                            'cputime'   : proctime-intvlcpustart,
                            'idletime'  : waittime-intvlwaitstart,
                            'ticks'     : tickcount-intvltickstart,
                            'msgtime'   : msgtime-intvlmsgtime,
                            'tickertime': tickertime-intvltickertime,
                            'rid'       : -1},
                        -1))
                    intvlclockstart=tnow
                    intvlcpustart=proctime
                    intvlwaitstart=waittime
                    intvltickstart=tickcount
                    intvlnexttime+=monitortime
                    intvltickertime=tickertime
                    intvlmsgtime=msgtime
            tickcount+=1
            nexttime+=ticktime
            loopstartat=time.perf_counter()

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
        self.running=self.laststatus=='OK' and self.lastoutid==-2
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
                  'k' no-op used to provide keep awake ticks
                  'x' return process stats (since process start
        """
        if self.running:
            self.stubendpipe.send((method, sync, self.msgOutCount, kwargs))
            rid=self.msgOutCount
            self.msgOutCount+=1
            if sync=='s' or sync =='x':
                instatus, inresponse, outid = self.stubendpipe.recv()
                while outid==-1:
                    self.handleprocstats(inresponse)
                    instatus, inresponse, outid = self.stubendpipe.recv()
                if outid==rid:
                    if instatus=='OK':
                        return inresponse
                    else:
                        print('response from remote: %s' % instatus)
                        print(inresponse)
                else:
                    print('message id mismatch, expected %d got %d' % (rid, outid))
            elif sync in ('a','k'):
                pass
            elif sync=='e':
                self.stubend()
            else:
                raise ValueError('unknown sync value %s' % sync)
            if self.stubendpipe.poll():
                instatus, inresponse, outid = self.stubendpipe.recv()
                if outid==-1:
                    self.handleprocstats(inresponse)
                else:
                    print('unexpected message from remote class', instatus, outid, inresponse)
                    x=17/0
        else:
            x=17/0

    def sendkwac(self):
        self.runOnProc(None,'k')

    def getProcessStats(self):
        return self.runOnProc(None,'x')

    def handleprocstats(self, statsmsg):
        """
        called when procstats message received - override to do something more appropriate
        """
        print(statsmsg)

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