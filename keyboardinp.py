#!/usr/bin/python3

import termios, tty, sys, select, atexit
import queue, threading, time


class CheckConsole():
    def __init__(self):
        self.keyq = queue.Queue()
        self.running=True
        self.kthread=threading.Thread(target=self.keyreader, name='keyboardrdr')
        atexit.register(self.stop)
        self.kthread.start()

    def stop(self):
        self.running=False

    def keyreader(self):
        self.old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        while self.running:
            c=(sys.stdin.read(1))
            self.keyq.put(c)
        if not self.old_settings is None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
        self.old_settings=None
        print('keyboard handler done')

    def close(self):
        self.stop()
        self.kthread.join()

    def get_data(self,maxwait):
        try:
            nextchar=self.keyq.get(timeout=maxwait) 
        except queue.Empty:
            return None
        if ord(nextchar)==27:
            try:
                char2=None
                char3=None
                char2=self.keyq.get(timeout=.001)
                char3=self.keyq.get(timeout=.001)
            except queue.Empty:
                pass
            if char2 is None and char3 is None:
                return 'ESC'
            elif not char2 is None and not char3 is None:
                if char2 =='[':
                    if char3 in self.esclookups:
                        return self.esclookups[char3]
                    return 'ESC['+char3+ '('+str(ord(char3))+')'+str(ord('A'))
                else:
                    return 'WHAT!'+char2+char3
        elif ord(nextchar) < 32:
            return self.ccodelookup[nextchar] if nextchar in self.ccodelookup else nextchar
        return nextchar

    esclookups={'A':'UPARR', 'B':'DNARR', 'C':'RTARR', 'D':'LTARR', '3': 'DEL', 'Z':'BACKTAB'}
    ccodelookup={'\t':'TAB'}

if __name__ == '__main__':
    last=None
    c=CheckConsole()
    print('running')
    try:
        while last != 'x':
            last=c.get_data(.1)
            if last!= None:
                print('====>', last)
                if last=='x':
                    c.stop()
    except KeyboardInterrupt:
        pass
    c.close()
