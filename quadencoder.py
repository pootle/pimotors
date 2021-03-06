#!/usr/bin/python3

import pigpio, time

class quadencoder():
    """
    A class to do the low level handling of a quadrature encoder on a motor. It maintains a position and also details of the last measurement interval.

    This version connects the outputs from the quad encoder directly (or via a simple buffer) to gpio pins.
    
    It uses pigpio to count pulses on one or more pins, and has an update routine that reads the counters and updates the absolute
    motor position. The position is held as a float and is the number of revs.
    
    This class cannot sense the motor's direction of rotation, so it asks the motor driver which direction the motor was last moving in
    """
    edgespecs={'both': pigpio.EITHER_EDGE, 'rising': pigpio.RISING_EDGE, 'falling': pigpio.FALLING_EDGE}
    
    def __init__(self, pinss, edges, pulsesperrev, parent, initialpos=0):
        """
        pinss       : a tuple / list / array of pins from feedback sensors.
        edges       : 'both', 'rising', or 'falling' - specifies which edges to count
        pulseperrev : the number of pulses we expect per rev per pin (= number of rising edges - twice this number counted in 'both' edge mode
        parent      : object that provides function needservice to get pigpio shared instance 
        initialpos  : sets the starting position of the motor
        """
        assert edges in self.edgespecs, 'invalid edge spec in quadencoder constructor'
        self.piggy=parent.needservice(sname='piggy', className='pigpio.pi')
#        self.edgemode = pigpio.RISING_EDGE if edges=='rising' else pigpio.FALLING_EDGE if edges=='falling' else pigpio.EITHER_EDGE
        self.edgedef=edges
        self.pprev=pulsesperrev
        self.ticksperrev = pulsesperrev*len(pinss)
        if self.edgedef=='both':
            self.ticksperrev *= 2
        if not pinss is None:
            for sp in pinss:
                assert isinstance(sp, int) and sp>=0
                self.piggy.set_mode(sp, pigpio.INPUT)
            self.scb=[self.piggy.callback(pn, self.edgespecs[self.edgedef]) for pn in pinss]
        else:
            self.scb=[]
        self.lasttallytime=time.time()
        self.mss=pinss
        self.lasttallyread=sum([s.tally() for s in self.scb])
        self.lastmotorpos=initialpos
        self.prevmotorpos=initialpos
        self.lasttallydiff=0
        self.lasttallyinterval=0
        self.isforwardfunc=parent.isforward

    def close(self):
        for i, pn in enumerate(self.mss):
            self.scb[i].cancel()
            self.piggy.set_pull_up_down(pn, pigpio.PUD_OFF)
        self.scb=None

    def stopped(self):
        """
        return True if we think the motor is stationary
        """
        return self.lasttallydiff==0

    def __iter__(self):
        """
        The iterator updates the motor position by reading the tally count and adjusting the motor position appropriately.
        
        It returns the latest known motor position.
        
        The tally counter always increases as it has no awareness of the motor's direction, so we use the motors last
        direction to check whether to add or subtract.
        
        The motorpos is recorded in revolutions.

        Using an iterator is more efficient than calling a tick function
        """
        while True:
            tallyr=sum([s.tally() for s in self.scb])
            tnow=time.time()
            self.lasttallyinterval=tnow-self.lasttallytime
            self.lasttallytime=tnow
            tallydiff=tallyr-self.lasttallyread
            self.prevmotorpos=self.lastmotorpos
            if not self.isforwardfunc():
                tallydiff = -tallydiff
            self.lastmotorpos+=tallydiff / self.ticksperrev
            self.lasttallyread=tallyr
            self.lasttallydiff=tallydiff
            yield(self.lastmotorpos)

    def odef(self):
        return {'className': type(self).__name__, 'edges': self.edgedef, 'pinss': str(self.mss), 'pulsesperrev': self.pprev}
        