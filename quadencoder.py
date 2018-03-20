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
    def __init__(self, pinss, edges, pulsesperrev, parent, isforward=None, initialpos=0):
        """
        pinss       : a tuple / list / array of pins from feedback sensors.
        edges       : 'both', 'rising', or 'falling' - specifies which edges to count
        pulseperrev : the number of pulses we expect per rev per pin (= number of rising edges - twice this number counted in 'both' edge mode
        parent      : object that provides function needservice to get pigpio shared instance 
        isforward   : a function that returns True if the motor is / was moving forward 
                            (if the motor has been set to zero speed, it may not yet have stopped) - can be set later if appropriate
        initialpos  : sets the starting position of the motor
        """
        self.piggy=parent.needservice(sname='piggy', className='pigpio.pi')
        self.edgemode = pigpio.RISING_EDGE if edges=='rising' else pigpio.FALLING_EDGE if edges=='falling' else pigpio.EITHER_EDGE
        self.ticksperrev = pulsesperrev*len(pinss)
        if self.edgemode==pigpio.EITHER_EDGE:
            self.ticksperrev *= 2
        if not pinss is None:
            for sp in pinss:
                assert isinstance(sp, int) and sp>=0
                self.piggy.set_mode(sp, pigpio.INPUT)
            self.scb=[self.piggy.callback(pn, self.edgemode) for pn in pinss]
        else:
            self.scb=[]
        self.lasttallytime=time.time()
        self.mss=pinss
        self.lasttallyread=sum([s.tally() for s in self.scb])
        self.lastmotorpos=initialpos
        self.prevmotorpos=initialpos
        self.lasttallydiff=0
        self.lasttallyinterval=0
        self.isforwardfunc=isforward

    def setforwardfunc(self,f):
        self.isforwardfunc=f

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

    def tick(self):
        """
        This method updates the motor position by reading the tally count and adjusting the motor position appropriately.
        
        The tally counter always increases as it has no awareness of the motor's direction, so we use the motors last
        direction to check whether to add or subtract.
        
        The motorpos is recorded in revolutions
        
        returns: 2-tuple, timestamp for the last reading and the change in motorpos in revs
        """
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
#        self.log(ltype='tally', prev=self.prevmotorpos, now=self.lastmotorpos, fwd=self.motorforward, change=tallydiff)
        return self.lasttallytime, self.lastmotorpos-self.prevmotorpos
