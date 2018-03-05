#!/usr/bin/python3

import time
import dcmotorbasic

class motoranalyse(dcmotorbasic.motor):
    """
    extends the standard motor class with methods to test and log the results
    """
    def findMaxrpm(self, repeat=4, **kwargs):
        """
        Test motor for maximum speed
        
        The motor is set to full speed (max pwm value) and run for interval seconds and the tally count per second and hence rpm is calculated over that interval.
        The test is repeated repeat times.
        
        direction: 'both', 'forward', 'backward'
        
        delay:      time in seconds after starting before we start to measure speed
        
        interval:   time over which speed is measured

        repeat:     number of times test is repeated
        """
        fmstate=self.setupfmstate(testname='maxrpm', tickfunc=self.maxrpmtick, **kwargs)
        fmstate['repeat'] = repeat
        fmstate['count'] = 0
        fmstate['phase'] = 'waitstop'
        fmstate['rtemplate']['frequ'] =100
        fmstate['rtemplate']['pw']=self.maxDC()
        self.frequency(100)
        self.DC(0)

    def maxrpmtick(self, fmstate):
        tnow=time.time()
        if fmstate['phase']=='waitstop':
            if self.motorpos.lasttallydiff==0:    # wait for motor to show no movement, then move to windup phase
                fmstate['phase']='windup'
                fmstate['motorstart']=tnow
                fmstate['protime']=fmstate['motorstart']+fmstate['delay']
                fmstate['peaked']=0
                fmstate['peakticks']=0
                fmstate['tallylist']=[]
                self.DC(self.mdrive.range if fmstate['curdir']=='f' else -self.mdrive.range)
            elif tnow > fmstate['protime']:# if motor hasn't stopped after delay there is a problem
                fmstate=self.rundone(msg='motor not stopped - abort', runok=False)
        elif fmstate['phase']=='windup':
            if tnow > fmstate['protime']:
                if self.motorpos.lasttallydiff==0:
                    fmstate=self.rundone(msg='max speed scan: no motion detected - abort', runok=False)
                else:
                    fmstate=self.rundone(msg='motor speed not stable after %d seconds, peakstarts %d \n %s' % (
                        fmstate['delay'], fmstate['peaked'], str(fmstate['tallylist'])), runok=False)
            else:
                newticks=self.motorpos.lasttallydiff
                fmstate['tallylist'].append(self.motorpos.lasttallydiff)
                if newticks <= fmstate['peakticks']:
                    if fmstate['peaked'] > 20:
                        fmstate['phase']='tallyho'
                        fmstate['protime']=tnow+fmstate['interval']
                        fmstate['windup time']=tnow-fmstate['motorstart']
                        fmstate['tallylist']=[newticks]
                        fmstate['motorstart']=tnow
                    else:
                        fmstate['peaked']+=1
                        fmstate['peakticks']=0
                else:
                    fmstate['peakticks']=newticks
        elif fmstate['phase']=='tallyho':
            fmstate['tallylist'].append(self.motorpos.lasttallydiff)
            if tnow > fmstate['protime']:
                tps=abs(sum(fmstate['tallylist'])/(self.motorpos.lasttallytime-fmstate['motorstart']))
                rpm=tps/self.motorpos.ticksperrev*60
                if fmstate['logto'] is None:
                    print('a')
                    print('a')
                    print('a')
                    print('a')
                    print('a')
                    print('a')
                    print('a')
                    print('a')
                    print('a')
                    print('max speed test %d: %3.2ftps, %4.1frpm, %2.3f runup time  ' % (fmstate['count'], tps, rpm, fmstate['windup time']))
                else:
                    newres=fmstate['rtemplate'].copy()
                    newres['direc']=fmstate['curdir']
                    newres['tps']=tps
                    newres['counts']=fmstate['count']
                    newres['rpm']=rpm
                    newres['tstamp']=self.motorpos.lasttallytime
                    self.log(ltype=fmstate['logto'], **newres)
                fmstate['count'] += 1
                if fmstate['count'] > fmstate['repeat']:
                    fmstate['curdir']=fmstate['nextdir']
                    if fmstate['curdir']==None:
                        fmstate=self.rundone(msg='max speed test run complete', runok=True)
                    else:
                        fmstate['nextdir']=None
                        fmstate['protime']=tnow+fmstate['delay']
                        fmstate['phase']='waitstop'
                        fmstate['count']=1
                        self.DC(0)
                else:
                    self.DC(0)
                    fmstate['protime']=tnow+fmstate['delay']
                    fmstate['phase']='waitstop'
        else:
            print('WHAT',fmstate['phase'])
            x=17/0
        return fmstate

    def setupfmstate(self, tickfunc, testname, direction='both', tick=.05, delay=12, interval=2, oncomplete=None, logtype=None):
        """
        useful routine to setup standard parts of the state for tests / measures and the log entries they produce.
        """
        assert direction in ('both', 'forward', 'backward')
        assert delay > .1
        assert interval > .1
        fmstate={
            'rtemplate' : {'motor': self.name, 'testname': testname, 'direc':'f', 'runid':time.time(),
                           'tick': tick, 'tstamp':0},
            'protime': time.time()+delay,
            'delay': delay,
            'interval': interval,
            'curdir': 'f',
            'nextdir': None,
            'runid': time.time(),
            'oncomplete': oncomplete,
            'logto': logtype,
                }
        if direction=='backward':
            fmstate['curdir']='b'
        elif direction=='both':
            fmstate['nextdir']='b'
        self.longactfunc=tickfunc
        self.longactstate=fmstate
        return fmstate

    def rundone(self, msg, runok):
        fmstate=self.longactstate
        if not fmstate['oncomplete'] is None:
            fmstate['oncomplete'](runok)
        self.longactstate=None
        self.stop()
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print('Z')
        print(msg)        
        return None
