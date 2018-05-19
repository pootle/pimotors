#!/usr/bin/python3

import pigpio, time

class fastencoder():
    """
    A class to process quadrature encoder info on a motor. It maintains a position and also details of the last measurement interval.

    This version uses the motorset level class quadfast.py to do the lowest level handling of the quad sensor outputs.
    
    It has an update routine that reads the counters and updates the absolute motor position. The position is held as a float and is the number of revs.
    """
    def __init__(self, ticksperrev, parent, pins):
        """
        ticksperrev : the number of pulses we expect per rev per pin (= number of rising edges - twice this number counted in 'both' edge mode
        parent      : object that provides function needservice to get pigpio shared instance
        pins        : pair of gpio pins that monitor the encoder. Note these are ignored here, 'cos they are used by quadfast.py at motorset level
        """
        self.ticksperrev = ticksperrev
        self.pins = pins
        self.lasttallytime=time.time()
        self.gettally=lambda: parent.parent.quadmon.quadpos(parent.name)
        self.lasttallyread=self.gettally()
        self.lastmotorpos=0
        self.prevmotorpos=0
        self.lasttallydiff=0
        self.lasttallyinterval=0

    def close(self):
        pass

    def stopped(self):
        """
        return True if we think the motor is stationary
        """
        return self.lasttallydiff==0

    def __iter__(self):
        """
        The iterator updates the motor position by reading the tally count and adjusting the motor position appropriately.
        
        It returns the latest known motor position.
        
        The motorpos is recorded in revolutions.

        Using an iterator is more efficient than calling a tick function?
        """
        while True:
            tallyr=self.gettally()
            tnow=time.time()
            self.lasttallyinterval=tnow-self.lasttallytime
            self.lasttallytime=tnow
            tallydiff=tallyr-self.lasttallyread
            self.prevmotorpos=self.lastmotorpos
            self.lastmotorpos+=tallydiff / self.ticksperrev
            self.lasttallyread=tallyr
            self.lasttallydiff=tallydiff
            yield(self.lastmotorpos)

    def odef(self):
        return {'className': type(self).__name__, 'ticksperrev': self.ticksperrev, 'pins': self.pins}
        