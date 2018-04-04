#!/usr/bin/python3
"""
provides the low level driver for pwm dutycycle and frequency control using an h_bridge hooked up to a Raspberry Pi and pigpio
"""

class dc_h_bridge():
    """
    A class that provides the low level interface to drive a dc motor through an h-bridge with direct control via
    gpio pins using the pigpio library
    """
    def __init__(self, pinf, pinb, parent, frequency=200, range=255, invert=False):
        """
        Initialises a single PWM motor using pigpio controlling an H bridge 

        The forward and backward pins are set up for pwm with a 0% (stopped, no power) duty cycle and
        the frequency is initialised
        
        pinf      : the gpio pin for 'forwards'
        pinb      : the gpio pin for 'backwards'
        parent    : object that provides function needservice to get pigpio shared instance
        frequency : the (initial) frequency in Hz used to drive the motor 
                    (see http://abyz.me.uk/rpi/pigpio/python.html#set_PWM_frequency)
        range     : the (integer) range of values used for (approximately) the %age on time
                    -range will drive the motor full speed in reverse, +(range/2) will drive it at
                    50% duty cycle forwards
        invert    : boolean, if True swap forwards and backwards
        """
        assert isinstance(range, int) and 10<=range<=10000, '%s is not valid - should be integer in range (10..10000)' % str(range)
        self.piggy=parent.needservice(sname='piggy', className='pigpio.pi')
        self.isinverted=invert==True
        self.pinf=pinf
        self.pinb=pinb
        self.lastHz = None
        self.lastdc=None
        self.frequency(frequency)
        self.range=range
        self.piggy.set_PWM_range(self.pinf, range)
        self.piggy.set_PWM_range(self.pinb, range)

    def invert(self, invert):
        """
        returns and optionally sets the flag that controls which way the motor turns for +ve values of dutycycle.
        
        This happens at the lowest level so most functionality uses this transparently.
        
        invert  : None invert flag unchanged, True / False sets the invert flag
        
        returns : True if the invert flag is set
        """ 
        if not invert is None and (invert==True) != self.isinverted:
            self.isinverted=invert==True
            if not self.lastdc is None:
                self.lastdc = -self.lastdc
        return self.isinverted

    def maxDC(self):
        """
        returns the max valid value for duty cycle
        """
        return self.range

    def DC(self, dutycycle):
        """
        The most basic way to drive the motor. returns and optionally sets the motor's duty cycle to the given value.
        
        This is the ONLY method that calls set_PWM_dutycycle so this method also handles the inverted flag
        The rpm resulting from different values of duty cycle will follow an approximately asymptotic curve after some 
        wibbly bits at low values.
        
        First checks the new value is different to the last value, and the value is valid.
        """
        if self.piggy is None:
            raise ValueError('the motor has been closed')
        if dutycycle is None or dutycycle == self.lastdc:
            return self.lastdc
        if dutycycle < -self.range:
            dutycycle=-self.range
        elif dutycycle > self.range:
            dutycycle=self.range
        forward = dutycycle > 0
        newval = int(abs(dutycycle))
        pinx, piny = (self.pinb, self.pinf) if forward == self.isinverted else (self.pinf, self.pinb)
        self.piggy.set_PWM_dutycycle(pinx,0)
        self.piggy.set_PWM_dutycycle(piny,newval)
        self.lastdc=dutycycle
        return dutycycle

    def frequency(self, frequency):
        """
        changes the frequency to be used for this motor. For low revs, low frequencies work better than higher
        frequencies, albeit this can make the motion a bit jerky.
        
        frequency: None or the frequency in Hz (See http://abyz.me.uk/rpi/pigpio/python.html#set_PWM_frequency for further details)
                    if None the current frequency is returned with no change to the frequency
        
        returns the actual frequency set (see link above...)
        """
        if frequency is None:
            return self.lastHz
        if isinstance(frequency, int):
            if frequency != self.lastHz:
                self.piggy.set_PWM_frequency(self.pinf, frequency)
                self.piggy.set_PWM_frequency(self.pinb, frequency)
                self.lastHz=self.piggy.get_PWM_frequency(self.pinf)
            return self.lastHz
        else:
            raise ValueError('motor driver (%s): setFrequency - frequency must be an int, not %s' % (
                    type(self).__name__, type(frequency).__name__))

    def stop(self):
        """
        stops (removes power) from the motor by setting the dutycycle to 0 on both pins.
        """
        self.DC(0)

    def close(self):
        """
        takes appropriate action to turn-off / shut down the motor
        """
        self.DC(0)

    def odef(self):
        """
        returns a dict with all setttings needed to re-create an instance
        
        #TODO - incomplete
        """
        return {'className': type(self).__name__, 'pinf': self.pinf, 'pinb': self.pinb, 'invert': self.isinverted,
                'frequency': self.lastHz, 'range': self.range}
