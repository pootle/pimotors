#!/usr/bin/python3
"""
A module to provide simple in-line control of multiple pwm devices (typically dc motors via an h-bridge) using pigpio.

Originally implemented to control motors through a pimoroni explorer phat (https://shop.pimoroni.com/products/explorer-phat).

This method using pigpio has a constant cpu load of ~10% on a raspberry pi Zero, as compared to the pimoroni module which has
a constant cpu load of ~20%.
"""
import statistics as st
import logger

class motor(logger.logger):
    """
    A class to provide control and logging of a motor. It uses a driver class to provide physical control of the motor.
    
    The driver class takes care of both the interface to motor hardware and some physical characteristics of the motor.
    
    It also accepts an optional motor sensor (e.g. a quadrature encoder) which will maintain the motor's position.
    
    If a feedback sensor is used, the ticker method must be called at (reasonably) regular intervals (typically 10 - 50 times per second)
    so the sensor can maintain info about the motors position etc.

    """
    physlogso=('phys', {'filename': 'stdout', 'format': '{setting} is {newval}.'})

    def __init__(self, mdrive, sensor=None, speedtable=None, **kwargs):
        """
        Initialises a single PWM motor, interfacing is handled by the mdrive class instance

        mdrive    : class instance that handles the low level interface to the motor.

        sensor      : a optional class instance to handle the motor feedback sensor and maintain the position
        
        speedtable: a table that maps requested speed to pwm values and frequencies to enable an approximately linear response
                    from as low a speed as practical. a dict with 2 entries, 'f' for forwards table, 'b' for reverse table

        **kwargs  : allows other arbitrary keyword parameters to be ignored / passed to the super class.
        
        self.motorforward is the last direction the motor was driven. It helps the fbmotorclass keep track of the motors position.
        Even if the motor speed is now zero this 
        """
        super().__init__(**kwargs)
        self.mdrive=mdrive
        self.motorpos=sensor
        if not self.motorpos is None:
            self.motorpos.setforwardfunc(self.isforward)
        self.motorforward=True
        self.stop()
        self.speedtabf=None if speedtable is None else speedtable['f']
        if self.speedtabf is None:
            self.maxspeed = None
        else:
            self.maxspeed = self.speedtabf[-1][0]
        self.speedtabb=None if speedtable is None else speedtable['b']
        self.minspeed = None if self.speedtabb is None else -self.speedtabb[-1][0]
        self.targetrpm=0

    def close(self):
        if not self.motorpos is None:
            self.motorpos.close()
        super().close()

    def isforward(self):
        return self.motorforward

    def lastPosition(self):
        return None if self.motorpos is None else self.motorpos.lastmotorpos

    def lastRPM(self):
        """
        returns the actual rpm of the motor if the motor has an appropriate sensor (else None)
        """
        if self.motorpos is None or self.motorpos.lasttallyinterval == 0:
            return None
        return 60*(self.motorpos.lastmotorpos-self.motorpos.prevmotorpos)/self.motorpos.lasttallyinterval

    def invert(self, invert):
        """
        returns and optionally sets the flag that controls which way the motor turns for +ve values of dutycycle.
        
        This happens at the lowest level so most functionality uses this transparently.
        """ 
        oldiv = self.mdrive.invert(None)
        newiv=self.mdrive.invert(invert)
        if newiv != oldiv:
            self.log(ltype='phys', setting='invert', newval=newiv)
            x=self.speedtabf
            self.speedtabf = self.speedtabb
            self.speedtabb = x
        return newiv

    def stop(self):
        """
        stops (removes power) from the motor by setting the dutycycle to 0 
        """
        self.DC(0)

    def DC(self, dutycycle):
        """
        The most basic way to drive the motor. Sets the motor's duty cycle to the given value.
        
        This is the ONLY method that calls set_PWM_dutycycle so this method also handles the invert flag
        The rpm resulting from different values of duty cycle will follow an approximately asymptotic curve after some 
        wibbly bits at low values.
        
        First checks the new value is different to the last value, and the value is valid.
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
        return self.mdrive.frequency(frequency)
        
    def targetRPM(self, rpm):
        """
        returns and optionally sets the current target rpm
        
        This provides an approximately linear way to drive the motor, i.e. the motor rpm should be a simple ratio of the speed
        parameter to this call.
        
        The value of speed - if not None - should be in the range of values supported by the speedtable.
        
        This uses the lookup table in self.speedtabf and self.speedtabb. See speedtable255 for an explanation.
        """
        if not rpm is None:
            fr, dc=self.rpmtoFDC(speed)
            self.log(ltype='phys', setting='speed', newval=speed)
            self.targetrpm=rpm
            self.frequency(fr)
            self.DC(-dc if rpm < 0 else dc)
        return self.targetrpm

    def _rpmtoFDC(self, speed):
        """
        Uses the speedtable loaded earlier to find a frequency and duty cycle that should be close to the requested speed.
        Note this returns the absolute speed (i.e. always positive)
        
        This is expected to use values in the range defined in the speedtab, very low values (below those at which we get stable running) 
        usually map to zero, the maximum value is clamped to the last entry in the speedtab.
        """
        aspeed = abs(speed)
        usestab=self.speedtabf if speed>0 and not self.invert else self.speedtabb
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
            return entb[1:3]
        else:
            deltas=(aspeed-enta[0]) / (entb[0]-enta[0])
            return enta[1], int(round(enta[2]+(entb[2]-enta[2]) * deltas))

    def ticker(self, waittime):
        if not self.motorpos is None:
            self.motorpos.tick()

    def odef(self):
        x=super().odef()
        x.update({'mdrive': self.mdrive.odef(), 'speedtable': {'f': self.speedtabf, 'b':self.speedtabb}})
        return x
