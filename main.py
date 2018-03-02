#!/usr/bin/python3

import textdisp, keyboardinp

from textdisp import dispfield as df, inpfield, selector

class dcfield(inpfield):
    def offerkey(self, key):
        if key in ('UPARR', 'DNARR', 'LTARR', 'RTARR','0',):
            dcadj=None
            if key=='UPARR':
                dcadj=10
            elif key=='DNARR':
                dcadj=-10
            elif key=='RTARR':
                dcadj=1
            elif key=='LTARR':
                dcadj=-1
            if not dcadj is None:
               newvalue=self.value+dcadj
            if not self.vcb is None and not dcadj is None:
                goodval=self.vcb(value=self.value+dcadj, **self.vcbp)
                return True, self.setValue(goodval)
            if key=='0':
                if not self.vcb is None:
                    goodval=self.vcb(value=0, **self.vcbp)
                else:
                    goodval=0
                return True, self.setValue(goodval)
            return True, False
        return True, False

class freqf(inpfield):
    def offerkey(self, key):
        if key in ('UPARR', 'DNARR', 'LTARR', 'RTARR'):
            dcadj=None
            if key=='UPARR':
                dcadj=2
            elif key=='DNARR':
                dcadj=.5
            elif key=='RTARR':
                dcadj=1.1
            elif key=='LTARR':
                dcadj=.9
            if not self.vcb is None and not dcadj is None:
                goodval=self.vcb(value=int(round(self.value*dcadj)), **self.vcbp)
                return True, self.setValue(goodval)
            return True, False
        return True, False


def updatemotor(mname, matt, value):
    return getattr(m.motors[mname],matt)(value)

def1=(
    {'name':'dmon'   , 'fclass':  df    ,'lineno': 0,'colno':20, 'style': 'label', 'format': 'last key:{:4s} hex:{:12s}','value':('',''), 'fmode':'*'},
    {'name':'title'  , 'fclass':  df    ,'lineno': 1,'colno':0 , 'style': 'label', 'format': '{:^32}', 'value':'pootles likkle app'},
    {'name':'cnote'  , 'fclass':  df    ,'lineno': 1,'colno':34, 'style': 'label', 'format': 'cc:{:3d}.', 'value':1},
    {'name':'onote'  , 'fclass':  df    ,'lineno': 1,'colno':44, 'style': 'label', 'format': 'or:{:3d}.', 'value':0},
    {'name':'clock'  , 'fclass':  df    ,'lineno': 1,'colno':54, 'style': 'label', 'format': '{:02d}:{:2d}:{:2d}', 'value':(0,0,0), 'fmode': '*'},
    {'name':'m0'     , 'fclass':  df    ,'lineno': 2,'colno':1 , 'style': 'label', 'format': None, 'value':'e'},
    {'name':'m0z'    , 'fclass':  df    ,'lineno': 2,'colno':2 , 'style': 'label', 'format': None, 'value':'X', 'atts': 'u'},
    {'name':'m0y'    , 'fclass':  df    ,'lineno': 2,'colno':3 , 'style': 'label', 'format': None, 'value':'it'},
    {'name':'m1z'    , 'fclass':  df    ,'lineno': 2,'colno':6 , 'style': 'label', 'format': None, 'value':'A', 'atts': 'u'},
    {'name':'m1y'    , 'fclass':  df    ,'lineno': 2,'colno':7 , 'style': 'label', 'format': None, 'value':'dd motor'},
    {'name':'mnamel' , 'fclass':  df    ,'lineno': 4,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'motor name'},
    {'name':'mtypel' , 'fclass':  df    ,'lineno': 5,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'motor type'},
    {'name':'mdrvtl' , 'fclass':  df    ,'lineno': 6,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'driver'},
    {'name':'mfrequl', 'fclass':  df    ,'lineno': 7,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'frequency'},
    {'name':'mdutyl' , 'fclass':  df    ,'lineno': 8,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'duty cycle'},
    {'name':'minvl'  , 'fclass':  df    ,'lineno': 9,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'reverse'},
    {'name':'mposnl' , 'fclass':  df    ,'lineno':10,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'position','atts': 'h'},
    {'name':'mrpml'  , 'fclass':  df    ,'lineno':11,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'position','atts': 'h'},
    
    {'name':'mnameleft' , 'fclass':  df    ,'lineno': 4,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':'', 'atts': 'h'},
    {'name':'mtypeleft' , 'fclass':  df    ,'lineno': 5,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':'', 'atts': 'h'},
    {'name':'mdrvtleft' , 'fclass':  df    ,'lineno': 6,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':'', 'atts': 'h'},
    {'name':'mfrequleft', 'fclass':  freqf ,'lineno': 7,'colno':14, 'style': 'output', 'format': '{:>7d}Hz      ', 'value':0, 'atts': 'h',
                'valuecallback':updatemotor, 'cbparams': {'mname':'left', 'matt': 'setFrequency'}},
    {'name':'mdutyleft' , 'fclass':  dcfield,'lineno': 8,'colno':14, 'style': 'output', 'format': '{:>7d}/255    ', 'value':0, 'atts': 'h',
                'valuecallback':updatemotor, 'cbparams': {'mname':'left', 'matt': 'setDC'}},
    {'name':'minvleft'  , 'fclass':selector,'lineno': 9,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':False, 'atts': 'h',
                'selectmap': ((False,'forward'),(True,'reverse')),
                'valuecallback':updatemotor, 'cbparams': {'mname':'left', 'matt': 'setInvert'}},
    {'name':'mposnleft' , 'fclass':  df    ,'lineno':10,'colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'mrpmleft'  , 'fclass':  df    ,'lineno':11,'colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},

    {'name':'mnameright' , 'fclass':  df    ,'lineno': 4,'colno':33, 'style': 'output', 'format': '{:^15.15s}', 'value':'', 'atts': 'h'},
    {'name':'mtyperight' , 'fclass':  df    ,'lineno': 5,'colno':33, 'style': 'output', 'format': '{:^15.15s}', 'value':'', 'atts': 'h'},
    {'name':'mdrvtright' , 'fclass':  df    ,'lineno': 6,'colno':33, 'style': 'output', 'format': '{:^15.15s}', 'value':'', 'atts': 'h'},
    {'name':'mfrequright', 'fclass':  freqf ,'lineno': 7,'colno':33, 'style': 'output', 'format': '{:>7d}Hz      ', 'value':0, 'atts': 'h',
                'valuecallback':updatemotor, 'cbparams': {'mname':'right', 'matt': 'setFrequency'}},
    {'name':'mdutyright' , 'fclass':  dcfield,'lineno': 8,'colno':33, 'style': 'output', 'format': '{:>7d}/255    ', 'value':0, 'atts': 'h',
                'valuecallback':updatemotor, 'cbparams': {'mname':'right', 'matt': 'setDC'}},
    {'name':'minvright'  , 'fclass':selector,'lineno': 9,'colno':33, 'style': 'output', 'format': '{:^15.15s}', 'value':False, 'atts': 'h',
                'selectmap': ((False,'forward'),(True,'reverse')),
                'valuecallback':updatemotor, 'cbparams': {'mname':'right', 'matt': 'setInvert'}},
    {'name':'mposnright' , 'fclass':  df    ,'lineno':10,'colno':33, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'mrpmright'  , 'fclass':  df    ,'lineno':11,'colno':33, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},

    {'name':'inlab'  , 'fclass':  df    ,'lineno':12,'colno':0 , 'style': 'label', 'format': '{:>20s}:', 'value':''},
    {'name':'inval'  , 'fclass':  df    ,'lineno':12,'colno':22, 'style': 'nonactinp', 'format': None, 'value':''}
)
deftabsequ= ('mfrequleft', 'mdutyleft', 'minvleft', 'mfrequright', 'mdutyright', 'minvright')

#def1 2 motors on h-bridges directly controlled from gpio pins using pigpio pwm
motordef1=(
    {'direct_h':{'pinf':20, 'pinb':19},
     'basicmotor': {'name':'left'},
    },
    {'direct_h':{'pinf':26, 'pinb':21},
     'basicmotor': {'name':'right'},
    },
)

#def2 2 motors on h-bridges directly controlled from pigpio (as def1) with rotation quadrature sensors monitored by pigpio that track motor position
motordef2=(
    {'direct_h':{'pinf':20, 'pinb':19},
     'senseparams': {'pinss': ((9, 10)), 'edges': 'both', 'pulsesperrev':3},
     'basicmotor': {'name':'left'},},
    {'direct_h':{'pinf':26, 'pinb':21},
     'senseparams': {'pinss': ((17, 27)), 'edges': 'both', 'pulsesperrev':3},
     'basicmotor': {'name':'right'},},
)

#def dc hat 2 motors on an adafruit dc and stepper motor hat
motordefdchat=(
    {'dchparams':{'motorno':4, 'invert': True},
     'basicmotor':{'name':'left'},},
    {'dchparams':{'motorno':3},
     'basicmotor':{'name':'right'},},
)

import time
class tester():
    def __init__(self, mparams):
        self.dcmh=None
        self.piggy=None
        self.motors={}
        self.activefreq=200
        self.activedutycycle=0
        for mdef in mparams:
            if 'dchparams' in mdef:
                if self.dcmh is None:
                    from dc_adafruit_dchat import dc_m_hat, dcmotorHatExtra
                    self.dcmh = dcmotorHatExtra(addr=0x60, freq=self.activefreq)
                mdrv=dc_m_hat(mhat=self.dcmh, **mdef['dchparams'])
            elif 'direct_h' in mdef:
                if self.piggy is None:
                    from dc_h_bridge_pigpio import dc_h_bridge
                    import pigpio
                    self.piggy=pigpio.pi()
                mdrv=dc_h_bridge(frequency=self.activefreq, piggy=self.piggy, **mdef['direct_h'])
            else:
                raise ValueError("motor def must have key 'dchparams' or 'direct_h'")
            mot=None
            if 'basicmotor' in mdef:
                if 'senseparams' in mdef:
                    import quadencoder
                    if self.piggy is None:
                        self.piggy=pigpio.pi()
                    sens=quadencoder.quadencoder(piggy=self.piggy, **mdef['senseparams'])
                else:
                    sens=None
                import dcmotorbasic
                mot=dcmotorbasic.motor(mdrive=mdrv, sensor=sens, **mdef['basicmotor'])
            if not mot is None:
                self.motors[mot.name]=mot

        self.dp=textdisp.display(def1, tabsequ=deftabsequ, setdebug=False)
        self.dp.updateFieldValue('cnote',self.dp.numcolours)
        self.keymon=keyboardinp.CheckConsole()
        self.tickcount=0
        self.menuacts={
            'x': self.exit,
            'a': self.nameMotor,
        }
        self.dp.setHotkeyActs(self.menuacts)
        
        for mname, m in self.motors.items():
            self.dp.setFieldAtt('mname%s' % mname, 'h', False)
            self.dp.updateFieldValue('mname%s' % mname, m.name)
            self.dp.setFieldAtt('mtype%s' % mname, 'h', False)
            self.dp.updateFieldValue('mtype%s' %mname, type(m).__name__)
            self.dp.setFieldAtt('mdrvt%s' % mname, 'h', False)
            self.dp.updateFieldValue('mdrvt%s' %mname, type(m.mdrive).__name__)
            self.dp.setFieldAtt('mfrequ%s' % mname, 'h', False)
            self.dp.updateFieldValue('mfrequ%s' %mname, self.activefreq)
            self.dp.setFieldAtt('mduty%s' % mname, 'h', False)
            self.dp.updateFieldValue('mduty%s' %mname, self.activedutycycle)
            self.dp.setFieldAtt('minv%s' % mname, 'h', False)
            self.dp.updateFieldValue('minv%s' %mname, m.getInvert())
            if not m.lastposition() is None:
                self.dp.setFieldAtt('mposnl', 'h', False)
                self.dp.setFieldAtt('mposn%s' % mname, 'h', False)
                self.dp.updateFieldValue('mposn%s' %mname, m.lastposition())
                self.dp.setFieldAtt('mrpml', 'h', False)
                self.dp.setFieldAtt('mrpm%s' % mname, 'h', False)

    def tickloop(self, interval):
        self.nexttick = time.time()+interval
        self.running=True
        while self.running:
            wt=self.nexttick-time.time()
            k=self.keymon.get_data(max(0,wt))
            # do the motor tick first to minimise jitter
            for m in self.motors.values():
                m.ticker(wt)
            self.nexttick+=interval
            if not k is None:
                if self.dp.offerkey(k):
                    pass
                else:
                    zkey=str(k)
                    zkey = ''.join(c if ord(c) > 32 else '' for c in k)
                    hexish = ":".join("{:02x}".format(ord(c)) for c in k)
                    self.dp.updateFieldValue('dmon',(zkey, hexish))
            self.tickcount += 1
            if self.tickcount > 20:
                self.tickcount=0
                if 'clock' in self.dp.fields:
                    tm, ts=divmod(int(time.time()),60)
                    th, tm=divmod(tm,60)
                    self.dp.updateFieldValue('clock', (th % 24, tm, ts))
                for m in self.motors.values():
                    pos=m.lastposition()
                    if not pos is None:
                        self.dp.updateFieldValue('mposn%s' % m.name, pos)
                    mrpm=m.lastrpm()
                    if not mrpm is None:
                        self.dp.updateFieldValue('mrpm%s' % m.name, mrpm)
            self.dp.show()
        self.keymon.close()
        if not self.piggy is None:
            self.piggy.stop()
            self.piggy=None

    def exit(self):
        self.running=False
        self.keymon.close()

    def nameMotor(self):
        self.dp.updateFieldValue('inlab','motor name')
        self.dp.editfield('inval','', self.makeMotor)

    def makeMotor(self,x,y):
        pass

if __name__ == '__main__':
    m=tester(motordef2)
    m.tickloop(interval=.05)
