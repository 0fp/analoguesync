#!/usr/bin/python
#coding: utf8

import RPi.GPIO as GPIO
import time

def main():
    ichannel = 22
    ochannel = 27
    poll_freq = 500.
    pulsewidth = 10 / 1000.

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ochannel, GPIO.OUT)

    lastState = 0
    t = time.time()
    pulseperiod = 0
    while True:
        GPIO
        state = GPIO.input(ichannel)

        if state != lastState:
            lastState = state
            print('+{}s: state is now {}'.format(pulseperiod, state))
            if state == 1:
                now = time.time()
                pulseperiod = now - t
                gate = pulseperiod - pulsewidth
                t = now
                print('set output')
                GPIO.output(ochannel, 1)

        if (time.time() - t > gate) and GPIO.input(ochannel):
            print('+{}s: reset output'.format(t / poll_freq))
            GPIO.output(ochannel, 0)

        time.sleep(1/poll_freq)

    GPIO.cleanup()

if __name__ == "__main__":
    main()
