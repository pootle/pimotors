#!/usr/bin/python3

import time

class motorset():
    """
    Creates a set of motors identified by their names.
    
    After setup many methods use the set of motors defined by the type of the mlist - see below.
    
    Other methods to provide co-ordinated actions, such as turning or attempting to keep straight will
    be defined at this level.
    
    The mlist parameter (common to many commands that directly control a motor)

    default                 : (None) All motors are used
    string                  : (name of motor) Only the motor identified by the name is used
    tuple, list, array...   : each entry is the name of a motor, all motors named are used
    """
    def __init__(self, motordefs=None, piggy=None):
        """
        Sets up motors from a list of dicts, each dict defines the details of an individual motor.
        
        piggy       : a pigpio instance to use if needed. If None, an instance will be created if any of the underlying
                        classes require it.

        motordefs   : a list of dicts, 1 per motor to be setup. Each dict uses the following keys:
                'basicmotor': creates a motor instance of type dcmotorbasic.motor.
                                The 'name' parameter is the key by which the motor will be identified within this motor set.
                'sensparams': if present, maps to a dict that defines the key info about a rotary encoder attached to the motor.
                                see quadencoder.quadencoder for details.
                'dchparams' : if present, maps to a dict that defines the key info for a dc motor driven by an adafruit dc motor hat.
                                see dc_adafruit_dchat.dc_m_hat. For now, only one hat, using a default address, is supported.
                'direct_h'  : if present, maps to a dict the defines the key info for a dc motor driven by an h-bridge controlled 
                                gpio pins on the local machine.
                                see dc_h_bridge_pigpio.dc_h_bridge for details.
                in this version, each motor must have an associated dchparams or direct_h entry.
        """
        self.piggy=piggy
        self.dcmh = None
        self.motors={}
        for mdef in motordefs:
            if 'dchparams' in mdef:
                if self.dcmh is None:
                    from dc_adafruit_dchat import dc_m_hat, dcmotorHatExtra
                    self.dcmh = dcmotorHatExtra(addr=0x60, freq=200)
                mdrv=dc_m_hat(mhat=self.dcmh, **mdef['dchparams'])
            elif 'direct_h' in mdef:
                from dc_h_bridge_pigpio import dc_h_bridge
                if self.piggy is None:
                    import pigpio
                    self.piggy=pigpio.pi()
                mdrv=dc_h_bridge(frequency=200, piggy=self.piggy, **mdef['direct_h'])
            else:
                raise ValueError("motor def must have key 'dchparams' or 'direct_h'")
            mot=None
            if 'senseparams' in mdef:
                import quadencoder
                if self.piggy is None:
                    import pigpio
                    self.piggy=pigpio.pi()
                sens=quadencoder.quadencoder(piggy=self.piggy, **mdef['senseparams'])
            else:
                sens=None
            if 'basicmotor' in mdef:
                import dcmotorbasic
                mot=dcmotorbasic.motor(mdrive=mdrv, sensor=sens, **mdef['basicmotor'])
            elif 'analysemotor' in mdef:
                import motoranalyser
                mot=motoranalyser.motoranalyse(mdrive=mdrv, sensor=sens, **mdef['analysemotor'])
            if not mot is None:
                self.motors[mot.name]=mot

    def lastMotorPosition(self, mlist=None):
        """
        fetches last known position for the specified motors (see class help for mlist param)
        """
        return self._listcall(mlist, 'lastPosition')

    def lastMotorRPM(self, mlist=None):
        """
        returns the last known RPM for the specified motors (see class help for mlist param)
        """
        return self._listcall(mlist, 'lastRPM')

    def motorInvert(self, inv, mlist=None):
        """
        return and optionlly reverse the motor direction for specified motors (see class help for mlist param)
        """
        return self._listcall(mlist, 'invert', inv)

    def motorFrequency(self, f, mlist=None):
        """
        sets the frequency used for the dutycycle (see class help for mlist param)
        
        f:    if None the frequency is unchanged
        
        returns the current frequency
        """
        return self._listcall(mlist, 'frequency', f)

    def motorDC(self, dutycycle, mlist=None):
        """
        directly sets the duty cycle of the given set of motors (see class help for mlist param)
        
        See the motor class for details of the dutycycle param.
        """
        return self._listcall(mlist, 'DC', dutycycle)

    def motorTargetRPM(self, rpm, mlist=None):
        """
        returns and optionally sets the target rpm of the given set of motors (see class help for mlist param)
        
        See the motor class for details of the speed param.
        """
        return self._listcall(mlist, 'targetRPM', rpm)

    def stopMotor(self, mlist=None):
        """
        stops specified motors (see class help for mlist param)
        """
        for u in self._delist(mlist):
            u.stop()

    def close(self):
        """
        completely shuts down this instance and deletes all internal knowledge of motors
        """
        for m in self._delist(None):
            m.close()
        time.sleep(.5)
        if not self.piggy is None:
            self.piggy.stop()
            self.piggy=None
        self.motors={}

    def ticker(self, waittime):
        """
        called at (hopefully very) regular intervals to provide feedback control for the motors
        
        waittime: the time the outer cycle waited to align tick time - allows this to be added to logging
        """
        for m in self.motors.values():
            m.ticker(waittime)

#######################################################################################
# INTERNAL STUFF
    def _delist(self, units):
        """
        internal routine converts / validates units param to list of motors
        """ 
        if units is None:
            return tuple(self.motors.values())
        elif isinstance(units,str):
            if units in self.motors:
                return (self.motors[units],)
            else:
                raise ValueError('%s is not a known motor name' % units)
        else:
            for u in units:
                if not u in self.motors:
                    self.stopMotor()
                    raise ValueError('%s is not a known motor name' % str(u))
            return [self.motors[m] for m in units]

    def _listcall(self, units, method, *args, **kwargs):
        if units is None:
            return {m.name: getattr(m, method)(*args, **kwargs) for m in self.motors.values()}
        elif isinstance(units, str):
            return getattr(self.motors[units], method)(*args, **kwargs)
        else:
            return {m: getattr(self.motors[m], method)(*args, **kwargs) for m in units}
