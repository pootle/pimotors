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

class speedr(inpfield):
    def offerkey(self, key):
        if key in ('UPARR', 'DNARR', 'LTARR', 'RTARR', '0', 'x', 'w'):
            dcadj=None
            if key=='UPARR':
                dcadj=10
            elif key=='DNARR':
                dcadj=-10
            elif key=='RTARR':
                dcadj=2
            elif key=='LTARR':
                dcadj=-2
            elif key=='0':
                dcadj=-self.value
            elif key=='w':
                fmin, fmax=self.parent.getFieldValue('mfwds'+self.vcbp['motors'])
                dcadj=-self.value+fmin
            elif key=='x':
                rmax, rmin=self.parent.getFieldValue('mrevs'+self.vcbp['motors'])
                dcadj=-self.value+rmin
            if not self.vcb is None and not dcadj is None:
                newval=self.value+dcadj
                print('--------------',newval)
                goodval=self.vcb(value=newval, **self.vcbp)
                if isinstance(goodval, dict):
                    self.parent.setFieldValues('mspeed', values=goodval)
                    goodval=[v for v in goodval.values()][0]
                goodval=self.setValue(goodval)
                return True, not goodval is None
            return True, False
        return True, False

def updatemotorlist(motors, funcname, value):
    resu=getattr(m, funcname)(value, motors)
    return resu

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
    {'name':'mrevsl' , 'fclass':  df    ,'lineno': 7,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'rev speeds','atts': 's'},
    {'name':'mfwdsl' , 'fclass':  df    ,'lineno': 8,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'fwd speeds','atts': 's'},
    {'name':'mfrequl', 'fclass':  df    ,'lineno': 9,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'frequency'},
    {'name':'mdutyl' , 'fclass':  df    ,'lineno': 10,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'duty cycle'},
    {'name':'minvl'  , 'fclass':  df    ,'lineno': 11,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'reverse'},
    {'name':'mposnl' , 'fclass':  df    ,'lineno':12,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'position','atts': 's'},
    {'name':'mrpml'  , 'fclass':  df    ,'lineno':13,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'RPM','atts': 's'},
    {'name':'manall' , 'fclass':  df    ,'lineno':14,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'motor test', 'atts': 's'},
    {'name':'mspeedl', 'fclass':  df    ,'lineno':15,'colno':0 , 'style': 'label', 'format': '{:>12.12s}:', 'value':'target rpm', 'atts': 's'},
    
    {'name':'inlab'  , 'fclass':  df    ,'lineno':16,'colno':0 , 'style': 'label', 'format': '{:>20s}:', 'value':''},
    {'name':'inval'  , 'fclass':  df    ,'lineno':16,'colno':22, 'style': 'nonactinp', 'format': None, 'value':''}
)

jointfields=(
    {'name':'mname*' , 'fclass':  df    ,'lineno': '=mnamel','colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':'*all*'},
    {'name':'mfrequ*', 'fclass':  freqf ,'lineno': '=mfrequl','colno':14, 'style': 'output', 'format': '{:>7d}Hz      ', 'value':0, 'atts': 't',
                'valuecallback':updatemotorlist, 'cbparams': {'motors':None, 'funcname': 'motorFrequency'}},
    {'name':'mduty*' , 'fclass':  dcfield,'lineno': '=mdutyl','colno':14, 'style': 'output', 'format': '{:>7d}/255    ', 'value':0, 'atts': 't',
                'valuecallback':updatemotorlist, 'cbparams': {'motors':None, 'funcname': 'motorDC'}},
    {'name':'mposn*' , 'fclass':  df    ,'lineno':'=mposnl','colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'mrpm*'  , 'fclass':  df    ,'lineno':'=mrpml','colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'manal*' , 'fclass':selector,'lineno':'=manall','colno':14, 'style': 'output', 'format': '{:^15.15s}','value':'none', 'atts': 'th',
                'selectmap': (('none', 'no action'),('findMaxrpm','max rpm'), ('mapdcToRPM', 'map dc to speed')),
                'returncallback': 'doMotorAction', 'cbparams': {'motors':None, }},
)

motorfields=(
    {'name':'mname' , 'fclass':  df    ,'lineno': '=mnamel','colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':''},
    {'name':'mtype' , 'fclass':  df    ,'lineno': '=mtypel','colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':''},
    {'name':'mdrvt' , 'fclass':  df    ,'lineno': '=mdrvtl','colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':''},
    {'name':'mrevs' , 'fclass':  df    ,'lineno': '=mrevsl','colno':14, 'style': 'output', 'format': '{:^7.2f}/{:^7.2f}', 'fmode': '*', 'value':(0,0), 'atts': 'h'},
    {'name':'mfwds' , 'fclass':  df    ,'lineno': '=mfwdsl','colno':14, 'style': 'output', 'format': '{:^7.2f}/{:^7.2f}', 'fmode': '*', 'value':(0,0), 'atts': 'h'},
    {'name':'mfrequ', 'fclass':  freqf ,'lineno': '=mfrequl','colno':14, 'style': 'output', 'format': '{:>7d}Hz      ', 'value':0, 'atts': 't',
                'valuecallback':updatemotorlist, 'cbparams': {'motors':'x', 'funcname': 'motorFrequency'}},
    {'name':'mduty' , 'fclass':  dcfield,'lineno': '=mdutyl','colno':14, 'style': 'output', 'format': '{:>7.0f}/255    ', 'value':0, 'atts': 't',
                'valuecallback':updatemotorlist, 'cbparams': {'motors':'x', 'funcname': 'motorDC'}},
    {'name':'minv'  , 'fclass':selector,'lineno': '=minvl','colno':14, 'style': 'output', 'format': '{:^15.15s}', 'value':False, 'atts': 't',
                'selectmap': ((False,'forward'),(True,'reverse')),
                'valuecallback':updatemotorlist, 'cbparams': {'motors':'x', 'funcname': 'motorInvert'}},
    {'name':'mposn' , 'fclass':  df    ,'lineno':'=mposnl','colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'mrpm'  , 'fclass':  df    ,'lineno':'=mrpml','colno':14, 'style': 'output', 'format': '{:^15.3f}', 'value':0, 'atts': 'h'},
    {'name':'manal' , 'fclass':selector,'lineno':'=manall','colno':14, 'style': 'output', 'format': '{:^15.15s}','value':'none', 'atts': 'th',
                'selectmap': (('none', 'no action'),('findMaxrpm','max rpm'), ('mapdcToRPM', 'map dc to speed'), ('mapSpeed', 'test speed map')),
                'returncallback': 'doMotorAction', 'cbparams': {'motors':'x', }},
    {'name':'mspeed' , 'fclass':speedr,'lineno':'=mspeedl','colno':14, 'style': 'output', 'format': '{:^15.3f}','value':100, 'atts': 'th',
                'valuecallback': updatemotorlist, 'cbparams': {'motors':'x', 'funcname': 'motorTargetSpeed'}},
)

mcols=[14,33,52]

import time
class tester(motorset.motorset):
    def __init__(self, mparams):
        super().__init__(motordefs=mparams, piggy=None)
        motnames=[m['name'] for m in mparams]   
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
                if 'returncallback' in fmf:
                    if isinstance(fmf['returncallback'], str):
                        fmf['returncallback']=getattr(self, fmf['returncallback'])
                self.dp.addfield(fmf)
            mtype=type(self.motors[mname]).__name__
            self.dp.updateFieldValue('mname%s' % mname, mname)
            self.dp.updateFieldValue('mtype%s' %mname, mtype)
            self.dp.updateFieldValue('mdrvt%s' %mname, type(self.motors[mname].mdrive).__name__)
            self.dp.updateFieldValue('mfrequ%s' %mname, self.motorFrequency(None, mname))
            self.dp.updateFieldValue('mduty%s' %mname, self.motorDC(None, mname))
            self.dp.updateFieldValue('minv%s' %mname, self.motorInvert(None, mname))
            check=self.lastMotorPosition(mname)
            if not self.lastMotorPosition(mname) is None:
                if first:
                    self.dp.setFieldAtt('mposnl', 's', False)
                    self.dp.setFieldAtt('mrpml', 's', False)
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
                    self.dp.setFieldAtt('manall', 's', False)
                    staranal=True
            if not self.motorTargetSpeed(None, mname) is None:
                self.dp.setFieldAtt('mspeedl', 'h', False)
                self.dp.setFieldAtt('mspeed%s' % mname, 'h', False)
                speedfb, speedmb, speedmf, speedff=self.motorSpeedLimits(mname)
                self.dp.setFieldAtt('mrevsl', 's', False)
                self.dp.setFieldAtt('mfwdsl', 's', False)
                self.dp.setFieldAtt('mrevs%s' % mname, 'h', False)
                self.dp.setFieldAtt('mfwds%s' % mname, 'h', False)
                self.dp.updateFieldValue('mrevs%s' % mname, (speedfb, speedmb))
                self.dp.updateFieldValue('mfwds%s' % mname, (speedmf, speedff))
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
        self.fieldupdatelist=['mposn', 'mrpm', 'mduty', 'mfrequ']

    def tickloop(self, interval):
        self.nexttick = time.time()+interval
        self.running=True
        while self.running:
            wt=self.nexttick-time.time()
            k=self.keymon.get_data(max(0,wt))
            # do the motor tick first to minimise jitter
            for m in self.motors.values():
                m.ticker()
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
            if self.tickcount > 50:
                self.tickcount=0
                if 'clock' in self.dp.fields:
                    tm, ts=divmod(int(time.time()),60)
                    th, tm=divmod(tm,60)
                    self.dp.updateFieldValue('clock', (th % 24, tm, ts))
                for fn in self.fieldupdatelist:
                    if fn=='mposn':
                        ress=self.lastMotorPosition(None)  
                    elif fn=='mrpm':
                        ress=self.lastMotorRPM(None)
                    elif fn=='mduty':
                        ress=self.motorDC(None, None)
                    elif fn=='mfrequ':
                        ress=self.motorFrequency(None)
                        for k in ress:
                            if ress[k]==None:
                                ress[k]=0
                    if not ress is None:
                        self.dp.setFieldValues(fn, values=ress)
#            self.dp.setRefresh()
            self.dp.show()
            self.dp.releaseCursor()
        self.keymon.close()
        self.close()
        self.dp.close()

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

    def doMotorAction(self, value, motors):
#        print('doing', value, 'for', motors)
        if value == 'findMaxrpm':
            self._listcall(units=motors, method=value)
        elif value =='mapdcToRPM':
            if motors is None:
                frequ=self.dp.getFieldValue('mfrequ*')
                # TODO update all motors frequ fields to match
            else:
                frequ=self.dp.getFieldValue('mfrequ'+motors)
            self._listcall(units=motors, method=value, repeat=2, frequency=frequ, minDCfwd=20, minDCback=20, direction='both',
                        delay=.5, interval=2)
        elif value=='mapSpeed':
            self._listcall(units=motors, method=value, direction='forward', delay=4, interval=2.5)

if __name__ == '__main__':
    import argparse
    import importlib

    clparse = argparse.ArgumentParser(description="U3A RPi project motor driver.")
    clparse.add_argument('-t', '--tick', type=float, default=.05, help="tick period in seconds, typically .1 to .01 seconds")
    clparse.add_argument('config', help='configuration file to use')
    clparse.add_argument('-l', '--logfile', help="analyser log filename")
    args=clparse.parse_args()
    conf=importlib.import_module(args.config)

    m=tester(conf.motordef)
    if args.logfile:
        for mot in m.motors.values():
            mot.addLog('analyser', filename=args.logfile, asdict=0, append=0)
    m.tickloop(interval=args.tick)
