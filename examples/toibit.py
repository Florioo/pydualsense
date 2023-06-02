#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ************************************************************
#
#     main.py
#
#     Copyright 2023 Sony Interactive Entertainment Inc.
#
# ************************************************************

import argparse
import fileinput
import pprint
import signal
import sys
import time
from logging import (
    DEBUG,
    INFO,
    NOTSET,
    WARNING,
    Formatter,
    NullHandler,
    StreamHandler,
    getLogger,
)

from pydualsense import pydualsense, TriggerModes, DSTouchpad
from pydualsense.force_feedback import ffb_off, ffb_weapon, ffb_feedback, ffb_vibration

logger = getLogger(__name__)
if __name__ == "__main__":
    default_log_level = DEBUG
    handler = StreamHandler()
    handler.setLevel(default_log_level)
    formatter = Formatter("%(asctime)s %(levelname)7s %(message)s")
    handler.setFormatter(formatter)
    logger.setLevel(default_log_level)
else:
    default_log_level = NOTSET
    handler = NullHandler()
logger.addHandler(handler)

LOOP = True

def ctrl_c_handler(_signum, _frame):
    global LOOP
    print("Ctrl-C")
    LOOP = False

signal.signal(signal.SIGINT, ctrl_c_handler)


def cross_pressed(state):
    print(state)

def touchpad0(active, id_num, x, y):
    print("TouchPad0", active, id_num, x, y)

def touchpad1(active, id_num, x, y):
    print("TouchPad1", active, id_num, x, y)

LED_1 = 0
def l2(value):
    global LED_1
    LED_1 = value

LED_2 = 0
def r2(value):
    global LED_2
    LED_2 = value


def example():
    ds: pydualsense = pydualsense() # open controller
    ds.init() # initialize controller

    try:
        if ds.conType == 0:
            print("Dualsense found (Bluetooth connection)")
        else:
            print("Dualsense found (USB connection)")

        ds.cross_pressed += cross_pressed
        ds.trackpad0_frame_reported += touchpad0
        ds.trackpad1_frame_reported += touchpad1
        ds.l2_changed += l2
        ds.r2_changed += r2

        ds.light.setColorI(0, 255, 0) # set touchpad color to green
        #tl = ffb_feedback(position=1, strength=8)
        ds.triggerL = ffb_weapon(start_position=4, end_position=6, strength=8)
        #ds.triggerR = ffb_feedback(position=1, strength=8)
        ds.triggerR = ffb_vibration(position=4, amplitude=5, frequency=3)
        while not ds.state.R1:
            ds.light.setColorI(LED_1, LED_2, 0)
            time.sleep(0.016)
    except Exception as ex:
        raise ex
    finally:
        print("disconnecting... (please wait)")
        ds.triggerL = ffb_off()
        ds.triggerR = ffb_off()
        ds.light.setColorI(0, 0, 0) # set touchpad color to green
        time.sleep(0.5)
        ds.close()
        print("disconnected")

def options(argv):
    op = argparse.ArgumentParser()
    op.add_argument("--dry-run", action="store_true", help="do not perform actions")
    op.add_argument("-v", "--verbose", action="store_true", help="verbose mode")
    op.add_argument("-q", "--quiet", action="store_true", help="quiet mode")
    op.add_argument("argv", nargs="*", help="args")
    opt = op.parse_args(argv[1:])
    # set logging level
    if opt.quiet:
        loglevel = WARNING
    elif opt.verbose:
        loglevel = DEBUG
    else:
        loglevel = INFO
    handler.setLevel(loglevel)
    logger.setLevel(loglevel)
    return opt


def main(argv):
    opt = options(argv)

    example()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

