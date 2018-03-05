#!/usr/bin/python3
#definition file for 2 H bridge motors directly controlled via gpio pins. 'left' and 'right'
#no feedback
motordef=(
    {'direct_h':{'pinf':20, 'pinb':19},
     'basicmotor': {'name':'left'},
    },
    {'direct_h':{'pinf':26, 'pinb':21},
     'basicmotor': {'name':'right'},
    },
)
