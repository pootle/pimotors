#!/usr/bin/python3
#def dc hat 2 motors on an adafruit dc and stepper motor hat
#no feedback

motordef=(
    {'dchparams':{'motorno':4, 'invert': True},
     'basicmotor':{'name':'left'},},
    {'dchparams':{'motorno':3},
     'basicmotor':{'name':'right'},},
)
