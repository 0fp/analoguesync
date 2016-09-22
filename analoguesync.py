#!/usr/bin/python
#coding: utf8

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

class LFO():
    cycle_length = 1
    t0 = 0
    min_pw = 10 / 1000.

    def __init__(self):
        self.t0 = time.time()
        pass

    def state(self):
        dt = time.time() - self.t0
        if dt < self.cycle_length - self.min_pw:
            return 1
        else:
            return 0

def main():
    poll_freq = 500.

    # GPIO Setup
    ochannel = 27
    GPIO.setup(ochannel, GPIO.OUT)
    ichannel = 22
    GPIO.setup(ichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # loop variables
    cycle_length = 2.
    multiplicity = 2
    pulsewidth = 10 / 1000.
    lfo = LFO()

    # main poll loop
    try:
        GPIO.wait_for_edge(ichannel, GPIO.RISING)
        t = time.time()
        GPIO.add_event_detect(ichannel, GPIO.RISING)

        while True:

            if GPIO.event_detected(ichannel):
                now = time.time()
                cycle_length = now - t
                t = now
                print('BPM %i' % (100 / cycle_length))

                lfo.t0 = now
                lfo.cycle_length = cycle_length

            if GPIO.input(ochannel) != lfo.state():
                GPIO.output(ochannel, lfo.state())

            time.sleep(1/poll_freq)

    except KeyboardInterrupt:
        pass

    # cleanup after yourself
    finally:
        GPIO.output(ochannel, 0)
        GPIO.cleanup()

if __name__ == "__main__":
    main()
