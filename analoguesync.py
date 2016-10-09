#!/usr/bin/python3.4
#coding: utf8

import RPi.GPIO as GPIO
import time
from subprocess import Popen
from threading import Timer

GPIO.setmode(GPIO.BCM)

def l2bpm(l):
    return int(1/l*60/2)

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
        for k in range(0, steps):
            if lfo.on:
                t = (k + lfo.phi) / steps * cycles
                flanks += [(t, lfo.on)]
            if lfo.off:
                gate = max(0.01, min(lfo.dc, 0.99))
                t = (k + (lfo.phi + gate)%1) / steps * cycles
                flanks += [(t, lfo.off)]

    flanks.sort(key=lambda _ : _[0])
    #print(flanks)
    return flanks

def _click():
    count = 1
    def _():
        nonlocal count
        #click = 'clav02.wav' if count == 0 else 'clav01.wav'
        click = ('clav02.wav', 'clav01.wav')[count==0]
        Popen(['aplay', '-q', click])
        count = (count + 1) % 4
    return _

class LFO():
    multiplier = 1
    dc         = 0.01
    phi        = 0

    def __init__(self, on=None, off=None):
        self.on  = on
        self.off = off

    def set_multiplier(self, multiplier):
        self.multiplier += multiplier
        print('set multiplier %i' % self.multiplier)

    def set_dc(self, dc):
        self.dc = min(1, max(0, self.dc + 0.1*dc))
        print('set dc %f' % self.dc)

    def set_phi(self, phi):
        self.phi = max(0, min(self.phi + 0.1 * phi, .9))
        print('set phi %f' % self.phi)

class Cycle():
    last   = [0]
    length = .25
    vlast  = 0

    steps = []
    lfos = []

    def build(self):
        self.steps = calculate_steps([LFO(self.vsync)] + self.lfos)

    def sync(self, _=None):
        last = self.last
        last += [time.time()]


        length = last[1] - last[0]
        if length < 2 and length > 0.1:
            self.length = length

        dt = last[-1] - self.vlast
        if dt < self.length/2:
            self.length += dt

        self.last = last[1:]
        print('r', l2bpm(self.length))

    def vsync(self):
        print('-')
        t = time.time()
        last = self.last[-1]
        dt = t - last

        if dt < self.length:
            length = self.length - dt
            if length > self.length/2:
                self.length = length

            self.vlast = t

        print('v', l2bpm(self.length))

class RotaryController():
    last = 0

    def __init__(self, a, b, callback):
        GPIO.setup([a, b], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(a, GPIO.BOTH, self.rot)

        self.a = a
        self.b = b
        self.callback = callback

    def rot(self, _):
        a = GPIO.input(self.a)
        b = GPIO.input(self.b)
        state = (a ^ b) | b << 1

        if self.last == 3 and state == 1:
            self.callback( 1)
        if self.last == 0 and state == 2:
            self.callback(-1)

        self.last = state

class Controller():
    edit    = False
    channel = 0
    param   = None
    plist   = ['mult', 'dc', 'phi']
    controls = []
    cycle = None

    def __init__(self, indicator):
        self.indicator = indicator
        self.timer = Timer(0, lambda: None)
        self.edit_t = Timer(0, lambda: None)

    def _blink(self):
        GPIO.output(self.indicator, 1)
        self.timer = Timer(0.05, lambda: GPIO.output(self.indicator, 0))
        self.timer.start()

    def blink(self):
        if not self.edit:
            self._blink()

    def channel_info(self):
        if self.param is None:
            print('c %i' % self.channel)
        else:
            print('c %i: %s' % (self.channel, self.plist[self.param]))
        for i in range(self.channel + 1):
            self.timer = Timer(0.2 * i, self._blink)
            self.timer.start()

    def set_mode(self, _):

        if not self.edit:
            self.timer.cancel()
            self.edit  = True
            self.channel = 0
            return

        print(self.channel)
        c = self.controls[self.channel]

        if self.param is None:
            self.param = 0
        else:
            self.param += 1

        if self.param == len(c):
            # reset
            self.edit    = False
            self.channel = 0
            self.param   = None
            return

        self.channel_info()

    def input(self, value):
        if not self.edit:
            if self.cycle.last[0] < time.time() - 5:
                l = 1/(1/self.cycle.length + value/30.)
                self.cycle.length = max(0.2, min(l, 2))
            return

        if self.param is None:
            self.channel = (self.channel + value) % 4
            self.channel_info()
        else:
            self.controls[self.channel][self.param](value)
            self.cycle.build()

def main():

    # GPIO Setup
    ichannel   = 4
    cIndicator = 6
    cRotary    = [26, 19]
    cButton    = 13
    cOut       = [10, 9, 11, 5]

    GPIO.setup(ichannel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    controller = Controller(cIndicator)

    GPIO.setup(cButton, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(cButton, GPIO.FALLING, controller.set_mode, 500)

    rotC = RotaryController(cRotary[0], cRotary[1], controller.input)

    lfos = []

    GPIO.setup(cIndicator, GPIO.OUT)
    lfos += [LFO(controller.blink)]
    lfos[-1].multiplier = 2

    controls = []
    for channel in cOut:
        def _(c, s):
            return lambda: GPIO.output(c, s)
        GPIO.setup(channel, GPIO.OUT)
        lfo = LFO( _(channel, 1), _(channel, 0))
        lfos += [lfo]
        controls += [(lfo.set_multiplier, lfo.set_dc, lfo.set_phi)]

    lfos[-3].multiplier = 2
    lfos[-3].dc         = 0
    lfos[-3].phi        = 0.5
    lfos[-2].multiplier = 4
    lfos[-2].dc         = 0.9
    lfos[-1].multiplier = 2
    lfos[-1].dc         = 0.9

    lfos += [LFO(_click())]
    lfos[-1].multiplier = 2
    lfos[-1].phi = 0.9

    controller.controls = controls

    min_pulsewidth = 0.01
    cycle_length = 0.7
    sync_t = []

    cycle = Cycle()
    cycle.lfos = lfos
    cycle.build()
    controller.cycle = cycle

    GPIO.add_event_detect(ichannel, GPIO.RISING, cycle.sync)

    cnt = 0
    try:
        idx = 0
        while True:

            next = (idx + 1) % len(cycle.steps)

            #print(idx)
            cycle.steps[idx][1]()

            if next == 0:
                dx = int(cycle.steps[idx][0] + 1) - cycle.steps[idx][0]
            else:
                dx = cycle.steps[next][0] - cycle.steps[idx][0]

            _ = dx * cycle.length
            time.sleep(max(_, 0))
            idx = next % len(cycle.steps)

    except KeyboardInterrupt:
        pass

    finally:
        for channel in cIndicator, cOut:
            GPIO.output(channel, 0)
        GPIO.cleanup()

if __name__ == '__main__':
    main()
