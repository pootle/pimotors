#!/usr/bin/python3
# definition file for 2 H bridge motors directly controlled via gpio pins. 'left' and 'right'
# feedback via gpio connected quad encoders using pigpio edge counting
motordef=(
    {'direct_h':{'pinf':26, 'pinb':21, 'invert': True},
     'senseparams': {'pinss': ((17, 27)), 'edges': 'both', 'pulsesperrev':3},
     'basicmotor': {'name':'left',
                    'speedmapinfo': {'fbuilder': {'minSpeed':1500, 'maxSpeed':13000, 'minDC':20, 'maxDC':255},
                                     'rbuilder': {'minSpeed':1500, 'maxSpeed':13000, 'minDC':20, 'maxDC':255}}},
     },
    {'direct_h':{'pinf':20, 'pinb':19},
     'senseparams': {'pinss': ((9, 10)), 'edges': 'both', 'pulsesperrev':3},
     'basicmotor': {'name':'right',
                    'speedmapinfo': {'fbuilder': {'minSpeed':1500, 'maxSpeed':13000, 'minDC':20, 'maxDC':255},
                                     'rbuilder': {'minSpeed':1500, 'maxSpeed':13000, 'minDC':20, 'maxDC':255}}},
    },
)
