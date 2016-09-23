#!/usr/bin/python3.4
#coding: utf8

import RPi.GPIO as GPIO
import time
from subprocess import Popen
from threading import Timer

GPIO.setmode(GPIO.BCM)

class LFO():
    cycle_length = 2.
    min_pw = 10 / 1000.
    multiplier = 1
    pulse = 0

    def __init__(self, rise, fall):
        self._rise = rise
        self._fall = fall

        self.t_fall = Timer(0, fall)

    def __del__(self):
        self.t_fall.cancel()

    def set_cycle(self, cycle_length):
        if self.multiplier == 0:
            return

        # start of cycle
        if self.pulse == 0:
            self.rise()

        # register estimated end of cycle
        t = (self.multiplier - self.pulse) * cycle_length - self.min_pw
        self.t_fall.cancel()
        self.t_fall = Timer(t, self.fall)
        self.t_fall.start()

        self.pulse += 1

    def rise(self):
        self._rise()

    def fall(self):
        self._fall()
        if self.pulse == self.multiplier:
            self.pulse = 0

def mkclick():
    measure = 0
    def _():
        nonlocal measure
        print(measure)
        if measure == 0:
            Popen(['aplay', '-q', 'clav02.wav'])
        elif measure % 2 == 0:
            Popen(['aplay', '-q', 'clav01.wav'])
        measure = (measure + 1) % 8
    return _

click = mkclick()

def main():
    poll_freq = 500.

    # GPIO Setup
    ochannel = 27
    GPIO.setup(ochannel, GPIO.OUT)
    ichannel = 22
    GPIO.setup(ichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    # loop variables
    cycle_length = 2.
    lfo = LFO(lambda: GPIO.output(ochannel, 1),
              lambda: GPIO.output(ochannel, 0))

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

                lfo.set_cycle(cycle_length)

                click()

            time.sleep(1/poll_freq)

    except KeyboardInterrupt:
        pass

    # cleanup after yourself
    finally:
        GPIO.output(ochannel, 0)
        GPIO.cleanup()

if __name__ == '__main__':
    main()
