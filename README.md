# pimotors
A collection of classes to drive motors directly connected to a Raspberry Pi, with smart feedback control.

Assuming your project needs a raspberry pi or similarly capable computer, but is not too heavily loaded, even a Raspberry pi zero can directly control and monitor motors up to several thousand rpm. A polling technique is used.

A Raspberry pi is quite fast enough to control and monitor motors running up to around 10000 rpm. This set of classes provides the basic functioanlity to do this with the following modules:
##driver and control modules
* dc_adafruit_dchat: dc motor connected via an adafruit dc and stepper motor hat

* dc_h_bridge_pigpio: dc motor connected via an h-bridge ( such as a pimoroni explorer phat) directly controlled via gpio pins and using pigpio to provide control of duty cycle and pulse frequency. 

* quadencoder: a quadrature shaft encoder, such as the Pololu Magnetic Encoder Pair Kit for Micro Metal Gearmotors. pigpio is used purely to count the pulses and the quadencoder class polls the counter (typically around 20 times per second) to kepp track of the motor.

* dcmotorbasic: A basic motor control, which uses helper classes to drive the motor and optionally track the sensors. It also has functionality to provide linear control of motor speed (duty cycle control is typically close to asymptotic which is not friendly!
## basic logger module used by the drivers above
* logger: a basic log facility for debug and writing trace files that can easily be analysed later
## modules that provide a console based ui to test motors
* keyboardinp: simple class to provide asyncronous keyboard input for the console (text) based form system (textdisp)

* textdisp: a basic form handler that will run over ssh 

* main: a utility to test motors using all the other classes here. Runs on the Raspberry pi and can be access via ssh
# setup
This all runs on Raspberry Pi 2x and 3x as well as Pi Zero

It runs on raspbian lite (i.e. the command line only version)

* enable i2c
* if using the adafruit dc and stepper motor HAT, [install the adafruit libraries for the HAT](https://learn.adafruit.com/adafruit-dc-and-stepper-motor-hat-for-raspberry-pi/installing-software).
* clone this repository
* in the folder: **python3 main.py**
