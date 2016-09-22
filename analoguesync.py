#!/usr/bin/python
#coding: utf8

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

def main():
    poll_freq = 500.

    # GPIO Setup
    ochannel = 27
    GPIO.setup(ochannel, GPIO.OUT)
    p = GPIO.PWM(ochannel, 0.5)
    ichannel = 22
    GPIO.setup(ichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # loop variables
    cycle_length = 2.
    multiplicity = 2
    pulsewidth = 10 / 1000.

    # main poll loop
    try:
        t = time.time()
        GPIO.wait_for_edge(ichannel, GPIO.RISING)

        while True:
            GPIO.wait_for_edge(ichannel, GPIO.RISING)
            now = time.time()
            cycle_length = now - t
            t = now
            freq = 1. / cycle_length
            dc = 1 - pulsewidth / cycle_length
            print('BPM %i' % (100*freq))
            p.ChangeFrequency( freq * multiplicity )
            p.start(100 * dc)

    except KeyboardInterrupt:
        pass

    # cleanup after yourself
    finally:
        GPIO.output(ochannel, 0)
        p.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
