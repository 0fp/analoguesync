#!/usr/bin/python3.4
#coding: utf8

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

class LFO():
    cycle_length = 2.
    t0 = 0
    min_pw = 10 / 1000.
    multiplier = -2
    c0 = 0
    c1 = 0

    def __init__(self):
        self.t0 = time.time()
        pass

    def state(self):
        dt = time.time() - self.t0

        if self.multiplier < 1:

            if self.c1 == - self.multiplier:
                if dt < self.min_pw:
                    if self.c0 == 0:
                        self.c1 = 0
                        return 1

                if dt < self.cycle_length - self.min_pw:
                    return 1

                if self.c0 == self.c1:
                    self.c0 = 0
                    return 0

                if self.c0 == 0:
                    return 0

            if self.c0 == self.c1:
                if dt < self.min_pw:
                    self.c0 += 1
            else:
                if dt > self.min_pw:
                    self.c1 += 1
            return 1

        sub_dt = dt
        cycle_length = self.cycle_length / self.multiplier

        while sub_dt > cycle_length:
            sub_dt -= cycle_length

        if sub_dt < cycle_length - self.min_pw:
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

if __name__ == '__main__':
    main()
