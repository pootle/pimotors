#!/usr/bin/python3

"""
This module provides feedback control for motors

So far a PID controller......
"""
class PIDfeedback():
    """
    This class can be used as part of a dc motor controller. It provides feedback control using a PID controller
    
    (https://en.wikipedia.org/wiki/PID_controller)
    
    It handles only the error value, the calling software works out what the error is to allow it to be calculated in
    or measured in different ways.
    
    This is a pretty trivial class so far
    """
    def __init__(self, timenow, Pfact, Ifact, Dfact):
        """
        timenow : timestamp of initial reading /  setup
        Pfact   : Proportion factor
        Ifact   : Integral factor
        Dfact   : Derivative (slope) factor
        """
        self.timeprev  = timenow
        self.timestart = timenow
        self.errorprev = 0
        self.errortotal= 0
        self.Pfact     = Pfact
        self.Ifact     = Ifact
        self.Dfact     = Dfact

    def reset(self, timenow, errornow):
        """
        simple reset function to save having to discard and recreate an instance
        """
        self.timeprev  = timenow
        self.timestart = timenow
        self.errorprev = 0
        self.errortotal= 0

    def factors(self, Pfact=None, Ifact=None, Dfact=None):
        """
        set and return any combination of the factors
        
        Any parameter not None will update that factor to the supplied Value.
        
        return a 3-tuple of the values
        """
        if not Pfact is None:
            self.Pfact=Pfact
        if not Ifact is None:
            self.Ifact=Pfact
        if not Dfact is None:
            self.Dfact=Pfact
        return self.Pfact, self.Ifact, self.Dfact

    def onefact(self, factor, newvalue):
        """
        set and return a single factor
        
        factor : 'P', 'I', or 'D'
        
        value  : None to just return the current value, or an integer or float to set and return the new value
        """
        assert newvalue is None or isinstance(newvalue,(int, float, str)), 'Value is not a number'
        value = float(newvalue) if isinstance(newvalue, str) else newvalue
        if factor=='P':
            if not value is None:
                self.Pfact=value
            return self.Pfact
        elif factor=='I':
            if not value is None:
                self.Ifact=value
            return self.Ifact
        elif factor=='D':
            if not value is None:
                self.Dfact=='D'
            return self.Dfact
        else:
            raise ValueError('factor should be "P", "I" or "D"; not %S' % str(factor))

    def ticker(self, timenow, errornow):
        """
        called on a regular basis, this calculates the correction factor to be applied.
        
        as long as ticks are regular we don't need to use the time as part of the slope calculation,
        
        timenow  : time at which the position was measured
        
        errornow : the absolute error at that time - note this is the error in position, not the error in velocity
        """
        lastinterval    = timenow-self.timeprev
        slope           = errornow-self.errorprev
        self.errortotal += errornow
        self.errorprev  = errornow
        self.timeprev   = timenow
        return self.Pfact*errornow + self.Ifact*self.errortotal + self.Dfact*slope

    def odef(self):
        return {'className': type(self).__name__, 'Pfact': self.Pfact, 'Ifact': self.Ifact, 'Dfact': self.Dfact}
