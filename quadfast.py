#!/usr/bin/python3

import time
import subprocess, sys, os, mmap, ctypes, struct

class quadshared(ctypes.Structure):
     _fields_ = [
        ("state",      ctypes.c_int),
        ("qcount",     ctypes.c_int),
        ("quadsApos",  ctypes.c_int),
        ("quadsAskip", ctypes.c_uint),
        ("quadsBpos",  ctypes.c_int),
        ("quadsBskip", ctypes.c_uint),
    ]

class quadfastwrapper():
    """
    A class that tracks rotary quad encoders using a fast C program in a separate processs which maintains a position in ticks from the quadencoder.
    
    The C program and this class communicate using a memory mapped file.
    
    The C program and this class are instantiated once for a set of motors (requires less cpu) 
    """
    def __init__ (self, filename, motorquads, loglvl):
        """
        filename   : name for the file to use as basis for memory mapped communication.
        
        motorquads : a dict with keys as the names of the motors, the values are 2 entry lists with the 2 pins to use.
        
        loglvl     : the log level to use for the C program.
        """
        self.mmfiled = os.open(filename, os.O_CREAT | os.O_TRUNC | os.O_RDWR)
        os.write(self.mmfiled, b'\x00' * ctypes.sizeof(quadshared))
        self.sharedbuf = mmap.mmap(self.mmfiled, ctypes.sizeof(quadshared), mmap.MAP_SHARED, mmap.PROT_WRITE)
        self.quadinfo = quadshared.from_buffer(self.sharedbuf)
        pargs=['./quadfeedback','-f%s'%filename,'-l%d'%loglvl]
        qent=0
        self.nmap={}
        for k,v in motorquads.items():
            for p in v:
                pargs.append('-n%d'%p)
            self.nmap[k]=qent
            qent += 1
        print(pargs)
        self.encproc=subprocess.Popen(args=pargs, stdout=sys.stdout, stderr=sys.stderr)

    def quadpos(self, mname):
        ent=self.nmap.get(mname, None)
        if ent is None:
            return None
        if ent==0:
            return self.quadinfo.quadsApos
        else:
            return self.quadinfo.quadsBpos

    def close(self):
        self.quadinfo.runstate=1
        print("closedown requested")
        if not self.encproc is None:
            try:
                self.encproc.wait(1)
            except subprocess.TimeoutExpired:
                print("failed to stop - forcing termination")
                self.encproc.terminate()
            self.quadinfo=None
        self.sharedbuf.close()
        os.close(self.mmfiled)
