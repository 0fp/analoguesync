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

        self.t0 = time.time()

    def __del__(self):
        self.t_rise.cancel()
        self.t_fall.cancel()

    def set_cycle(self, cycle_length):

        self.cycle_length = cycle_length

        dt = time.time() - self.t0
        cl = self.cycle_length * self.multiplier
        self.cl = cl

        if abs(self.multiplier) == 1:
            # always reset for new cycle_length
            self.t_rise.cancel()
            gateoff = cl - self.min_pw
            print('-', gateoff,dt, cycle_length)
            self._rise()
            self.t_fall.cancel()
            self.t_fall = Timer(gateoff, self.fall)
            self.t_fall.start()

        if self.multiplier > 1:

            gateoff = cl - self.min_pw - dt
            if gateoff < 3 * self.min_pw:
                self.t0 = time.time()
                dt = 0
                gateoff = cl - self.min_pw
            self.t_rise.cancel()
            self._rise()

            print('-', gateoff,dt, cycle_length)
            self.t_fall.cancel()
            self.t_fall = Timer(gateoff, self.fall)
            self.t_fall.start()

    def rise(self):
        self.t0 = time.time()
        gateoff = self.cl - self.min_pw
        print('rise')
        self._rise()
        self.t_fall.cancel()
        self.t_fall = Timer(gateoff, self.fall)
        self.t_fall.start()

    def fall(self):
        print('fall')
        self._fall()
        self.t_rise.cancel()
        self.t_rise = Timer(self.min_pw, self.rise)
        self.t_rise.start()

def _click():
    count = 0
    def _():
        nonlocal count
        print(count)
        if count == 0:
            Popen(['aplay', '-q', 'clav02.wav'])
        elif count:
            Popen(['aplay', '-q', 'clav01.wav'])
        count = (count + 1) % 4
    return _

def main():
    poll_freq = 10

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

    click = LFO(_click(), lambda: True)
    click.multiplier = 4

    t = 0
    def set_cycle(_):
        nonlocal t
        now = time.time()
        if master_muliplier > 0:
            cycle_length = (now - t) / master_muliplier
        if master_muliplier < 0:
            cycle_length = (now - t) * (-master_muliplier)
        t = now

        print('BPM %i' % (100 / cycle_length))

        lfo.set_cycle(cycle_length)
        click.set_cycle(cycle_length)

    # main poll loop
    try:
        GPIO.wait_for_edge(ichannel, GPIO.RISING)
        t = time.time()
        GPIO.add_event_detect(ichannel, GPIO.RISING, set_cycle)

        while True:
            time.sleep(1/poll_freq)

    except KeyboardInterrupt:
        pass

    # cleanup after yourself
    finally:
        GPIO.output(ochannel, 0)
        GPIO.cleanup()

if __name__ == '__main__':
    main()
