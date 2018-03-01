#!/usr/bin/python3
"""
provides the low level driver for pwm dutycycle and frequency control using an h_bridge hooked up to a Raspberry Pi and pigpio
"""
import pigpio

class dc_h_bridge():
    """
    A class that provides the low level interface to drive a dc motor through an h-bridge with direct control via
    gpio pins using the pigpio library
    """
    def __init__(self, pinf, pinb, piggy, frequency, range=255, invert=False):
        """
        Initialises a single PWM motor using pigpio controlling an H bridge 

        The forward and backward pins are set up for pwm with a 0% (stopped, no power) duty cycle and
        the frequency is initialised
        
        pinf      : the gpio pin for 'forwards'
        pinb      : the gpio pin for 'backwards'
        frequency : the (initial) frequency in Hz used to drive the motor 
                    (see http://abyz.me.uk/rpi/pigpio/python.html#set_PWM_frequency)
        range     : the (integer) range of values used for (approximately) the %age on time
                    -range will drive the motor full speed in reverse, +(range/2) will drive it at
                    50% duty cycle forwards
        invert    : boolean, if True swap forwards and backwards
        piggy     : an instance of pigpio.pi (or None in which case a new instance of pigpio is started)        
        """
        if isinstance(range, int) and 10<=range<=10000:
            self.piggy=piggy
            self.invert=invert==True
            self.pinf=pinf
            self.pinb=pinb
            self.lastHz = None
            self.lastdc=None
            self.setFrequency(frequency)
            self.range=range
            self.piggy.set_PWM_range(self.pinf, range)
            self.piggy.set_PWM_range(self.pinb, range)
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
        
        This is the ONLY method that calls set_PWM_dutycycle so this method also handles the invert flag
        The rpm resulting from different values of duty cycle will follow an approximately asymptotic curve after some 
        wibbly bits at low values.
        
        First checks the new value is different to the last value, and the value is valid.
        """
        if dutycycle == self.lastdc:
            return
        if dutycycle < -self.range:
            dutycycle=-self.range
        elif dutycycle > self.range:
            dutycycle=self.range
        forward = dutycycle > 0
        newval = int(abs(dutycycle))
        pinx, piny = (self.pinb, self.pinf) if forward == self.invert else (self.pinf, self.pinb)
        self.piggy.set_PWM_dutycycle(pinx,0)
        self.piggy.set_PWM_dutycycle(piny,newval)
        self.lastdc=dutycycle
        return dutycycle

    def setFrequency(self, frequency):
        """
        changes the frequency to be used for this motor. For low revs, low frequencies work better than higher
        frequencies, albeit this can make the motion a bit jerky.
        
        frequency to use - See http://abyz.me.uk/rpi/pigpio/python.html#set_PWM_frequency for further details
        
        returns the actual frequency set (see link above...)
        """
        if isinstance(frequency, int):
            if frequency != self.lastHz:
                self.lastHz=frequency
                self.piggy.set_PWM_frequency(self.pinf, self.lastHz)
                self.piggy.set_PWM_frequency(self.pinb, self.lastHz)
            return self.piggy.get_PWM_frequency(self.pinf)
        else:
            raise ValueError('motor driver (%s): setFrequency - frequency must be an int, not %s' % (
                    type(self).__name__, type(frequency).__name__))

    def stop(self):
        """
        stops (removes power) from the motor by setting the dutycycle to 0 on both pins.
        """
        self.setDC(0)

    def odef(self):
        return {'driver': type(self).__name__, 'pinf': self.pinf, 'pinb': self.pinb, 'frequency': self.lastHz, 'invert': self.invert}
