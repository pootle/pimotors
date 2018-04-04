#!/usr/bin/python3
"""
A module to provide simple in-line control of multiple motors (typically dc motors via an h-bridge or a stepper) using pigpio.

Originally implemented to control motors through a pimoroni explorer phat (https://shop.pimoroni.com/products/explorer-phat).

This method using pigpio has a constant cpu load of ~10% on a raspberry pi Zero, as compared to the pimoroni module which has
a constant cpu load of ~20%.
"""
import logger
import time

class motor(logger.logger):
    """
    A class to provide control and logging of a motor. It uses a driver class to provide physical control of the motor.
    
    The driver class takes care of both the interface to motor hardware and some physical characteristics of the motor.
    
    This class also accepts an optional motor sensor (e.g. a quadrature encoder) which will maintain the motor's position.
    
    If a feedback sensor is used, the ticker method must be called at (reasonably) regular intervals 
    (typically 10 - 50 times per second) so the sensor can maintain info about the motors position etc.
    
    This class provides motor control at a number of levels, starting from direct low level physical control, to controls 
    which set targets and use feedback to match the target as closely as possible. (this last is WIP)
    
    Each level builds on the preceeding level, and lower level calls should not be used.
    
    Base level:
        Should always be available.

        DC          : sets / returns the dutycycle (typically in 255ths). Values outside the range +/-maxDC are clamped.
        frequency   : sets / returns the frequency used (how many on pulses per second
        maxDC       : returns the maximum value for DC. Values between -maxDC and +maxDC are valid.
    
    Intermediate level:
        Only available if a speedmapper is set up - see speedLimits below.

        speed       : This attempts to provide a linear response. The units are arbitrary. Requires a speedmapper to
                        be setup. 
        speedLimits : returns None if speed interface is not available. Otherwise returns the valid ranges for speed
                        (values close to zero can be blocked if the motor does not handle them well.

    Best level:
        Only available if speed mapper, feedback sensor, and feedback handler are set up.

        targetSpeed : Attempts to accurately maintain the motor's speed and revolutions.
    """
    physlogso=('phys', {'filename': 'stdout', 'format': '{setting} is {newval}.'})

    def __init__(self, mdrive, rotationsense=None, speedmapinfo=None, feedback=None, **kwargs):
        """
        Initialises a single motor, low level interfacing is handled by the driver specified in mdrive

        mdrive          : dict with class / class name and parameters for the constructor

        rotationsense   : optional params for class instance to handle the motor feedback sensor
        
        speedmapinfo    : optional params for making speedmappers - see speedmapper class below (or whatever other class you use)

        feedback        : optional params for feedback control - optional and (for this class) only allowed if rotationsense also specified

        **kwargs    : allows other arbitrary keyword parameters to be ignored / passed to the super class.
        
        self.motorforward is the last direction the motor was driven. It helps the feedback keep track of the motors position.
        Even if the motor speed is now zero this wil show which way the motor might still be moving.
       
        """
        super().__init__(createlogmsg=False, **kwargs)
        self.tickacts=[] # a list of all the things that need to happen each tick - see addTicker below
        self.mdrive=logger.makeClassInstance(parent=self, **mdrive)
        if rotationsense is None:
            self.motorpos=None
            self.postick=None
        else:
            self.motorpos=logger.makeClassInstance(parent=self, isforward=self.isforward, **rotationsense)
            self.postick=iter(self.motorpos)
        self.motorforward=True
        self.speedmap=None if speedmapinfo is None else logger.makeClassInstance(invert=self.mdrive.invert(None), **speedmapinfo)
        self.currSpeed=0
        self.feedbackcontrol=None if feedback is None or self.postick is None else logger.makeClassInstance(timenow=time.time(), **feedback)
        self.targSpeed=None
        self.longactfunc=None
        self.logCreate()
        self.stop()

    def needservice(self, **kwargs):
        return self.parent.needservice(**kwargs)

    def logCreate(self):
        if self.motorpos is None:
            posmsg='no position sensing'
        else:
            posmsg='position sensing with a' + type(self.motorpos).__name__
        if self.speedmap is None:
            speedmsg='no speed mapping'
        else:
            speedmsg='speed mapping using a' + type(self.speedmap).__name__
        self.log(ltype='life', otype=type(self).__name__, lifemsg='created motor with %s and %s.' % (posmsg, speedmsg))

    def logClose(self):
        self.log(ltype='life', otype=type(self).__name__, lifemsg='motor closed')

    def close(self):
        """tidy shutdown"""
        if not self.motorpos is None:
            self.motorpos.close()
        self.mdrive.close()
        super().close()

    def isforward(self):
        """
        returns True if the last direction was forward (specifically even if now zero, shows direction before stopping)
        """
        return self.motorforward

    def lastPosition(self):
        """
        If the motor has a sensor, returns our most recent view of the position, otherwise returns None (i.e not known)
        """
        return None if self.motorpos is None else self.motorpos.lastmotorpos

    def lastRPM(self):
        """
        returns the most recent known actual rpm of the motor if the motor has an appropriate sensor (else None)
        """
        if self.motorpos is None or self.motorpos.lasttallyinterval == 0:
            return None
        return 60*(self.motorpos.lastmotorpos-self.motorpos.prevmotorpos)/self.motorpos.lasttallyinterval

    def invert(self, invert):
        """
        returns and optionally sets the flag that controls which way the motor turns for +ve values of dutycycle.
        
        invert: if None, returns the invert setting, otherwise sets invert to the given value and returns the new value.
        
        This is merely passed through to the low level driver.
        """ 
        oldiv = self.mdrive.invert(None)
        newiv=self.mdrive.invert(invert)
        if newiv != oldiv:
            self.log(ltype='phys', setting='invert', newval=newiv)
            if not self.speedmap is None:
                self.speedmap.setInvert(newiv)
        return newiv

    def stop(self):
        """
        stops (removes power) from the motor by setting the speed / dutycycle to 0 
        """
        if self.speedmap is None:
            self.DC(0)
        else:
            self.speed(0) # this will eventually set DC to zero as well

    def maxDC(self):
        return self.mdrive.maxDC()

    def DC(self, dutycycle):
        """
        The most basic way to drive the motor. Sets the motor's duty cycle to the given value.
        
        The rpm resulting from different values of duty cycle will follow an approximately asymptotic curve after some 
        wibbly bits at low values.
        """
        appliedval=self.mdrive.DC(dutycycle)
        if appliedval != 0:
            self.motorforward=appliedval > 0
        self.log(ltype='phys', setting='dutycycle', newval=abs(appliedval))
        return appliedval

    def frequency(self, frequency):
        """
        returns the frequency to be used for this motor. First changes the frequency if the value is not None.
        
        For low revs, low frequencies work better than higher frequencies, albeit this can make the motion a bit jerky.
        
        frequency: None or the frequency in Hz. (no change is made if None)
        
        returns the current frequency
        """
        nf = self.mdrive.frequency(frequency)
        if not frequency is None:
            self.log(ltype='phys', setting='frequency', newval=nf)
        return nf

    def speedLimits(self):
        """
        See speedmapper.speedLimits below. 
        """
        if self.speedmap is None:
            return None
        return self.speedmap.speedLimits()      

    def speed(self, speed):
        """
        returns and optionally sets the current speed.
        
        This provides an approximately linear way to drive the motor, i.e. the motor rpm should be a simple ratio of the speed
        parameter to this call.
        
        The value of speed - if not None - should be in the range of values supported by the speedtable - but value is clamped.....
        
        This uses the lookup table in self.speedtabf and self.speedtabb. See speedmapper class for an explanation.
        
        Note that the units here are arbitrary, but for feedback control it should be shaft rpm.
        
        speed   : the requested speed
        
        returns : None if speed mapping not supported here else the actual value set (it is clamped by the speedmapper)
        """
        if self.speedmap is None:
            return None
        if not speed is None:
            fr, dc, appliedspeed =self.speedmap.speedToFDC(speed)
            self.currSpeed=-appliedspeed if speed < 0 else appliedspeed
            self.log(ltype='phys', setting='speed', newval=self.currSpeed)
            self.frequency(fr)
            self.DC(-dc if speed < 0 else dc)
        return self.currSpeed

    def targetSpeed(self, speed):
        """
        sets a target speed for the motor. This attempts to accurately maintain the motor's speed and count of revolutions.
        """
        if self.feedbackcontrol is None:    # can we do this?
            return None
        elif speed is None or speed==self.targSpeed: # if no new speed or speed unchanged, just return current speed
            return self.targSpeed

        if self.targSpeed is None:
            self.feedbackcontrol.reset(self.motorpos.lasttallytime,0)
            facts=self.feedbackcontrol.factors()
            self.fbtrace={'motor': self.name, 'ltype': 'feedbacktrace', 'runid':time.time(), 'Pf':facts[0], 'If':facts[1], 'Df':facts[2],
                     'tstamp':0, 'targetSpeed':0, 'speed':0, 'tallyinterval':0, 'motorpos':0, 'error':0, 'adjust':0,
                     'expectchange':0, 'actualchange':0}

            self.targSpeed=0
        clampedspeed=self.speedmap.speedClamp(speed)
        if self.targSpeed==0:             # just set speed to (hopefully!) something near the right value.
            self.speed(clampedspeed)
            self.targSpeed=clampedspeed
        else:                             # already running - apply change in target speed to actual speed
            speedchange=clampedspeed-self.targSpeed
            self.speed(self.currSpeed+speedchange)
            self.targSpeed=clampedspeed
        return self.targSpeed

    def addTicker(self, tickgen, tickID, ticktick, priority):
        """
        Various functions need to be run on a regular basis.
        
        ticker functions are written as generators, this allows them to be written as if they run continuously, making 
        the code easier to understand and the invocation much more efficient. Also the generator can gracefully exit
        when complete.
        
        The list (which is ordered) is processed in sequence each tick.
        
        tickgen  : a generator that will be called each tick (of this ticker) 
        
        tickID   : some ID for the ticker to uniquely identify it
        
        ticktick : number of top level ticks (i.e. calls of ticker below) between calls of this ticker. prime numbers are good!)
        
        priority : the lower the number the higher up the list
        
        Each entry in the list is a little dict for ease of understanding:
            'g'  : the generator we got by calling tickfunc
            'tid': the tickID
            'ttc : the tick count per tick of this ticker
            'tc' : current countdown
            'pr' : priority of this ticker
        """
        ta={'g'  : tickgen,
            'tid': tickID,
            'ttc': ticktick,
            'tc' : ticktick,
            'pr' : priority}
        for ti, t in enumerate(self.tickacts):
            if t['pr'] > priority:
                self.tickacts.insert[ti+1]
                break
        else:
            #we reached the end
            self.tickacts.append(ta)

    def ticker(self):
        """
        called as a regular tick (typically 5 - 50 per second) from some higher place, this updates sensor info (if available) and
        invokes any long term (e.g. multiple tick) operations.
        """
        if not self.postick is None:
            posnow=next(self.postick)
            if not self.targSpeed is None:
                mp=self.motorpos
                expectedposchange=mp.lasttallyinterval*self.targSpeed/60
                actualposchange  =mp.lastmotorpos-mp.prevmotorpos
                lasterror=actualposchange-expectedposchange
                adjust=self.feedbackcontrol.ticker(mp.lasttallytime, lasterror)
                if True:
                    self.fbtrace['tstamp']         = self.motorpos.lasttallytime
                    self.fbtrace['targetSpeed']    = self.targSpeed
                    self.fbtrace['speed']          = self.currSpeed
                    self.fbtrace['tallyinterval']  = self.motorpos.lasttallyinterval
                    self.fbtrace['motorpos']       = self.motorpos.lastmotorpos
                    self.fbtrace['error']          = lasterror/mp.lasttallyinterval*60
                    self.fbtrace['adjust']         = adjust
                    self.fbtrace['expectchange']   = expectedposchange
                    self.fbtrace['actualchange']   = actualposchange
                    self.log(**self.fbtrace)
                self.speed(self.currSpeed+adjust)

        if not self.longactfunc is None: #this is legacy  and things using it should convert to tickers
            newstate=self.longactfunc(self.longactstate)
            if newstate==None:
                self.longactfunc=None
            self.longactstate=newstate
        
        for ti, t in enumerate(self.tickacts):
            t['tc'] -=1
            if t['tc']<=0:
                try:
                    next(t['g'])
                except StopIteration:
                    self.tickacts.pop(ti)
                t['tc']=t['ttc']

    def odef(self):
        """
        This should return the info needed to recreate an identical motor
        """
        x=super().odef()
        x.update({'mdrive': self.mdrive.odef(), }) #'speedtable': {'f': self.speedtabf, 'b':self.speedtabb}})
        if not self.motorpos is None:
            x['rotationsense']=self.motorpos.odef()
        if not self.speedmap is None:
            x['speedmapinfo']=self.speedmap.odef()
        if not self.feedbackcontrol is None:
            x['feedback']=self.feedbackcontrol.odef()
        return x

class speedmapper():
    """
    A mapper to provide an approximately linear interface for motor speed, using whatever real world measure is appropriate.

    Because DC motors have a complex relationship between the duty cycle and frequency of pulses and the resultant speed (rpm),
    this class provides a simple lookup based mechanism to to map a requested speed to a suggested duty cycle and frequency.
    
    It provides a simple interface to build what is hopefully a reasonable mapping table, but a full table can also be passed.
    """
    def __init__(self, invert, ftable=None, rtable=None, fbuilder=None, rbuilder=None):
        """
        This prepares a speed mapper.
        
        Either provide forward and reverse speed tables, or min and max speeds and duty cycles.
        
        invert: The lookup always works on the true direction of the motor, so the table is associated with the 'real' motor direction.
                we assume the motor wiring is unchanged, we want to to logically go the other way
        
        ftable: lookup table for forward speeds. if None then min/max speed/DC are used to build a default table
        
        rtable: lookup table for reverse speeds. if None then min/max speed/DC are used to build a default table
        
        fbuilder, rbuilder: dicts that define parameters to build a default lookup table as follows:
            
            min_speed: a float defining the lowest speed we'll try to use, any speed below this value will be mapped to
                        zero.
            max_speed: a float defining the maximum speed we can use, this speed and any higher speed will map to 100% on
                        duty cycle
            
            min_DC   : The duty cycle to use for the minimum speed
            
            max_DC   : the maximum applicable duty cycle (this allows duty cycle to use arbitrary units to match whatever
                        lower level software expects
        """
        assert not ftable is None or not fbuilder is None
        assert not rtable is None or not rbuilder is None
        self.invert=invert
        self.rbuild=rbuilder
        self.fbuild=fbuilder
        self.speedtabf, self.minSpeedf, self.maxSpeedf = self.maketable(**fbuilder) if ftable is None else (ftable, ftable[0][0], ftable[-1][0])
        self.speedtabb, self.minSpeedb, self.maxSpeedb = self.maketable(**rbuilder) if rtable is None else (rtable, rtable[0][0], rtable[-1][0])

    def speedLimits(self):
        """
        returns a 4-tuple of max reverse speed (-ve), min reverse speed (-ve), min forward speed and max forward speed

        The units are arbitrary, and depend on how the speedtable is defined.        
        """
        return -self.maxSpeedb, -self.minSpeedb, self.minSpeedf, self.maxSpeedf

    def speedClamp(self, speed):
        """
        Clamps the speed to be <= max speed (in each direction) and also returns zero if < min speed in either direction.
        
        speed : some speed or other
        
        returns: a valid speed - zero or between min and max in each direction
        """
        fwd=speed >=0
        if self.invert:
            fwd = not fwd
        aspeed = abs(speed)
        if fwd:
            if aspeed < self.minSpeedf:
                cspeed = 0
            elif aspeed > self.maxSpeedf:
                cspeed = self.maxSpeedf
            else:
                cspeed = aspeed
        else:
            if aspeed < self.minSpeedb:
                cspeed = 0
            elif aspeed > self.maxSpeedb:
                cspeed = self.maxSpeedb
            else:
                cspeed = aspeed
        return cspeed if speed >=0 else -cspeed

    def speedToFDC(self, speed):
        """
        Uses the speedtable loaded earlier to find a frequency and duty cycle that should be close to the requested speed.
        Note this returns the absolute speed (i.e. always positive)
        
        This is expected to use values in the range defined in the speedtab, very low values (below those at which we get stable running) 
        usually map to zero, the maximum value is clamped to the last entry in the speedtab.
        
        speed: the desired speed
        
        returns: 3 tuple: frequency, dutycycle and actual speed used (speed used is absolute value - i.e. always positive
                note values below the minimum defined in the speedtable are changed to zero, and values above the maximum are changed to 
                the maximum.
        """
        fwd=speed >=0
        if self.invert:
            fwd = not fwd
        aspeed = abs(speed)
        if fwd:
            usestab=self.speedtabf
            if aspeed < self.minSpeedf:
                useent=0
                applied=0
            elif aspeed > self.maxSpeedf:
                useent=-1
                applied=self.maxSpeedf
            else:
                useent=None
                applied=aspeed
        else:
            usestab=self.speedtabb
            if aspeed < self.minSpeedb:
                useent=0
                applied=0
            elif aspeed > self.maxSpeedb:
                useent=-1
                applied=self.maxSpeedb
            else:
                useent=None
                applied=aspeed
        if useent is None:
            i=0
            while i < len(usestab) and usestab[i][0] < aspeed:
                i+=1
            if i>=len(usestab):
                enta=None
                entb=usestab[-1]
            elif i==0 or usestab[i][0]==aspeed:
                enta=None
                entb=usestab[i]
            else:
                enta=usestab[i-1]
                entb=usestab[i]
            if enta is None:
                return entb[1], entb[2], applied
            else:
                deltas=(aspeed-enta[0]) / (entb[0]-enta[0])
                return enta[1], int(round(enta[2]+(entb[2]-enta[2]) * deltas)), applied
        else:
            enta=usestab[useent]
            return enta[1], enta[2], applied

    def setInvert(self, invert):
        """
        This should always be the same as the value in the motor driver which is the 'real' data
        """
        self.invert=invert

    def maketable(self, minSpeed, maxSpeed, minDC, maxDC, oneFrequ=None, asint=True):
        """
        creates a hopefully useful speed map table from the given params and the simple table defined below
        
        the speeds and duty cycle values are offset and scaled to range between the minimum and maximum values given
        minSpeed: the minimum valid speed. Any speed below this will be treated as zero.
        maxSpeed: the maximum valid speed, Any speed above this will be treated as maxSpeed and will yield maxDC
        minDC   : the dutycycle value to use for the lowest valid speed
        maxDC   : the duty cycle value to use for the fastest valid speed
        oneFrequ: if None the frequency from the simple table is used, otherwise all enries are forced to use this value
        asint   : if True all duty cycle values are rounded to the nearest int 
            
        """
        assert maxSpeed > minSpeed
        assert maxDC > minDC
        speedrange=maxSpeed-minSpeed
        dcrange=maxDC-minDC
        nst=[(minSpeed+speedrange*entry[0], entry[1] if oneFrequ is None else oneFrequ, minDC+dcrange*entry[2]) for entry in simplespeedtable]
        nst.insert(0,(0,nst[1][1],0))
        return nst, nst[1][0], nst[-1][0]

    def odef(self):
        x = {'className': type(self).__name__, 'minfwdspeed': self.minSpeedf, 'maxfwdspeed': self.maxSpeedf, 
                'minbackspeed': self.minSpeedb, 'maxbackspeed': self.maxSpeedb}
        if not self.fbuild is None:
            x['fbuilder']=self.fbuild
        if not self.rbuild is None:
            x['rbuilder']=self.rbuild
        return x
        
simplespeedtable=[
(0.0012062726176115801, 20, 0.0), 
(0.0048250904704463205, 20, 0.00423728813559322), 
(0.0048250904704463205, 20, 0.00847457627118644), 
(0.012062726176115802, 20, 0.012711864406779662), 
(0.025331724969843185, 20, 0.01694915254237288), 
(0.06996381182147166, 20, 0.0211864406779661), 
(0.11821471652593486, 20, 0.025423728813559324), 
(0.14354644149577805, 20, 0.029661016949152543), 
(0.18335343787696018, 40, 0.038135593220338986), 
(0.22677925211097708, 40, 0.046610169491525424), 
(0.31242460796139926, 40, 0.06779661016949153), 
(0.3884197828709288, 40, 0.08898305084745763), 
(0.5018094089264173, 40, 0.13135593220338984), 
(0.5850422195416164, 80, 0.19491525423728814), 
(0.6755126658624849, 80, 0.2584745762711864), 
(0.7696019300361882, 80, 0.3432203389830508), 
(0.8359469240048251, 80, 0.4491525423728814), 
(0.8866103739445115, 80, 0.5550847457627118), 
(0.9276236429433052, 80, 0.6610169491525424), 
(0.9541616405307599, 80, 0.7669491525423728), 
(0.9758745476477684, 80, 0.8728813559322034), 
(1.0, 80, 1.0)]

