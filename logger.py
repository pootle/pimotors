#!/usr/bin/python3

import time, sys

class logger():
    """
    A base class for named objects where state changes can be logged, with easy control over what is and isn't logged
    log files are held as a universal list 
    """
    logfiles={}
    logheader='{M:02d}:{S:05.2f} {name:10s}: '
    lifelogso = ('life', {'filename': 'stdout', 'format': 'instance of {otype} {lifemsg}'})

    def __init__(self, name, logtypes=None, parent=None, createlogmsg=True, **kwargs):
        """
        prepares the object and opens log files as required.

        name        : a useful name for the object to put in log entries
        logtypes    : a list of 2-tuples, each with a logtype name and a dict of the settings to be used.
                         a logtype name can appear more than once and will be added to the list associated with that type
        parent      : allows hierarchies of objects
        createlogmsg: if True this constructor calls logCreate, otherwise not (and the inheriting class should call it)
        kwargs      : allows other keyword parameters to be ignored
        """
        self.name=name
        self.parent=parent
        self.logentries={}
        if not logtypes is None:
            for lte in logtypes:
                self.addLog(lte[0], **lte[1])
        if createlogmsg:
            self.logCreate()

    def addLog(self, ltype, **kwargs):
        fn=kwargs['filename']
        if fn.casefold()=='stdout' and not fn=='stdout':
            raise ValueError('stdout must be lower case')
        if not fn in logger.logfiles:
            if fn=='stdout':
                logger.logfiles[fn]=sys.stdout
            elif 'header' in kwargs:
                logger.logfiles[fn].write(kwargs['header'])
                logger.logfiles[fn].write('\n')
        if not ltype in self.logentries:
            self.logentries[ltype]=[kwargs]
        else:
            self.logentries[ltype].append(kwargs)

    def logCreate(self):
        self.log(ltype='life', otype=type(self).__name__, lifemsg='created') #'instance {otype} {lifemsg}'

    def logClose(self):
        self.log(ltype='life', otype=type(self).__name__, lifemsg='closed')

    def close(self):
        self.logClose()
        for lt,lv in self.logentries.items():
            for le in lv:
                fn=le['filename']
                if fn!='stdout' and fn in logger.logfiles:
                    logger.logfiles[fn].close()
                    del(logger.logfiles[fn])

    def log(self, **params):
        """
        adds a log entry for the given ltype as defined by the current objects' logentries 
        """
        ltype=params['ltype']
        if ltype in self.logentries:
            tm,ts=divmod(params.get('tstamp',time.time()),60)
            th,tm=divmod(tm,60)
            for le in self.logentries[ltype]:
                if not le['filename'] in logger.logfiles:
                    logf=open(le['filename'],'a' if 'append' in le else 'w')
                    logger.logfiles[le['filename']]=logf
                else:
                    logf=logger.logfiles[le['filename']]
                if 'format' in le:
                    logf.write((le['format'] if 'noheader' in le else logger.logheader+le['format']).format(
                            name=self.name,H=int(th), M=int(tm),S=ts, **params))
                elif 'asdict' in le:
                    logf.write(params.__repr__())
                else:
                    logf.write(logger.logheader.format(name=self.name,H=int(th), M=int(tm),S=ts)+'\n'.join(['%s: %s' % (k,v) for k,v in params.items()]))
                if le['filename']=='stdout':
                    logf.write('\033[K\n')
                else:
                    logf.write('\n')

    def odef(self):
        return {'name':self.name}

    def __repr__(self):
        return '%s(**%s)' % (type(self).__name__, str(self.odef()))

from importlib import import_module as modimporter

def makeClassInstance(className, **kwargs):
    """
    creates an instance of the class identified by the hierarchic name, with other parameters
    
    className:  The hierarchic name for the required class - e.g. 'modulename.classname'
    
    **kwargs : all the other arguments required by the constructor
    """
    components = className.split('.')
    assert len(components) > 1, "className %s is not of form <modname>.<classname>" % className
    try:
        mod = modimporter(components[0])
    except ImportError:
        print("FAILED to import module %s for className %s" % (str(components[0]), str(className)))
        raise
    for comp in components[1:]:
        try:
            mod = getattr(mod, comp)
        except AttributeError:
            print('FAILED to find %s in %s from className %s' % (str(comp), str(mod), str(className) ))
            raise
    try:
        return mod(**kwargs)
    except:
        print('FAILED constructor call on %s with parameters %s' % (str(mod), str(kwargs)))
        raise
