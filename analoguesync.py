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
    lastState = 0
    cycle_length = 2.
    multiplicity = 2
    pulsewidth = 10 / 1000.

    # main poll loop
    try:
        GPIO.wait_for_edge(ichannel, GPIO.RISING)
        t = time.time()
        while True:
            # get sync signal state
            state = GPIO.input(ichannel)

            # detect edge
            if state != lastState:
                lastState = state
                print('+{}s: state is now {}'.format(cycle_length, state))

                # switch slave output, update sync parameters
                if state == 1:
                    now = time.time()
                    cycle_length = now - t
                    t = now
                    freq = 1. / cycle_length * multiplicity
                    print('BPM %i' % (100*freq))
                    p.ChangeFrequency( freq )
                    p.start(99)

    except KeyboardInterrupt:
        pass

    # cleanup after yourself
    finally:
        GPIO.output(ochannel, 0)
        p.stop()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
