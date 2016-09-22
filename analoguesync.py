#!/usr/bin/python
#coding: utf8

import RPi.GPIO as GPIO
import time

def main():
    ichannel = 22
    ochannel = 27
    poll_freq = 500.
    pulsewidth = 10 / 1000.

    # GPIO Setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(ochannel, GPIO.OUT)

    # loop variables
    lastState = 0
    t = time.time()
    pulseperiod = 0
    gate = 0

    # main poll loop
    try:
        while True:
            # get sync signal state
            state = GPIO.input(ichannel)

            # detect edge
            if state != lastState:
                lastState = state
                print('+{}s: state is now {}'.format(pulseperiod, state))

                # switch slave output, update sync parameters
                if state == 1:
                    now = time.time()
                    pulseperiod = now - t
                    gate = pulseperiod - pulsewidth
                    t = now
                    print('set output')
                    GPIO.output(ochannel, 1)

            # check for gate time overflow
            if (time.time() - t > gate) and GPIO.input(ochannel):
                print('+{}s: reset output'.format(t / poll_freq))
                GPIO.output(ochannel, 0)

            # wait in darkness
            time.sleep(1/poll_freq)

    except KeyboardInterrupt:
        pass

    # cleanup after yourself
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
