#!/usr/bin/python3
# definition file for 2 H bridge motors directly controlled via gpio pins. 'left' and 'right'
# feedback via gpio connected quad encoders using pigpio edge counting
# uses the analyser class
motordef=(
    {'direct_h':{'pinf':20, 'pinb':19},
     'senseparams': {'pinss': ((9, 10)), 'edges': 'both', 'pulsesperrev':3},
     'analysemotor': {'name':'left'},},
    {'direct_h':{'pinf':26, 'pinb':21},
     'senseparams': {'pinss': ((17, 27)), 'edges': 'both', 'pulsesperrev':3},
     'analysemotor': {'name':'right'},},
)
