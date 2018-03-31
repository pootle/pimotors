#!/usr/bin/python3
""" 
definition file for 2 H bridge motors directly controlled via gpio pins. The motors are 'left' and 'right'.

The motors can have rotary encoders and can use a speed mapping table to provide something approaching a linear response.

The configuration is defined by a list of motors. Each entry in the list defines a single motor. The full list defines a motorset's motors.

A single motor definition is defined by a dict, for a full specification see the individual motor class' documentation.
There are currently 2 similar classes that can be used:
    motor in module dcmotorbasic
    motoranayse in module motoranalyser
    
    motoranayse inherits from dcmotorbasic and provides additional methods to test and log the motor's performance. There are
        associated jupyter notebooks that analyse the logs.
    
    Both these classes have the same configuration definitions.

The motor and motoranalyse classes:
    className       : The name of the class to instantiate for this motor. See className in the details below.

    name            : The name of the motor. Used in all further access to the motor within the motorset.
    
    mdrive          : The class that takes care of the low level interface to the motor - typically defined by the hardware in use, and the way in which 
                        it is connected (direct gpio, through a HAT accessed through I2C, ...)
    
    rotationsense   : The class that tracks the motor's movement, it provides methods to detect the angle through which the motor has turned.
    
    speedmapinfo    : The class that takes a requested speed and turns it into the values used by the mdrive class to run the motor. For brushed dc
                        motors here, that is the frequency at which the motor is turned off and on, and the duty cycle that is applied. 

    logtypes        : This is a list of the logging that is to be printed / recorded to file.

Standard parameters:
    className: These strings identify a class, typically as <modulename>.<classname>. The class constructor is then called 
    using everything else in the dict as keyword parameters. Other parameters can be supplied by position or keyword. 
"""
motordef=(
    {
     'className'    : 'motoranalyser.motoranalyse',
#     'className'    : 'dcmotorbasic.motor',
     'name'         : 'left',
     'mdrive'       : {'className': 'dc_h_bridge_pigpio.dc_h_bridge', 'pinf':26, 'pinb':21, 'invert': True},
     'rotationsense': {'className': 'quadencoder.quadencoder', 'pinss': ((17, 27)), 'edges': 'both', 'pulsesperrev':3},
     'speedmapinfo':  {'className': 'dcmotorbasic.speedmapper', 
                       'fbuilder': {'minSpeed':1500, 'maxSpeed':13000, 'minDC':20, 'maxDC':255},
                       'rbuilder': {'minSpeed':1500, 'maxSpeed':13000, 'minDC':20, 'maxDC':255}},
     'feedback'     : {'className': 'feedback.PIDfeedback', 'Pfact': -500, 'Ifact':0, 'Dfact':-100},
     'logtypes'     : (('phys',{'filename': 'leftlog.txt',  'format': '{setting} is {newval}.'}),),
     },
    {
     'className'    : 'motoranalyser.motoranalyse',
#     'className'    : 'dcmotorbasic.motor',
     'name'         : 'right',
     'mdrive'       : {'className': 'dc_h_bridge_pigpio.dc_h_bridge', 'pinf':20, 'pinb':19},
     'rotationsense': {'className': 'quadencoder.quadencoder', 'pinss': ((9, 10)), 'edges': 'both', 'pulsesperrev':3},
     'speedmapinfo' : {'className': 'dcmotorbasic.speedmapper', 
                       'fbuilder': {'minSpeed':1500, 'maxSpeed':13000, 'minDC':20, 'maxDC':255},
                       'rbuilder': {'minSpeed':1500, 'maxSpeed':13000, 'minDC':20, 'maxDC':255}},
     'feedback'     : {'className': 'feedback.PIDfeedback', 'Pfact': 0, 'Ifact':0, 'Dfact':0},
     'logtypes'     : (('phys',{'filename': 'rightlog.txt',  'format': '{setting} is {newval}.'}),),
    },
)
