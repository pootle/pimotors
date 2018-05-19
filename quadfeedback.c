// A c module to interface to the pigpio daemon that sets up and monitors pairs of gpio pins connected to a quad
// rotary encoder. It hooks up a callback that is triggered by pigpio, and maintains the position of the motor
// in quad counts to keep it as simple as possible. (i.e. if the encoder gives 3 pulses per rev and we use both
// pins the integer position will be 1/6th of a revolution.
//
// if the position goes the *wrong* way just swap the order the pins are declared.
//
// gcc -Wall -pthread -o quadfeedback quadfedback.c -lpigpiod_if2 -lrt
//
#include <pigpiod_if2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

int logit=9; // 
int pint=-1; // this is the access key to pigpio used in *nearly* all calls

struct encinfo { // this is the internal structure used to represent each encoder.
    int encOK;
    unsigned pinA;
    unsigned pinB;
    unsigned pinAup;
    unsigned pinBup;
    int pinAcbid;
    int pinBcbid;
    int lastquad;
    int quadno;     // index into sharedquads.quads for this encoder.
};

struct quadstate {  // and this is the structure we stick into the mmapped file for each encoder so e can pick it up from the python
                    // motor controller
    int pos;            // current motor position
    unsigned skipcount; // number of dodgy readings we've found - i.e. where we've skipped 2 quadrants.
};

struct sharedquads{ // and this is the total structure of the shared data
    int state;      // 0 for running, initially set in this process
                    // 1 for stop requested from the controller side, 
                    // 2 to reset the pos to zero requested from controller side (pref with the motor stopped!)
                    // -1 when this process has exited, set in this process.
    int qcount;     // number of quads active
    struct quadstate quads[3]; // 3 should be more than enough for usual uses.
};

struct sharedquads* qshared=NULL; // this will point to the mmapped file we use to communicate with the motor controller

// The quad position is a number in range 0..3 representing the 2 quad sensors. This table provides 4 groups of 4 entries that translate
// the current quad position and the last quad position into a change:
// 0 means no change, 1 means forward 1 quad, and -1 means back 1 quad. 99 means we've moved 2 quads and we can't directly infer direction
// fwds gives sequence 1,3,2,0... backwards gives sequence 1,0,2,3...
int quadlookup[16] = {
    0,  1, -1, 99,
   -1,  0, 99,  1,
    1, 99,  0, -1,
   99, -1,  1,  0
};

int setuppin(unsigned gppin, unsigned pullupmode) {
    if ((gppin<0) | (gppin>31)) {
        if ((logit & 1) != 0) {
            printf("setuppin: invalid pin no %d\n", gppin);
        }
        return -1;
    }
    int res = set_mode(pint, gppin, PI_INPUT);
    if (res==0) {
        if ((logit & 1) != 0) {
            printf("setuppin has set mode for pin%d\n", gppin);
        }
        return gppin;
    } else {
        if ((logit & 1) != 0) {
            printf("setuppin FAILED to set mode for pin %d because %d\n", gppin, res);
        }
        return -1;
    }
}

static void changefound(int pi, unsigned pinno, unsigned edgetype, uint32_t tick, void* data) {
    struct encinfo* enc = data;
    if (edgetype != PI_TIMEOUT) {
        if (pinno == enc->pinA) {
            enc->pinAup = edgetype;
        } else {
            enc->pinBup = edgetype;
        }
        int newquad=enc->pinAup << 1 | enc->pinBup;
        int qchange = quadlookup[enc->lastquad <<2 | newquad];
        if ((logit & 4) != 0) {
            printf("changefound reports qchange %d from newquad %d, oldquad %d in #%d.\n", qchange, newquad, enc->lastquad, enc->quadno);
        }
        if (qchange > 10) {
            qshared->quads[enc->quadno].skipcount+=1;
        } else {
            qshared->quads[enc->quadno].pos+=qchange;
            if ((logit & 4) != 0) {
                printf("changefound position now %d\n", qshared->quads[enc->quadno].pos);
            }
        }
        enc->lastquad=newquad;
    }
}

int setupenc(struct encinfo* enc, unsigned gppinA, unsigned gppinB, unsigned pudA, unsigned pudB, int qindex) {
    if (pint >=0) {
        if (enc->encOK==-1) {
            enc->encOK=-1;
//            enc->pos=0;
            enc->pinA=setuppin(gppinA, pudA);
            enc->pinB=setuppin(gppinB, pudB);
//            enc->skipcount=0;
            enc->quadno=qindex;
            qshared->quads[qindex].skipcount=0;
            qshared->quads[qindex].pos=0;
            if ((enc->pinA>=0) | (enc->pinB >=0)) {
                enc->encOK=0;
                if (enc->pinA > 0) {
                    enc->pinAup = (gpio_read(pint, enc->pinA));
                    enc->lastquad = enc->pinAup << 1;
                    enc->pinAcbid = callback_ex(pint, enc->pinA, EITHER_EDGE, changefound, enc);
                    enc->encOK+=1;
                } else {
                    enc->pinAcbid = -1;
                }
                if (enc->pinB > 0) {
                    enc->pinBup = gpio_read(pint, enc->pinB);
                    enc->lastquad += enc->pinBup;
                    enc->pinBcbid = callback_ex(pint, enc->pinB, EITHER_EDGE, changefound, enc);
                    enc->encOK +=1;
                } else {
                    enc->pinBcbid = -1;
                }
                if (enc->encOK==2) {
                    if ((logit & 1) != 0) {
                        printf("encoder setup with 2 pins callback on pins %d, %d, with current quad pos %d\n", enc->pinA, enc->pinB, enc->lastquad);
                    }
                    return 0;
                } else {
                    if ((logit & 1) != 0) {
                        printf("encode code only functions with 2 callback pins, there are %d setup\n", enc->encOK);
                    }
                    return -1;
                }
            } else {
                if ((logit & 1) != 0) {
                    printf("setupenc setup found no valid pins %d, %d\n", gppinA, gppinB);
                }
                return -1;
            }
        } else {
            if ((logit & 1) != 0) {
                printf("setupenc failed - already setup\n");
            }
            return -1;
        }
    } else {
        if ((logit & 1) != 0) {
            printf("unable to setup encoder - pigpio not setup\n");
        }
        return -1;      
    }
}

int shutdownenc(struct encinfo* enc) {
    if (pint >= 0) {
        if (enc->pinA >= 0) {
            if (enc->pinAcbid >= 0) {
                int res = callback_cancel(enc->pinAcbid);
                if ((logit & 1) != 0) {
                    printf("shutdownenc callback canceled for pin %d, result %d\n", enc->pinA, res);
                }
            }
            set_pull_up_down(pint, enc->pinA, PI_PUD_OFF);
            if ((logit & 1) != 0) {
                printf("shutdownenc shutdown pin %d\n", enc->pinA);
            }
        }
        if (enc->pinB >= 0) {
            if (enc->pinBcbid >= 0) {
                int res = callback_cancel(enc->pinBcbid);
                if ((logit & 1) != 0) {
                    printf("shutdownenc callback canceled for pin %d, result %d\n", enc->pinB, res);
                }
            }
            set_pull_up_down(pint, enc->pinB, PI_PUD_OFF);
            if ((logit & 1) != 0) {
                printf("shutdownenc shutdown pin %d\n", enc->pinB);
            }
        }
        enc->encOK=-1;
        return 0;
    } else {
        if ((logit & 1) != 0) {
            printf("unable to shutdown encoder - pigpio not setup\n");
        }
        return -1; 
    }
}

int setup() {
    if (pint >= 0) {
        if ((logit & 1) != 0) {
            printf("setup called when already setup\n");
        }
        return -1;
    }
    pint=pigpio_start(NULL, NULL);
    if (pint < 0) {
        if ((logit & 1) != 0) {
            printf("setup failed - pigpio_ start returned %d\n", pint);
        } 
        return -1;
    } else {
        if ((logit & 1) != 0) {
            printf("setup successfull\n");
        }
        return 0;   
    }
}

int shutdown() {
    if (pint >= 0) {
        
        pigpio_stop(pint);
        if ((logit & 1) != 0) {
            printf("shutdown successfull\n");
        }
        return 0;
    } else {
        if ((logit & 1) != 0) {
            printf("shutdown aborted - pigpio not active\n");
        }
        return -1;
    }
}

void printhelp(char* aname) {
    printf("help for %s\n\n", aname);
    printf("-h --help: show this help and exit\n"
           "-f --filename: name of the file to share data\n"
           "-l           : log level to report to stdout (via printf)\n"
           "-n           : gpio pin with no pullup or pulldown set\n"
           "-u           : gpio pin with pullup set\n"
           "-d           : gpio pin with puldown set\n"
           "\n"
           "There must be an even number of pins and each pair are assumed to be for 1 rotary encoder\n"
           "\n"
           "Example: %s -f/tmp/quads -n7 -n11, -u17, -u27\n"
           "\n",aname);
}

unsigned strtounsigned(char* sstr, unsigned max) {
    char *ptr;
    long ret;
    ret = strtoul(sstr, &ptr, 10);
    if (ret>=max) {
        return max;
    } else {
        return (unsigned)ret;
    }
}

int main(int argc, char* argv[]) {
    unsigned pins[argc];
    unsigned puds[argc];
    unsigned pincount=0;
    char* filename=NULL;
    for (int count = 1; count < argc; count++) {
        printf("arg %d:%s\n", count, argv[count]);
        if ((strncmp(argv[count],"-h", 2) ==0) | (strncmp(argv[count], "--help",6)==0)) {
	        printhelp(argv[0]);
	        exit(0);
	    } else if ((strncmp(argv[count],"-f", 2) ==0) | (strncmp(argv[count], "--filename",10)==0)) {
	        if (strncmp(argv[count],"-f", 2) ==0) {
	            filename=argv[count]+2;
	        } else {
	            filename=argv[count]+10;
	        }
	    } else if ((strncmp(argv[count],"-u", 2) == 0) | (strncmp(argv[count],"-n", 2) == 0) | (strncmp(argv[count],"-d", 2)==0) ){
	        pins[pincount]=strtounsigned(argv[count]+2, 32);
	        printf("count %d: %d\n", pincount, pins[pincount]);
	        if (pins[pincount]==32) {
	            printf("argument %s is not in range 0..31", argv[count]);
	            exit(-1);
	        }
	        if (strncmp(argv[count],"-u", 2) == 0) {
    	        puds[pincount]=PI_PUD_UP;
    	    } else if (strncmp(argv[count],"-n", 2) == 0) {
    	        puds[pincount]=PI_PUD_OFF;
    	    } else {
    	        puds[pincount]=PI_PUD_DOWN;
    	    }
    	    pincount += 1;
    	} else if (strncmp(argv[count],"-l", 2) == 0) {
    	    logit=strtounsigned(argv[count]+2, 64);
	    } else {
	        printf("unknown option %s in parameters\n\n", argv[count]);
	        printhelp(argv[0]);
	        if (qshared != NULL) {
    	        qshared->state=-1;
    	    }
	        exit(-1);
	    }
    }
    if (filename==NULL) {
        printf("no shared file specified\n\n");
        exit(0);
    }
    printf("do file %s\n", filename);
	int mfiled = open(filename, O_RDWR | O_CREAT, (mode_t)0600);
    if ( mfiled == -1 ) {
        printf( "Could not open file %s\n", filename );
        exit(EXIT_FAILURE);
    }
    struct stat checkstat;
    fstat(mfiled, &checkstat);
    int mmsize=sizeof(struct sharedquads);
    if (checkstat.st_size<=mmsize) {
        printf("initialise file...\n");
        char* junk=malloc(mmsize+1);
        write(mfiled, junk, mmsize+1);
        free(junk);
    }
    qshared = mmap(NULL, mmsize, PROT_READ | PROT_WRITE, MAP_SHARED, mfiled, 0);
    printf("mmap setup\n");
    qshared->state = 0;
    printf("state set to 0\n");

    printf("param setup done\n");
    if (pincount < 2) {
        printf("not enough pins for a quad encoder defined\n\n");
        printhelp(argv[0]);
        qshared->state=-1;
        exit(-1);
    }
    if ((pincount & 1) ==1) {
        printf("There should be an even number of pins!\n\n");
        printhelp(argv[0]);
        qshared->state=-1;
        exit(-1);
    }
    if (setup() != 0) {
        qshared->state=-1;
        exit(-1);
    }
    qshared->qcount=pincount >>1;
    struct encinfo* enclist = (struct encinfo*) malloc(sizeof(struct encinfo) * qshared->qcount);
    for (int count=0; count < pincount; count += 2) {
        enclist[count>>1].encOK=-1;
        int x = setupenc(&enclist[count>>1], pins[count], pins[count+1], puds[count], puds[count+1], count>>1);
        if (x!=0) {
            shutdown();
            qshared->state=-1;
            exit(-1);
        }
    }
    struct timespec sleept;
    sleept.tv_sec=0;
    sleept.tv_nsec=500000000; // run this on .5 second ticker.
    while (qshared->state >= 0) {
        nanosleep(&sleept, NULL);
        if (qshared->state==1) {
            qshared->state=-1;
        } else if (qshared->state==2) {
            for (int count=0; count < qshared->qcount; count++) {
                qshared->quads[count].pos=0;
                qshared->quads[count].skipcount=0;
            }
            qshared->state=0;
        }
        if ((logit & 8) != 0) {
            for (int count=0; count < qshared->qcount; count++) {
                printf("quad(%d) now at %4d. skipcount is %2d    ", count, qshared->quads[count].pos, qshared->quads[count].skipcount);
            }
            printf("\n");
        }
    }
    shutdown();
    qshared->state=-1;
    if ((logit & 1) != 0) {
        printf("completed\n");
    }
    exit(0);    
}