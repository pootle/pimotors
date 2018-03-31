#!/usr/bin/python3

import time
import dcmotorbasic

class motoranalyse(dcmotorbasic.motor):
    """
    extends the standard motor class with methods to test and log the results
    """
    def findMaxrpm(self, **kwargs):
        if self.postick is None:
            x=17/0
        self.addTicker(tickgen=self.doMaxRPM(**kwargs), tickID='maxRPM', ticktick=1, priority=10)

    def doMaxRPM(self, direction='both', repeat=2, interval=2, delay=4, logtype='analyser', **kwargs):
        rtemplate = {'motor': self.name, 'testname': 'maxrpm', 'ltype': logtype, 'direc':'f', 'runid':time.time(),
                     'tstamp':0, 'maxdc': self.maxDC(), 'tallylist': 0}
        rcount=0
        while rcount <= repeat:
            dlist={'both':'fb', 'forward':'f', 'backward':'b'}[direction]
            while len(dlist) > 0:
                # wait for stop
                print('run', rcount, 'is', dlist[0])
                timeout=time.time()+delay*5
                self.DC(0)
                mp=self.motorpos
                while mp.lasttallydiff != 0 and mp.lasttallytime < timeout:
                    yield()                
                if mp.lasttallydiff!= 0:
                    self.analrunends('FAIL','motor failed to stop (%d)' % mp.lasttallydiff)
                    raise StopIteration()
                dcval = self.maxDC()
                if dlist[0]=='b':
                    dcval = -dcval
                if self.invert(None):
                    dcval = -dcval
                self.DC(dcval)
                timeout=time.time()+delay
                while mp.lasttallytime < timeout:
                    yield()
                if mp.lasttallydiff == 0:
                    self.analrunends('FAIL','motor no movement detected')
                motorstart=mp.lasttallytime
                tallylist=[]
                timeout=time.time()+interval
                while mp.lasttallytime < timeout:
                    yield()
                    tallylist.append(mp.lasttallydiff)
                tps=abs(sum(tallylist)/(mp.lasttallytime-motorstart))
                rpm=tps/mp.ticksperrev*60
                print(type(rtemplate))
                newres=rtemplate.copy()
                newres['direc']=dlist[0]
                newres['tps']=tps
                newres['rpm']=rpm
                newres['tstamp']=mp.lasttallytime
                newres['tallylist']=tallylist
                self.log(**newres)
                dlist=dlist[1:]
            rcount += 1
        self.analrunends('OK', 'maxRPM run complete')

    def analrunends(self, isOK, msg):
        self.stop()
        print('')
        print('')
        print('')
        print('')
        print(isOK, msg)        

    def mapdcToRPM(self, repeat=4, frequency=None, minDCfwd=30, minDCback=30, **kwargs):
        """
        Test motor for maximum speed
        
        The motor is set to full speed (max pwm value) and run for interval seconds and the tally count per second and hence rpm is calculated over that interval.
        The test is repeated repeat times.
        
        direction: 'both', 'forward', 'backward'
        
        frequency: frequency to use for test
        
        delay:      time in seconds after starting before we start to measure speed
        
        interval:   time over which speed is measured

        minDCfwd:   lowest DC value to use (forward).
        
        minDCback:  lowest DC value to use (backward).
        
        repeat:     number of times test is repeated
        """
        fmstate=self.setupfmstate(testname='mapDCtoRPM', tickfunc=self.mapdrtick, **kwargs)
        fmstate['repeat'] = repeat
        fmstate['count'] = 0
        fmstate['phase'] = 'waitstop'
        if self.mdrive.invert(None):
            fmstate['minDCf'] = minDCfwd
            fmstate['minDCb'] = minDCback            
        else:
            fmstate['minDCf'] = minDCfwd
            fmstate['minDCb'] = minDCback
        fmstate['rtemplate']['frequ'] = self.frequency(frequency)
        self.DC(0)
        fmstate['protime'] = time.time()+kwargs['delay']*10,

    def mapdrtick(self, fmstate):
        tnow=self.motorpos.lasttallytime
        if fmstate['phase']=='waitstop':
            if self.motorpos.lasttallydiff==0:    # wait for motor to show no movement, then move to windup phase
                fmstate['phase']='windup'
                fmstate['protime']=tnow+fmstate['delay']*4
                if self.mdrive.invert(None) == (fmstate['curdir']=='f'):
                    fmstate['dcchange']=-1
                else:
                    fmstate['dcchange']=1
                fmstate['DC'] = fmstate['minDCf'] if fmstate['dcchange']==1 else -fmstate['minDCb']
                self.DC(fmstate['DC'])
            else:
                print(self.name, self.motorpos.lasttallydiff)
                if tnow > fmstate['protime']:# if motor hasn't stopped after delay there is a problem
                    fmstate=self.rundone(msg='motor not stopped - abort', runok=False)
        elif fmstate['phase']=='windup':
            if tnow > fmstate['protime']:
                if self.motorpos.lasttallydiff==0:
                    if abs(fmstate['DC']) <100:
                        # try faster
                        fmstate['DC']+=fmstate['dcchange']
                        self.DC(fmstate['DC'])
                        fmstate['protime']=tnow+fmstate['delay']
                    else:
                        fmstate=self.rundone(msg='map speed scan: no motion detected (DC %d) - abort' % fmstate['DC'], runok=False)
                else:
                    fmstate['tallylist']=[]
                    fmstate['tallystart']=tnow
                    fmstate['protime']=tnow+fmstate['interval']
                    fmstate['phase']='tallyho'
        elif fmstate['phase']=='tallyho':
            fmstate['tallylist'].append(self.motorpos.lasttallydiff)
            if tnow > fmstate['protime']:
                tps=abs(sum(fmstate['tallylist'])/(self.motorpos.lasttallytime-fmstate['tallystart']))
                rpm=tps/self.motorpos.ticksperrev*60
                newres=fmstate['rtemplate'].copy()
                newres['direc']='f' if fmstate['dcchange']==1 else 'b'
                newres['DC'] = fmstate['DC']
                newres['tps']=tps
                newres['rpm']=rpm
                newres['tstamp']=self.motorpos.lasttallytime
                newres['tallylist']=fmstate['tallylist']
                self.log(ltype='analyser', **newres)
                fmstate['DC']+=fmstate['dcchange']
                if abs(fmstate['DC']) > self.mdrive.range:
                    self.DC(0)
                    fmstate['protime']=tnow+fmstate['delay']*10
                    if fmstate['nextdir'] is None:
                        fmstate['count']+=1
                        if fmstate['count'] >= fmstate['repeat']:
                            fmstate=self.rundone(msg='map speed scan: test run complete', runok=True)
                        else:
                            self.DC(0)
                            fmstate['mode']='waitstop'
                            fmstate['curdir']='f'
                            fmstate['nextdir']=None
                            if fmstate['requdir']=='backward':
                                fmstate['curdir']='b'
                            elif fmstate['requdir']=='both':
                                fmstate['nextdir']='b'
                    else:
                        fmstate['curdir'] = fmstate['nextdir']
                        fmstate['nextdir']=None
                        fmstate['phase'] = 'waitstop'
                else:
                    self.DC(fmstate['DC'])
                    fmstate['protime']=tnow+fmstate['delay']
                    fmstate['phase']='windon'
        elif fmstate['phase']=='windon':
            if tnow > fmstate['protime']:
                fmstate['tallylist']=[]
                fmstate['tallystart']=tnow
                fmstate['protime']=tnow+fmstate['interval']
                fmstate['phase']='tallyho'
                
        else:
            print('WHAT',fmstate['phase'])
            x=17/0
        return fmstate


    def mapSpeed(self, repeat=2, speedsteps=100, **kwargs):
        """
        Test motor for maximum speed
        
        The motor is set to full speed (max pwm value) and run for interval seconds and the tally count per second and hence rpm is calculated over that interval.
        The test is repeated repeat times.
        
        direction: 'both', 'forward', 'backward'
        
        delay:      time in seconds after starting before we start to measure speed
        
        interval:   time over which speed is measured

        speedsteps: number of speeds to test using evenly spaced values between the minimum and maximum values in the speedtable
        
        repeat:     number of times test is repeated
        """
        fmstate=self.setupfmstate(testname='mapDCtoRPM', tickfunc=self.mapSpeedTick, **kwargs)
        fmstate['repeat'] = repeat
        fmstate['count'] = 0
        fmstate['phase'] = 'waitstop'
        fmstate['steps'] = speedsteps         
        self.targetSpeed(0)
        fmstate['protime'] = time.time()+kwargs['delay']*10,

    def mapSpeedTick(self, fmstate):
        tnow=self.motorpos.lasttallytime
        if fmstate['phase']=='waitstop':
            if self.motorpos.lasttallydiff==0:    # wait for motor to show no movement, then move to windup phase
                fmstate['phase']='windup'
                fmstate['protime']=tnow+fmstate['delay']*4
                speedfb, speedmb, speedmf, speedff=self.speedLimits()
                if fmstate['curdir']=='f':
                    fmstate['speed']=speedmf
                    fmstate['speedchange']=(speedff-speedmf)/fmstate['steps']
                    fmstate['maxspeed']=speedff
                else:
                    fmstate['speed']=-speedmb
                    fmstate['speedchange']=-(speedfb-speedmb)/fmstate['steps']
                    fmstate['maxspeed']=speedmf
                self.targetSpeed(fmstate['speed'])
            else:
                print(self.name, self.motorpos.lasttallydiff)
                if tnow > fmstate['protime']:# if motor hasn't stopped after delay there is a problem
                    fmstate=self.rundone(msg='motor not stopped - abort', runok=False)
        elif fmstate['phase']=='windup':
            if tnow > fmstate['protime']:
                if self.motorpos.lasttallydiff==0:
                    fmstate=self.rundone(msg='map speed scan: no motion detected (DC %d) - abort' % fmstate['DC'], runok=False)
                else:
                    fmstate['tallylist']=[]
                    fmstate['tallystart']=tnow
                    fmstate['protime']=tnow+fmstate['interval']
                    fmstate['phase']='tallyho'
        elif fmstate['phase']=='tallyho':
            fmstate['tallylist'].append(self.motorpos.lasttallydiff)
            if tnow > fmstate['protime']:
                tps=abs(sum(fmstate['tallylist'])/(self.motorpos.lasttallytime-fmstate['tallystart']))
                rpm=tps/self.motorpos.ticksperrev*60
                newres=fmstate['rtemplate'].copy()
                newres['direc']=fmstate['curdir']
                newres['speed'] = fmstate['speed']
                newres['tps']=tps
                newres['rpm']=rpm
                newres['tstamp']=self.motorpos.lasttallytime
                newres['tallylist']=fmstate['tallylist']
                self.log(ltype='analyser', **newres)
                print('===============', fmstate['speed'], fmstate['speedchange'], fmstate['maxspeed'])
                fmstate['speed']+=fmstate['speedchange']
                if abs(fmstate['speed']) > fmstate['maxspeed']:
                    self.targetSpeed(0)
                    fmstate['protime']=tnow+fmstate['delay']*10
                    if fmstate['nextdir'] is None:
                        fmstate['count']+=1
                        if fmstate['count'] >= fmstate['repeat']:
                            fmstate=self.rundone(msg='map speed scan: test run complete', runok=True)
                        else:
                            self.targetSpeed(0)
                            fmstate['mode']='waitstop'
                            fmstate['curdir']='f'
                            fmstate['nextdir']=None
                            if fmstate['requdir']=='backward':
                                fmstate['curdir']='b'
                            elif fmstate['requdir']=='both':
                                fmstate['nextdir']='b'
                    else:
                        fmstate['curdir'] = fmstate['nextdir']
                        fmstate['nextdir']=None
                        fmstate['phase'] = 'waitstop'
                else:
                    print('===============xxx', fmstate['speed'])
                    self.targetSpeed(fmstate['speed'])
                    fmstate['protime']=tnow+fmstate['delay']
                    fmstate['phase']='windon'
        elif fmstate['phase']=='windon':
            if tnow > fmstate['protime']:
                fmstate['tallylist']=[]
                fmstate['tallystart']=tnow
                fmstate['protime']=tnow+fmstate['interval']
                fmstate['phase']='tallyho'
                
        else:
            print('WHAT',fmstate['phase'])
            x=17/0
        return fmstate

    def setupfmstate(self, tickfunc, testname, direction='both', tick=.05, delay=3, interval=2, oncomplete=None, logtype=None):
        """
        useful routine to setup standard parts of the state for tests / measures and the log entries they produce.
        """
        assert direction in ('both', 'forward', 'backward')
        assert delay > .1
        assert interval > .1
        fmstate={
            'rtemplate' : {'motor': self.name, 'testname': testname, 'direc':'f', 'runid':time.time(),
                           'tick': tick, 'tstamp':0},
            'protime' : time.time()+delay,
            'delay'   : delay,
            'interval': interval,
            'requdir' : direction,
            'curdir'  : 'f',
            'nextdir' : None,
            'runid'   : time.time(),
            'oncomplete': oncomplete,
            'logto'   : logtype,
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
        print(msg)        
        return None
