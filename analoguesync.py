#!/usr/bin/python
#coding: utf8

import RPi.GPIO as GPIO
import time

def main():
    channel = 22
    poll_freq = 500.

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    lastState = 0
    t = 0
    while True:
        GPIO
        state = GPIO.input(channel)
        if state != lastState:
            lastState = state
            print('+{}s: state is now {}'.format(t / poll_freq, state))
            t = 0
        time.sleep(1/poll_freq)
        t += 1

if __name__ == "__main__":
    main()
