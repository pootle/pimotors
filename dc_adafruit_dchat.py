#!/usr/bin/python3
"""
provides the low level driver for pwm dutycycle using an adafruit dc motor HAT and the adafruit library
"""
from Adafruit_MotorHAT import Adafruit_MotorHAT as adamh

class dc_m_hat():
    """
    A class that provides the low level interface to drive a dc motor through an Adafruit DC motor hat
    """
    RANGE=255
    def __init__(self, motorno, mhat, frequency=400, invert=False):
        """
        prepares an instance to drive a motor connected through an ADAfruit motor hat.
        
        motorno  : the motor number according to the adafruit library 1, 2 ,3 or 4.
        mhat     : the instance of Adafruit_MotorHAT the motor is connected to
        frequency: the frequency we want to use to drive the motor
        invert   : flips the motor's direction 
        
        Note that the frequency is shared across all pwm ports on this hat, so we save the current value
        in the mhat object and only update if it changes. Higher level software beware.
        """
        if 1 <= motorno <= 4:
            self.mhat=mhat
            self.setFrequency(frequency)
            self.motorno=motorno
            self.lastdc=None
            self.invert=invert==True
            self.mot=self.mhat.getMotor(motorno)
            self.mot.run(adamh.RELEASE)
        else:
            raise ValueError('%s is not valid - should be integer in range (10..10000)',str(range))

    def setInvert(self, invert):
        """
        sets the flag that controls which way the motor turns for +ve values of dutycycle.
        
        This happens at the lowest level so most functionality uses this transparently.
        
        invert  : sets the invert flag
        
        returns : True if the invert flag changed 
        """ 
        iv=invert==True
        if iv != self.invert:
            self.invert=iv
            if not self.lastdc is None:
                self.lastdc = -self.lastdc
            return True
        else:
            return False

    def setDC(self, dutycycle):
        """
        The most basic way to drive the motor. Sets the motor's duty cycle to the given value.
        
        This is the ONLY method that sets_PWM_dutycycle so this method also handles the invert flag
        The rpm resulting from different values of duty cycle will follow an approximately asymptotic curve after some 
        wibbly bits at low values.
        
        First checks the new value is different to the last value, and the value is valid.
        """
        if dutycycle == self.lastdc:
            return
        if -dc_m_hat.RANGE<=dutycycle<=dc_m_hat.RANGE and isinstance(dutycycle, int):
            if dutycycle==0:
                self.mot.run(adamh.RELEASE)
            forward = dutycycle > 0
            newval = int(abs(dutycycle))
            self.mot.run(adamh.FORWARD if forward else adamh.BACKWARD)
            self.mot.setSpeed(newval)
            self.lastdc=dutycycle
        else:
            self.stop()
            raise ValueError('%s is not valid - should be in range (-255, +255)' % str(dutycycle))

    def setFrequency(self, frequency):
        """
        changes the frequency to be used for this motor. For low revs, low frequencies work better than higher
        frequencies, albeit this can make the motion a bit jerky. Note that this HAT can only use a single frequency across
        all motors it controls.
        """
        if not hasattr(self.mhat, 'pootlespwmfrequ') or self.mhat.pootlespwmfrequ != frequency:
            self.mhat._pwm.setPWMFreq(frequency)
            self.mhat.pootlespwmfrequ=frequency

    def stop(self):
        """
        stops (removes power) from the motor.
        """
        self.setDC(0)

    def odef(self):
        return {'driver': type(self).__name__, 'motorno': self.motorno, 'invert': self.invert}
