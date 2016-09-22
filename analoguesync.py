#!/usr/bin/python
#coding: utf8

import RPi.GPIO as GPIO
import time

def main():
    channel = 22
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    lastState = 0
    t = 0
    while True:
        GPIO
        state = GPIO.input(channel)
        if state != lastState:
            lastState = state
            print('{} state is now {}'.format(t, state))
        time.sleep(0.001)
        t += 1

if __name__ == "__main__":
    main()
