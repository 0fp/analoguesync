#!/usr/bin/python3.4
#coding: utf8

import RPi.GPIO as GPIO
import time
from subprocess import Popen
from threading import Timer

GPIO.setmode(GPIO.BCM)

def calculate_steps(lfos):

    # m = abs(multiplier) ** sign(multiplier)
    cycles = max(lfos, key=lambda _: _.multiplier).multiplier
    if cycles < 1:
        cycles = 1

    flanks = []
    for lfo in lfos:
        m = abs(lfo.multiplier) ** (lfo.multiplier < 0 and -1 or 1)
        steps = int(cycles / m)
        print(steps)
        for k in range(0, steps):
            on  = (k / steps * cycles, lfo.channel, True)
            off = ((k+1) / steps * cycles - 0.01, lfo.channel, False)
            flanks += [on, off]


    flanks.sort(key=lambda _ : _[0])
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

class Cycle():
    last   = [0]
    length = 1
    drift  = 0

    def sync(self, _=None):
        last = self.last
        last += [time.time()]

        length = last[1] - last[0]
        if length < 2:
            self.drift  = self.length - length
            self.length = length

        self.last = last[1:]

def main():

    # GPIO Setup
    ichannel = 22
    GPIO.setup(ichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    lfos = []
    for channel in [17, 27]:
        lfos.append(lfo(channel))
        GPIO.setup(channel, GPIO.OUT)

    lfos[0].multiplier = 4
    lfos[1].multiplier = -4

    min_pulsewidth = 0.01
    cycle_length = 0.7
    sync_t = []

    steps = calculate_steps(lfos)

    cycle = Cycle()
    GPIO.wait_for_edge(ichannel, GPIO.RISING)
    cycle.sync()
    GPIO.wait_for_edge(ichannel, GPIO.RISING)
    cycle.sync()
    GPIO.add_event_detect(ichannel, GPIO.RISING, cycle.sync)

    cnt = 0
    try:
        idx = 0
        while True:

            next = (idx + 1) % len(steps)

            if idx == 0:
                while True:
                    time.sleep(0.002)
                    if abs(time.time() - cycle.last[0]) < 0.002:
                        break

            c = steps[idx][1]
            v = steps[idx][2]
            GPIO.output(c, v)

            if next == 0:
                dx = int(steps[idx][0] + 1) - steps[idx][0]
            dx = steps[next][0] - steps[idx][0]

            _ = dx * cycle.length
            time.sleep(max(_, 0))
            idx = next

    except KeyboardInterrupt:
        pass

    finally:
        for channel in [17, 27]:
            GPIO.output(channel, 0)
        GPIO.cleanup()

if __name__ == '__main__':
    main()
