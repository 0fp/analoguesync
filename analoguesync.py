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

        self.t_rise = Timer(0, self.rise)
        self.t_fall = Timer(0, self.fall)

    def __del__(self):
        self.t_fall.cancel()

    def set_cycle(self, cycle_length):

        self.cycle_length = cycle_length

        # always reset for new cycle_length
        self.t_rise.cancel()
        self.t_fall.cancel()

        if self.multiplier == 0:
            return

        # start of cycle
        self.rise()

    def rise(self):
        if self.pulse == 0:
            self._rise()

        # register estimated end of cycle
        t = (self.multiplier - self.pulse) * self.cycle_length - self.min_pw
        self.t_fall.cancel()
        self.t_fall = Timer(t, self.fall)
        self.t_fall.start()

        self.pulse = (self.pulse + 1) % self.multiplier

    def fall(self):
        self._fall()

        # register next start of cycle
        self.t_rise.cancel()
        self.t_rise = Timer(self.min_pw, self.rise)
        self.t_rise.start()

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
    master_muliplier = 2
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
                if master_muliplier > 0:
                    cycle_length = (now - t) / master_muliplier
                if master_muliplier < 0:
                    cycle_length = (now - t) * (-master_muliplier)
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
