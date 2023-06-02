# python implementation of Nielk1/ExtendInput.DataTools.DualSense.TriggerEffectGenerator.cs
#
# https://gist.github.com/Nielk1/6d54cc2c00d2201ccb8c2720ad7538db

from enum import IntEnum
from typing import Optional

from pydualsense.enums import TriggerModes
from pydualsense.pydualsense import DSTrigger, pydualsense

class Button(IntEnum):
    R2 = 11
    L2 = 22

def ffb_off() -> DSTrigger:
    dst: DSTrigger = DSTrigger()
    dst.mode = TriggerModes.FFB_Off
    return dst


def ffb_feedback(position: int, strength: int) -> Optional[DSTrigger]:
    if not (0 <= position <= 9):
        return None
    if 0 < strength <= 8:
        dst: DSTrigger = DSTrigger()

        force_value = strength - 1
        force_zones = 0
        active_zones = 0
        for i in range(10):
            force_zones |= (force_value << (3 * i))
            active_zones |= (1 << i)

        dst.mode = TriggerModes.FFB_Feedback
        dst.forces[0] = (active_zones >> 0) & 0xff
        dst.forces[1] = (active_zones >> 8) & 0xff
        dst.forces[2] = (force_zones >> 0) & 0xff
        dst.forces[3] = (force_zones >> 8) & 0xff
        dst.forces[4] = (force_zones >> 16) & 0xff
        dst.forces[5] = (force_zones >> 24) & 0xff

        return dst
    else:
        return None


def ffb_weapon(start_position: int, end_position: int, strength: int) -> Optional[DSTrigger]:
    if not (2 <= start_position <= 7):
        return None
    if end_position > 8:
        return None
    if end_position <= start_position:
        return None
    if strength > 8:
        return None
    if 0 < strength <= 8:
        dst: DSTrigger = DSTrigger()

        start_and_stop_zone = (1 << start_position) | (1 << end_position)

        dst.mode = TriggerModes.FFB_Weapon
        dst.forces[0] = (start_and_stop_zone >> 0) & 0xff
        dst.forces[1] = (start_and_stop_zone >> 8) & 0xff
        dst.forces[2] = strength - 1

        return dst
    else:
        return None

def ffb_vibration(position: int, amplitude: int, frequency: int) -> Optional[DSTrigger]:
    if not (0 <= position <= 9):
        return None
    if amplitude > 8:
        return None
    if amplitude > 0 and frequency > 0:
        dst: DSTrigger = DSTrigger()

        strength_value = (amplitude - 1) & 0x07
        amplitude_zones = 0
        active_zones = 0

        for i in range(10):
            amplitude_zones |= strength_value << (3 * i)
            active_zones |= (1 << i)

        dst.mode = TriggerModes.FFB_Vibration
        dst.forces[0] = (active_zones >> 0) & 0xff
        dst.forces[1] = (active_zones >> 8) & 0xff
        dst.forces[2] = (amplitude_zones >> 0) & 0xff
        dst.forces[3] = (amplitude_zones >> 8) & 0xff
        dst.forces[4] = (amplitude_zones >> 16) & 0xff
        dst.forces[5] = (amplitude_zones >> 24) & 0xff
        dst.forces[6] = (amplitude_zones >> 32) & 0xff
        dst.forces[7] = (amplitude_zones >> 40) & 0xff
        dst.forces[8] = frequency

        return dst
    else:
        return None


