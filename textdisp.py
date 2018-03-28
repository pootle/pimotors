#!/usr/bin/python3

import shutil
import curses
debug=False
gotoyx='\033[{};{}H'
clearline='\033[K'
reset='\033[0m'
graphicmode='\033[{}m'

"""
each named entry in the style map has 3 possible components:
    bgcol: the background colour - any of the standard background colour strings can be used '30' - '37', '38;5;n' etc
    fgcol: The foreground colour - any of the standard foreground colour strings can be used '40' - '47', '48;5;n' etc
    atts : a string with 0 or more characters used additively; these are combined with the same flags in the field's atts
            to yield the actual attributes used to draw the screen 
            'b' : bold
            'i' : italic
            'r' : swap fg / bg
            's' : strikethough
            't' : 'tab'able - can be an active field (if not hidden)
            'u' : underline
"""
fieldstylemap={
    'background': {'bg': ';43' , 'fg': ';39'},
    'hidden'    : {'bg': ';43' , 'fg': ';33'},
    'label'     : {'bg': ';102', 'fg': ';30'},
    'output'    : {'bg': ';47' , 'fg': ';30'},
    'activeinp' : {'bg': ';40' , 'fg': ';37;1'},
    'nonactinp' : {'bg': ';43' , 'fg': ';33'},
}

"""
defines how to turn the various attributes on and off. turn off can be '0', if there is no way to explicitly turn off the single component 
"""
attsmap={
    'b': (';1', ';21'),
    'u': (';4', ';24'),
    'r': (';7', ';27'),
    's': (';9', ';29'),
    'i': (';3', ';23'),
    'h': (''  , ''),  # field is hidden
}

def setbgfgmods(dstate, style, atts=''):
    """
    checks the current state of background, foreground and mods, and adjusts if appropriate - updating dstate as necessary
    """
    amode=[]
    sons=''
    soffs=''
    dex=''
    if atts != dstate['atts']:
        reset=False
        for sc, sv in attsmap.items():
            if (sc in atts) != (sc in dstate['atts']):
                if debug:
                    print('att doing >%s< needs change' % sc)  
                if sc in atts:
                    sons += sv[0]
                elif sv[1]=='0':
                    reset=True
                else:
                    soffs+=sv[1]
        if reset:
            sons=';0'
            soffs=''
            for sc in atts:
                sons += attsmap[sc][0]
            dstate['fgcol']=None
            dstate['bgcol']=None
        if debug:
            dex='atts >%s< yields >%s<|>%s<' % (atts, sons, soffs)
        dstate['atts']=atts
    if dstate['fg'] != style['fg']:
        sons += style['fg']
        dstate['fg']=style['fg']
    if dstate['bg'] != style['bg']:
        sons += style['bg']
        dstate['bg']=style['bg']
    if soffs != '':
        sall=soffs[1:]+sons
    elif sons != '':
        sall=sons[1:]
    else:
        sall=None
    if debug:
        if sall is None:
            return 'no change' + dex + ' from >' + atts + '<'
        else:
            return '>%s<' % sall + dex + ' from >' + atts + '<'
    elif sall is None:
        return ''
    else:
        return graphicmode.format(sall, end='')

def setpos(dstate, ypos, xpos):
    if ypos != dstate['cursory'] or xpos != dstate['cursorx']:
        dstate['cursory']=ypos
        dstate['cursorx']=xpos
        if debug:
#            print('-- cursor to line %3d, col %3d' % (dstate['topline']+ypos, xpos))
            pass
        else:
            print(gotoyx.format(dstate['topline']+ypos,xpos+1),end='')

class dispfield():
    def __init__(self, name, parent, lineno, colno, format, fmode=None, style=None, atts='', value=None):
        """
        name  : hashable object (typically string) used to get the field for update etc.
        
        parent: the container for this object
        
        lineno: lineno for the field, there can be blank lines which are automatically setup. a +ve integer TODO or hashable object that is the name of
                    another field to get the value from
        
        colno : column number for the field. a +ve integer TODO or a hashable object that is the name of another field to get the value from
        
        format: a python format string  used to generate the text for this field. Use this to force consistent field widths. None means value is simple text
        
        fmode : if none value is treated as a simple argument to format, if '*' value is treated as *args, if '**' value is treated as kwargs

        value : the initial value for the field
                
#        bg    : the background value for displaying the field
#        fg    : the foreground value for displaying the field
#        mods  : font effects to use on this field - string with either a single value (e.g. '4' for underline) or multiple values (e.g. '5;1' for slow blink bold

        style  : there is a list of style names to set the fields visual appearance. Each maps to a set of attributes - typically
                     foreground and background, but can include others such as bold.

        atts  : a set of boolean flags - see fieldstates that modify the style
        
        """
        self.name=name
        self.parent=parent
        self.lno=lineno
        self.colno=colno
        self.value=value
        self.format=format
        self.fmode=fmode
        self.changed=True
        self.style=style
        self.atts=atts

    def setValue(self,fvalue):
        if self.value==fvalue:
            return False
        else:
            self.value=fvalue
            self.changed=True
            return True

    def setAtt(self, schar, on):
        assert schar in attsmap.keys()
        if (schar in self.atts)==on:
            return False
        if on:
            self.atts+=schar
        else:
            self.atts=self.atts.replace(schar,'')
        self.changed=True
        if debug:
            print('field', self.name, 'att', schar, 'is', on, 'atts now', self.atts)
        return True

    def showif(self, dstate):
        if self.changed:
            setpos(dstate,ypos=self.lno, xpos=self.colno)
            self.show(dstate)

    def getDisplayValue(self):
        return self.value

    def show(self, dstate):
        assert dstate['cursory']==self.lno and dstate['cursorx']==self.colno
        dval=self.getDisplayValue()
        if self.format is None:
            dstr=self.value
        elif self.fmode is None:
            try:
                dstr=self.format.format(dval)
            except TypeError:
                print('TypeError formating >%s< in field %s with value %s' % (str(self.format), self.name, str(dval)))
                raise
            except ValueError:
                print('ValueError formating >%s< in field %s with value %s' % (str(self.format), self.name, str(dval)))
                raise
        elif self.fmode == '*':
            dstr=self.format.format(*dval)
        elif self.fmode == '**':
            dstr=self.format.format(**dval)
        modmods =''
        if 'h' in self.atts:
            styleset=fieldstylemap['hidden']
        else:
            styleset=fieldstylemap[self.style] 
            styleatts=styleset.get('atts','')
            assert not styleatts is None
            assert not self.atts is None
            for sc in attsmap.keys():
                if sc=='r':
                    if (sc in self.atts) != (sc in styleatts):
                        modmods+=sc
                elif (sc in self.atts) or (sc in styleatts):
                    modmods+= sc
        mtext=setbgfgmods(dstate, style=styleset, atts=modmods)
        if debug:
            print('field %12s, mods: %20s, string length %3d: %s' % (self.name, mtext, len(dstr), dstr))
        else:
            print(mtext, dstr, sep='', end='')
        dstate['cursorx'] += len(dstr)
        self.changed=False

class inpfield(dispfield):
    """
    The basics for a field that supports used input / amendment - the extra params allow parameterised callbacks invoked when the
    value of the field changes 
    
    valuecallback : a function to call whenever the user changes the value
    
    cbparams      : dict of additional keyword args added to the callback.
    
    returncallback: a function to call when the hits return while the field is active. This can be used instead of OR as well as 
                    the valuecallback function
    
    """
    def __init__(self, valuecallback=None, cbparams=None, returncallback=None, **kwargs):
        super().__init__(**kwargs)
        self.vcb=valuecallback
        self.vcbp=cbparams
        self.retcb=returncallback

    def enter(self):
        self.setAtt('r', True)
        self.cursorpos=0
        return True

    def leave(self):
        self.setAtt('r', False)
        return True
    
class selector(inpfield):
    """
    a user amendable field that cycles through a fixed set of values. Each entry is a 2 -tuple, the first is the value of the field (the internal
    representation), the second is the display value that is used as basis for the text displayed
    """
    def __init__(self, selectmap, **kwargs):
        super().__init__(**kwargs)
        self.selectvals=[mapentry[0] for mapentry in selectmap]
        self.displayvals=[mapentry[1] for mapentry in selectmap]

    def getDisplayValue(self):
        try:
            ix = self.selectvals.index(self.value)
        except ValueError:
            raise ValueError('%s is not in the selectmap for field %s' % (str(self.value), str(self.name)))
        return self.displayvals[ix]            

    def offerkey(self, key):
        if key in ('UPARR', 'DNARR'):
            ix=self.selectvals.index(self.value)
            if key=='UPARR':
                ix += 1
            elif key=='DNARR':
                ix -= 1
            ix = ix % len(self.selectvals)
            if self.vcb is None:
                return True, self.setValue(self.selectvals[ix])
            else:
                goodval=self.vcb(value=self.selectvals[ix], **self.vcbp)
                return True, self.setValue(goodval)
            return True, False
        elif key=='RETURN':
            if callable(self.retcb) and self.value!='none':
                self.retcb(value=self.value, **self.vcbp)
        return True, False

class editfield(dispfield):
    def enter(self):
        """
        called when this field becomes the active field
        """
        self.setAtt('r', True)
        self.cursorpos=0
        return True

    def leave(self):
        """
        called when ceases being the active field
        """
        self.setAtt('r', False)
        return True

    def offerkey(self, key):
        if key=='LTARR':
            self.cursorpos -= 1
            if self.cursorpos < 0:
                self.cursorpos=0
        elif key=='RTARR':
            self.cursorpos += 1
            if self.cursorpos > len(self.value):
                self.cursorpos=len(self.value)
        elif key=='\x7f':
            if self.cursorpos>0:
                self.value=self.value[:self.cursorpos-1]+self.value[self.cursorpos:]
                self.cursorpos-=1
                if self.cursorpos < 0:
                   self.cursorpos=0
        elif key=='DEL':
            if self.cursorpos < len(self.value):
                self.value=self.value[:self.cursorpos]+self.value[self.cursorpos+1:]
        elif len(key)==1:
            if ord(key) >31:
                oldval=self.value
                if self.cursorpos <=0:
                    self.value=key+oldval
                    self.cursorpos=1
                elif self.cursorpos >= len(oldval):
                    self.value=oldval+key
                    self.cursorpos=len(oldval)+1
                else:
                    cpos=self.cursorpos
                    self.value=oldval[:cpos]+key+oldval[cpos:]
                    self.cursorpos+=1
        return True, True

def makefield(fclass, **kwargs):
    try:
        return fclass(**kwargs) 
    except TypeError:
        print('')
        print('')
        print('failure to make field using params:')
        print(kwargs)
        print('on a %s' %fclass.__name__)
        raise

class display():
    def __init__(self, fieldefs, colnames, setdebug=None):
        global debug
        if not setdebug is None:
            debug=setdebug
        self.colnames=colnames
        curses.setupterm()
        self.numcolours = curses.tigetnum("colors")
        self.pendfields=[]
        self.fields={}
        for f  in fieldefs:
            self.addfield(f)
#        linebuild=sorted([makefield(parent=self, **f) for f in fieldefs],key=lambda x: x.lno)
        maxline=max([f.lno for f in self.pendfields])
        self.lines=[[] for i in range(maxline+1)]
#        self.fields={f.name:f for f in linebuild}
        self.bgstyle=fieldstylemap['background']
#        self.pendfields=linebuild
        self.lineschanged=[[True, True] for l in self.lines]

    def close(self):
        ssize=shutil.get_terminal_size()
        print(gotoyx.format(ssize.lines,0),flush=True, end='')

    def addfield(self, fielddef):
        assert not fielddef['name'] in self.fields
        fd=fielddef.copy()
        if isinstance(fd['lineno'],str):
            ln=fd['lineno']
            assert ln[0] == '='
            if ln[0]=='=':
                rf=self.fields[ln[1:]]
                fd['lineno']=rf.lno
        f=makefield(parent=self, **fd)
        self.pendfields.append(f)
        self.fields[f.name]=f

    def redolayout(self):
        changedlines=[]
        for pf in self.pendfields:
            while pf.lno >= len(self.lines):
                self.lines.append([])
            self.lines[pf.lno].append(pf)
            if not pf.lno in changedlines:
                changedlines.append(pf.lno)
        self.pendfields=[]
        for lno in changedlines:
            self.lines[lno].sort(key=lambda f: f.colno)
        self.lineschanged=[[True, True] for l in self.lines]
        self.inpfield=None
        self.tabsequ=None
        self.activefield=None
        tabbyfields=[]
        for l in self.lines:
            for f in l:
                if 't' in f.atts:
                    tabbyfields.append(f)
        if len(tabbyfields) > 0:
            tabbyfields.sort(key=lambda x: x.lno)
            tabbyfields.sort(key=lambda x: x.colno)
            self.tabsequ=[f.name for f in tabbyfields]            

    def updateFieldValue(self, fname, fvalue):
        """
        updates the named field's value ( by calling its setValue method), sets the linechanged flag if appropriate so update screen
        the next time show is called
        """
        assert fname in self.fields
        f=self.fields[fname]
        if f.setValue(fvalue): #True if display needs updating
            self.lineschanged[f.lno][1]=True

    def setFieldValues(self, root, values=None, onevalue=None):
        """
        Updates a row of field values.
        
        root    : the root of the field name, if values is present, then the keys from values are appended to this to identify each field, otherwise
                  the onevalue is applied using all the entries in self.motnames
        values  : a dict with keys for the columns to be updated and values to be applied to each, if None, the onevalue is used.
        
        onevalue: if values is None then onevalue is the values applied to the columns identified in self.motnames
        """
        collist=self.colnames if values is None else values.keys()
        for cname in collist:
            fname=root+cname
            fval=onevalue if values is None else values[cname]
            if not fval is None:
                self.updateFieldValue(fname, fval)

    def getFieldValue(self, root, keys=None):
        """
        fetches the value(s) of 1 or more fields,
        
        if keys is None:
            returns the value of the field with name in root.
        else:
            keys is a list of strings.
            a dict is returned with keys from the keys argument and values from the fields with names from root + each key in turn
        """
        if keys is None:
            assert root in self.fields
            return self.fields[root].value
        else:
            return {k:self.fields[root+k].value for k in keys}

    def setFieldAtt(self, fname, schar, avalue):
        """
        updates 1 attribute of the named field (by calling its setAtt method), sets the linechanged flag if appropriate so update screen
        the next time show is called
        """
        assert fname in self.fields, 'did not find field %s in fieldlist' % fname
        f=self.fields[fname]
        if f.setAtt(schar, avalue):
            self.lineschanged[f.lno][1]=True

    def setHotkeyActs(self, macts):
        """
        sets the list of 'hot' keys and the functions to call that are used when no individual field has focus.
        """
        self.hotkeys=macts

    def setRefresh(self):
        """
        call if other things may have messed with the screen - forces full repaint
        """
        for lc in self.lineschanged:
            lc[0]=True

    def releaseCursor(self):
        print(gotoyx.format(0,1),end='')

    def show(self):
        if len(self.pendfields) >0:
            self.redolayout()
        ssize=shutil.get_terminal_size()
        dstate={'topline': ssize.lines-len(self.lines), 'cursory':None, 'cursorx': None, 'fg': None, 'bg':None, 'atts': ''}
        for lno, l in enumerate(self.lines):
            if self.lineschanged[lno][0]:
                self.lineschanged[lno][0]=False
                self.lineschanged[lno][1]=False
                setpos(dstate,ypos=lno, xpos=0)
                mtext= setbgfgmods(dstate, style=self.bgstyle)
                if debug:
                    print('display sets mods', mtext)
                else:
                    print(mtext, end='')
                for f in l:
                    assert f.lno==lno
                    if f.colno != dstate['cursorx']:
                        spcount=f.colno - dstate['cursorx']
                        assert spcount>0, 'space count %d for field %s' % (spcount, f.name)
                        if debug:
                            print('-- spaces(%3d)' % spcount)
                        else:
                            print(' '*spcount,end='')
                        dstate['cursorx']+=spcount
                    f.show(dstate)
                    mtext=setbgfgmods(dstate, style=self.bgstyle)
                    if debug:
                        print('display sets mods', mtext)
                    else:
                        print(mtext, end='')
                if debug:
                    print('-- clear to end of line')
                else:
                    print(clearline, end='')
            elif self.lineschanged[lno][1]:
                self.lineschanged[lno][1]=False
                for f in l:
                    f.showif(dstate)
        print(reset, end='')
        if self.activefield is None:
            print(gotoyx.format(ssize.lines,0),flush=True, end='')
        else:
            f=self.fields[self.tabsequ[self.activefield]]
            setpos(dstate,ypos=f.lno, xpos=f.colno+f.cursorpos)
            print('', end='', flush=True)

    def enterField(self, fname):
        f=self.fields[fname]
        if f.enter():
            self.lineschanged[f.lno][1]=True

    def leaveField(self, fname):
        f=self.fields[fname]
        if f.leave():
            self.lineschanged[f.lno][1]=True

    def offerkey(self, key):
        """
        called whenever a keystroke is detected - return True if consumed, else False
        """
        # first check for inter field navigation
        if key in ('TAB', 'BACKTAB', 'ESC') and not self.tabsequ is None:
            if not self.activefield is None:
                self.leaveField(self.tabsequ[self.activefield])
            if key=='ESC':
                self.activefield=None
            else:
                if key=='TAB':
                    if self.activefield is None or self.activefield==len(self.tabsequ)-1:
                        self.activefield=0
                    else:
                        self.activefield+=1
                    mv=1
                else:
                    if self.activefield is None or self.activefield == 0:
                        self.activefield=len(self.tabsequ)-1
                    else:
                        self.activefield-=1
                    mv=-1
                zerohits=0
                while 'h' in self.fields[self.tabsequ[self.activefield]].atts and zerohits<2:
                    if self.activefield==0:
                        zerohits+=1
                    self.activefield+=mv
                    if self.activefield < 0:
                        self.activefield=len(self.tabsequ)-1
                    elif self.activefield >= len(self.tabsequ):
                        self.activefield = 0
                if zerohits < 2:
                    self.enterField(self.tabsequ[self.activefield])
                    if debug:
                        print('-- field', self.fields[self.tabsequ[self.activefield]].name,'set active')
                else:
                    self.activefield=None
            return True
        if self.activefield is None:
            if key in self.hotkeys:
                self.hotkeys[key]()
                return True
        else:
            activn=self.tabsequ[self.activefield]
            activf=self.fields[activn]
            if hasattr(activf,'offerkey'):
                consumed, changed = activf.offerkey(key)
                if changed:
                    self.lineschanged[activf.lno][1]=True
                return consumed
        return False

        if self.inpfield is None:
            if key in self.hotkeys:
                self.hotkeys[key]()
                return True
            return False
        msg=None
        if key =='\n':
            efield=self.inpfield
            self.inpfield=None
            cb=efield.editdone
            del(efield.cursorpos)
            del(efield.editdone)
            if callable(cb):
                cb(efield.name, efield.value)
            return True
        elif key=='LTARR':
            self.inpfield.cursorpos -= 1
            if self.inpfield.cursorpos < 0:
                self.inpfield.cursorpos=0
        elif key=='RTARR':
            self.inpfield.cursorpos += 1
            if self.inpfield.cursorpos > len(self.inpfield.value):
                self.inpfield.cursorpos=len(self.inpfield.value)
        elif key=='\x7f':
            if self.inpfield.cursorpos>0:
                self.updateFieldValue(self.inpfield.name, self.inpfield.value[:self.inpfield.cursorpos-1]+self.inpfield.value[self.inpfield.cursorpos:])
                self.inpfield.cursorpos-=1
                if self.inpfield.cursorpos < 0:
                   self.inpfield.cursorpos=0
        elif key=='DEL':
            if self.inpfield.cursorpos < len(self.inpfield.value):
                self.updateFieldValue(self.inpfield.name, self.inpfield.value[:self.inpfield.cursorpos]+self.inpfield.value[self.inpfield.cursorpos+1:])
        elif len(key)==1:
            if ord(key) >31:
                oldval=self.inpfield.value
                if self.inpfield.cursorpos <=0:
                    self.updateFieldValue(self.inpfield.name, key+oldval)
                    self.inpfield.cursorpos=1
                elif self.inpfield.cursorpos >= len(oldval):
                    self.updateFieldValue(self.inpfield.name, oldval+key)
                    self.inpfield.cursorpos=len(oldval)+1
                else:
                    cpos=self.inpfield.cursorpos
                    self.updateFieldValue(self.inpfield.name, oldval[:cpos]+key+oldval[cpos:])
                    self.inpfield.cursorpos+=1
        else:
            msg='last key #%s#  ' % (":".join("{:02x}".format(ord(c)) for c in key))
        if not msg is None:
            self.updateFieldValue('hdr', msg)
        return True

    def editfield(self, fieldname, initialval, oncomplete):
        """
        setup named field as an input field that allows basic editing
        """
        assert self.inpfield is None and fieldname in self.fields
        self.inpfield=self.fields[fieldname]
        self.inpfield.format='{:<45s}'
        self.inpfield.value=initialval
        self.inpfield.changed=True
        self.lineschanged[self.inpfield.lno][1]=True
        self.inpfield.cursorpos=len(initialval)
        self.inpfield.editdone=oncomplete
