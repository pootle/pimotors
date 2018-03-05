#!/usr/bin/python3

import textdisp, keyboardinp

from textdisp import dispfield as df, inpfield, selector
import motorset

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
            goodval = None
            if not self.vcb is None and not dcadj is None:
                goodval=self.vcb(value=self.value+dcadj, **self.vcbp)                
            if key=='0':
                if not self.vcb is None:
                    goodval=self.vcb(value=0, **self.vcbp)
                else:
                    goodval=0
            if not goodval is None:
                if isinstance(goodval, dict):
                    self.parent.setFieldValues('mduty', values=goodval)
                    goodval=[v for v in goodval.values()][0]
                goodval = self.setValue(goodval)
                return True, not goodval is None
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
                if isinstance(goodval, dict):
                    self.parent.setFieldValues('mfrequ', values=goodval)
                    goodval=[v for v in goodval.values()][0]
                goodval=self.setValue(goodval)
                return True, not goodval is None
            return True, False
        return True, False


def updatemotor(mname, matt, value):
    return getattr(m.motors[mname],matt)(value)

def updatemotorlist(motors, funcname, value):
    resu=getattr(m, funcname)(value, motors)
    return resu

def runmotorfunc(**kwargs):
    m.runmotorfunc(**kwargs)     

def1=(
#    {'name':'dmon'   , 'fclass':  df    ,'lineno': 0,'colno':20, 'style': 'label', 'format': 'last key:{:4s} hex:{:12s}','value':('',''), 'fmode':'*'},
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
    {'name':'mrpml'  , 'fclass':  df    ,'lineno':11,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'RPM','atts': 'h'},
    {'name':'manall' , 'fclass':  df    ,'lineno':12,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'motor test', 'atts': 'h'},
    
    {'name':'inlab'  , 'fclass':  df    ,'lineno':13,'colno':0 , 'style': 'label', 'format': '{:>20s}:', 'value':''},
    {'name':'inval'  , 'fclass':  df    ,'lineno':13,'colno':22, 'style': 'nonactinp', 'format': None, 'value':''}
)

jointfields=(
    {'name':'mname*' , 'fclass':  df    ,'lineno': 4,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':'*all*'},
    {'name':'mfrequ*', 'fclass':  freqf ,'lineno': 7,'colno':14, 'style': 'output', 'format': '{:>7d}Hz      ', 'value':0, 'atts': 't',
                'valuecallback':updatemotorlist, 'cbparams': {'motors':None, 'funcname': 'motorFrequency'}},
    {'name':'mduty*' , 'fclass':  dcfield,'lineno': 8,'colno':14, 'style': 'output', 'format': '{:>7d}/255    ', 'value':0, 'atts': 't',
                'valuecallback':updatemotorlist, 'cbparams': {'motors':None, 'funcname': 'motorDC'}},
    {'name':'mposn*' , 'fclass':  df    ,'lineno':10,'colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'mrpm*'  , 'fclass':  df    ,'lineno':11,'colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'manal*' , 'fclass':selector,'lineno':12,'colno':14, 'style': 'output', 'format': '{:^15.15s}','value':'none', 'atts': 'th',
                'selectmap': (('none', 'no action'),('findMaxrpm','max rpm')),
                'returncallback': runmotorfunc, 'cbparams': {'motors':None, }},
)

motorfields=(
    {'name':'mname' , 'fclass':  df    ,'lineno': 4,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':''},
    {'name':'mtype' , 'fclass':  df    ,'lineno': 5,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':''},
    {'name':'mdrvt' , 'fclass':  df    ,'lineno': 6,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':''},
    {'name':'mfrequ', 'fclass':  freqf ,'lineno': 7,'colno':14, 'style': 'output', 'format': '{:>7d}Hz      ', 'value':0, 'atts': 't',
                'valuecallback':updatemotorlist, 'cbparams': {'motors':'x', 'funcname': 'motorFrequency'}},
    {'name':'mduty' , 'fclass':  dcfield,'lineno': 8,'colno':14, 'style': 'output', 'format': '{:>7d}/255    ', 'value':0, 'atts': 't',
                'valuecallback':updatemotorlist, 'cbparams': {'motors':'x', 'funcname': 'motorDC'}},
    {'name':'minv'  , 'fclass':selector,'lineno': 9,'colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':False, 'atts': 't',
                'selectmap': ((False,'forward'),(True,'reverse')),
                'valuecallback':updatemotorlist, 'cbparams': {'motors':'x', 'funcname': 'motorInvert'}},
    {'name':'mposn' , 'fclass':  df    ,'lineno':10,'colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'mrpm'  , 'fclass':  df    ,'lineno':11,'colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'manal' , 'fclass':selector,'lineno':12,'colno':14, 'style': 'output', 'format': '{:^15.15s}','value':'none', 'atts': 'th',
                'selectmap': (('none', 'no action'),('findMaxrpm','max rpm')),
                'returncallback': runmotorfunc, 'cbparams': {'motors':'x', }},
)

mcols=[14,33,52]

#def dc hat 2 motors on an adafruit dc and stepper motor hat
motordefdchat=(
    {'dchparams':{'motorno':4, 'invert': True},
     'basicmotor':{'name':'left'},},
    {'dchparams':{'motorno':3},
     'basicmotor':{'name':'right'},},
)

import time
class tester(motorset.motorset):
    def __init__(self, mparams):
        super().__init__(motordefs=mparams, piggy=None)
        usenames='basicmotor' if 'basicmotor' in mparams[0] else 'analysemotor'
        motnames=[m[usenames]['name'] for m in mparams]
        self.dp=textdisp.display(def1, colnames=motnames, setdebug=False)
        self.dp.updateFieldValue('cnote',self.dp.numcolours)
        self.keymon=keyboardinp.CheckConsole()
        self.tickcount=0
        self.menuacts={
            'x': self.exit,
            'a': self.nameMotor,
        }
        self.dp.setHotkeyActs(self.menuacts)
        first=True
        staranal=False
        starfeedback=False
        for midx, mname in enumerate(motnames):
            for mf in motorfields:
                fmf=mf.copy()
                fmf['name']+=mname
                fmf['colno']=mcols[midx]
                if 'cbparams' in fmf:
                    cbp=fmf['cbparams'].copy()
                    cbp['motors']=mname
                    fmf['cbparams']=cbp
                self.dp.addfield(fmf)
            mtype=type(self.motors[mname]).__name__
            self.dp.updateFieldValue('mname%s' % mname, mname)
            self.dp.updateFieldValue('mtype%s' %mname, mtype)
            self.dp.updateFieldValue('mdrvt%s' %mname, type(self.motors[mname].mdrive).__name__)
            self.dp.updateFieldValue('mfrequ%s' %mname, self.motorFrequency(None, mname))
            self.dp.updateFieldValue('mduty%s' %mname, self.motorDC(None, mname))
            self.dp.updateFieldValue('minv%s' %mname, self.motorInvert(None, mname))
            if not self.lastMotorPosition(mname) is None:
                if first:
                    self.dp.setFieldAtt('mposnl', 'h', False)
                    self.dp.setFieldAtt('mrpml', 'h', False)
                    first=False
                    starfeedback=True
                self.dp.setFieldAtt('mposn%s' % mname, 'h', False)
                dv=self.lastMotorPosition(mname)
                self.dp.updateFieldValue('mposn%s' % mname, 0 if dv is None else dv)
                self.dp.setFieldAtt('mrpm%s' % mname, 'h', False)
                dv=self.lastMotorRPM(mname)
                self.dp.updateFieldValue('mrpm%s' % mname, 0 if dv is None else dv)
                if mtype=='motoranalyse':
                    self.dp.setFieldAtt('manal%s' % mname, 'h', False)
                    self.dp.setFieldAtt('manall', 'h', False)
                    staranal=True
        if len(motnames) > 0:
            jcol=mcols[len(motnames)]
            for f in jointfields:
                f['colno']=jcol
                self.dp.addfield(f)
            if starfeedback:
                self.dp.setFieldAtt('mposn*', 'h', False)
                self.dp.setFieldAtt('mrpm*', 'h', False)
            if staranal:
                self.dp.setFieldAtt('manal*', 'h', False)

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
                    if 'dmon' in self.dp.fields:
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
                ress=self.lastMotorPosition(None)
                if not ress is None:
                    self.dp.setFieldValues('mposn', values=ress)
                    if 'right' in ress and 'left' in ress and not ress['right'] is None and not ress['left'] is None:
                        self.dp.updateFieldValue('mposn*', ress['right']-ress['left'])
                ress=self.lastMotorRPM(None)
                if not ress is None:
                    self.dp.setFieldValues('mrpm', values=ress)
                    if 'right' in ress and 'left' in ress and not ress['right'] is None and not ress['left'] is None:
                        self.dp.updateFieldValue('mrpm*', ress['right']-ress['left'])
            self.dp.show()
        self.keymon.close()
        self.close()
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

    def runmotorfunc(self, motors, value, **kwargs):
        self._listcall(units=motors, method=value, **kwargs)
        return

if __name__ == '__main__':
    import argparse
    import importlib

    clparse = argparse.ArgumentParser(description="U3A RPi project motor driver.")
    clparse.add_argument('-t', '--tick', type=float, default=.05, help="tick period in seconds, typically .1 to .01 seconds")
    clparse.add_argument('config', help='configuration file to use')
    args=clparse.parse_args()
    conf=importlib.import_module(args.config)

    m=tester(conf.motordef)
    m.tickloop(interval=args.tick)
