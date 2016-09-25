#!/usr/bin/python3.4
#coding: utf8

import RPi.GPIO as GPIO
import time
from subprocess import Popen
from threading import Timer

GPIO.setmode(GPIO.BCM)

def calculate_steps(lfos):
    lfos.sort(key=lambda _:_.multiplier, reverse=True)

    # m = abs(multiplier) ** sign(multiplier)
    cycles = lfos[0].multiplier
    if cycles < 1:
        cycles = 1

    flanks = []
    for lfo in lfos:
        m = abs(lfo.multiplier) ** (lfo.multiplier < 0 and -1 or 1)
        steps = int(cycles / m)
        print(steps)
        for k in range(0, steps):
            on  = (k / steps * cycles, lfo.channel, True)
            off = ((k+0.1) / steps * cycles - 0.01, lfo.channel, False)
            flanks += [on, off]


    flanks.sort(key=lambda _:_[0])
    print(flanks)
    return flanks

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

class lfo():
    multiplier = 0
    channel = 0
    def __init__(self, channel):
        self.channel = channel

    def __repr__(self):
        return '({}, {})'.format(self.channel, self.multiplier)

def main():

    # GPIO Setup
    ichannel = 22
    GPIO.setup(ichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    lfos = []
    for channel in [17, 27]:
        lfos.append(lfo(channel))
        GPIO.setup(channel, GPIO.OUT)

    lfos[0].multiplier = -2
    lfos[1].multiplier = 3

    min_pulsewidth = 0.01
    cycle_length = 0.7
    sync_t = []

    steps = calculate_steps(lfos)

    GPIO.wait_for_edge(ichannel, GPIO.RISING)
#    GPIO.add_event_detect(ichannel, GPIO.RISING, set_cycle)

    try:
        idx = 0
        while True:
            c = steps[idx][1]
            v = steps[idx][2]
            print(c, v)
            GPIO.output(c, v)

            next = (idx + 1) % len(steps)
            dt = steps[next][0] - steps[idx][0]
            dt = max(dt, 0)

            time.sleep(dt * cycle_length)
            idx = next

    except KeyboardInterrupt:
        pass

    finally:
        for channel in [17, 27]:
            GPIO.output(channel, 0)
        GPIO.cleanup()

if __name__ == '__main__':
    main()
