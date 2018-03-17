#!/usr/bin/python3
#definition file for 2 H bridge motors directly controlled via gpio pins. 'left' and 'right'
#no feedback
motordef=(
    {'direct_h':{'pinf':20, 'pinb':19},
     'basicmotor': {'name':'left',
                    'speedmapinfo': {'fbuilder': {'minSpeed':29, 'maxSpeed':160, 'minDC':20, 'maxDC':255},
                                     'rbuilder': {'minSpeed':29, 'maxSpeed':160, 'minDC':20, 'maxDC':255}}},
    },
    {'direct_h':{'pinf':26, 'pinb':21},
     'basicmotor': {'name':'right'},
    },
)
