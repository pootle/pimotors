#!/usr/bin/python3
"""
provides the low level driver for pwm dutycycle using an adafruit dc motor HAT and the adafruit library
"""
from Adafruit_MotorHAT import Adafruit_MotorHAT as adamh
import atexit

class dcmotorHatExtra(adamh):
    """
    small extension to the adafruit class to remember the frequency we last set.
    """
    def __init__(self, freq, *args, **kwargs):
        super().__init__(*args, freq=freq, **kwargs)
        self.pootlespwmfrequ=freq
        atexit.register(self._cleanexit)

    def setPWMFreq(self, freq):
        if self.pootlespwmfrequ==freq:
            return
        else:
            self._pwm.setPWMFreq(freq)
            self.pootlespwmfrequ=frequency

    def _cleanexit(self):
        for mno in range(1,4):
            self.getMotor(mno).run(adamh.RELEASE)

class dc_m_hat():
    """
    A class that provides the low level interface to drive a dc motor through an Adafruit DC motor hat
    """
    RANGE=255
    def __init__(self, motorno, parent, frequency=400, invert=False):
        """
        prepares an instance to drive a motor connected through an ADAfruit motor hat.
        
        motorno   : the motor number according to the adafruit library 1, 2 ,3 or 4.
        parent    : object that provides function needservice to get adafruit hat instance
        frequency : the frequency we want to use to drive the motor
        invert    : flips the motor's direction 
        
        Note that the frequency is shared across all pwm ports on this hat, so we save the current value
        in the mhat object and only update if it changes. Higher level software beware.
        """
        if 1 <= motorno <= 4:
            self.mhat=parent.needservice(sname='adafruitdcsm_hatdefault', className='dc_adafruit_dchat.dcmotorHatExtra', freq=40)
            self.frequency(frequency)
            self.motorno=motorno
            self.lastdc=None
            self.isinverted=invert==True
            self.mot=self.mhat.getMotor(motorno)
            self.mot.run(adamh.RELEASE)
        else:
            raise ValueError('%s is not valid - should be integer in range (1..4)',str(motorno))

    def invert(self, invert):
        """
        returns and optionally sets the flag that controls which way the motor turns for +ve values of dutycycle.
        
        This happens at the lowest level so most functionality uses this transparently.
        
        invert  : if None the flag is unchanged else sets the invert flag
        
        returns : current value of the flag
        """
        if not invert is None and (invert==True) != self.isinverted:
            self.isinverted=invert==True
            if not self.lastdc is None:
                self.lastdc = -self.lastdc
        return self.isinverted

    @classmethod
    def maxDC(cls):
        """
        returns the max valid value for duty cycle
        """
        return cls.RANGE

    def DC(self, dutycycle):
        """
        The most basic way to drive the motor. returns and optioanlly sets the motor's duty cycle to the given value.
        
        This is the ONLY method that sets_PWM_dutycycle so this method also handles the inverted flag
        The rpm resulting from different values of duty cycle will follow an approximately asymptotic curve after some 
        wibbly bits at low values.
        
        First checks the new value is not None and is different to the last value, and clamps the value to the valid range.
        
        returns the value actually set
        """
        if dutycycle is None or dutycycle == self.lastdc:
            return self.lastdc
        if not -dc_m_hat.RANGE<=dutycycle<=dc_m_hat.RANGE:
            if dutycycle < -dc_m_hat.RANGE:
                dutycycle=-dc_m_hat.RANGE
            elif dutycycle > dc_m_hat.RANGE:
                dutycycle=dc_m_hat.RANGE
        if dutycycle==0:
            self.mot.run(adamh.RELEASE)
        forward = dutycycle > 0
        if self.isinverted:
            forward=not forward
        newval = int(abs(dutycycle))
        self.mot.run(adamh.FORWARD if forward else adamh.BACKWARD)
        self.mot.setSpeed(newval)
        self.lastdc=dutycycle
        return self.lastdc

    def frequency(self, frequency):
        """
        changes the frequency to be used for this motor. For low revs, low frequencies work better than higher
        frequencies, albeit this can make the motion a bit jerky. Note that this HAT can only use a single frequency across
        all motors it controls.
        
        frequency:  None - returns the current setting, or the frequency in Hz.
        """
        if not frequency is None and self.mhat.pootlespwmfrequ != frequency:
            self.mhat._pwm.setPWMFreq(frequency)
            self.mhat.pootlespwmfrequ=frequency
        return self.mhat.pootlespwmfrequ

    def stop(self):
        """
        stops (removes power) from the motor.
        """
        self.DC(0)

    def close(self):
        """
        takes appropriate action to turn-off / shut down the motor
        """
        self.DC(0)

    def odef(self):
        return {'className': type(self).__name__, 'motorno': self.motorno, 'invert': self.isinverted,
                'range':RANGE, 'frequency':self.frequency}
