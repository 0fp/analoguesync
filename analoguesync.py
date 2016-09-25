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
        if lfo.multiplier == 0:
            continue

        m = abs(lfo.multiplier) ** (lfo.multiplier < 0 and -1 or 1)
        steps = int(cycles / m)
        print(steps)
        for k in range(0, steps):
            if lfo.on:
                flanks += [(k / steps * cycles, lfo.on)]
            if lfo.off:
                flanks += [((k + lfo.dc) / steps * cycles - 0.01, lfo.off)]

    flanks.sort(key=lambda _ : _[0])
    print(flanks)
    return flanks

def _click():
    count = 0
    def _():
        nonlocal count
        #click = 'clav02.wav' if count == 0 else 'clav01.wav'
        click = ('clav02.wav', 'clav01.wav')[count==0]
        Popen(['aplay', '-q', click])
        count = (count + 1) % 4
    return _

class LFO():
    multiplier = 1
    dc = 0.5
    def __init__(self, on=None, off=None):
        self.on  = on
        self.off = off

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
        def _(c, s):
            return lambda: GPIO.output(c, s)
        GPIO.setup(channel, GPIO.OUT)
        lfos.append(LFO( _(channel, 1), _(channel, 0)))

    lfos[0].multiplier = 2
    lfos[1].multiplier = 1

    lfos += [LFO(_click())]

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

            steps[idx][1]()

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
