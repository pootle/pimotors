#!/usr/bin/python3

import time
import logger

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
        self.dcmh = None
        self.motors={}
        for mdef in motordefs:
            mot=logger.makeClassInstance(parent=self, **mdef)
            self.motors[mot.name]=mot

    def needservice(self, servicename):
        """
        called by motor instantiation if it uses a single instance of something
        
        servicename: name of the required class
        """
        try:
            return getattr(self, servicename)
        except AttributeError:
            if servicename=='pigpio':
                import pigpio
                setattr(self,servicename, pigpio.pi())
            else:
                raise ValueError('unknown service instance %s requested' % servicename)
        return getattr(self, servicename)

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

    def motorSpeedLimits(self, mlist=None):
        return self._listcall(mlist, 'speedLimits')

    def motorTargetSpeed(self, speed, mlist=None):
        """
        returns and optionally sets the target rpm of the given set of motors (see class help for mlist param)
        
        See the motor class for details of the speed param.
        """
        return self._listcall(mlist, 'targetSpeed', speed)

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
        piggy=getattr(self,'pigpio', None)
        if not piggy is None:
            piggy.stop()
        self.motors={}

    def ticker(self):
        """
        called at (hopefully very) regular intervals to provide feedback control for the motors
        
        """
        for m in self.motors.values():
            m.ticker()

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
