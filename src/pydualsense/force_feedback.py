# python implementation of Nielk1/ExtendInput.DataTools.DualSense.TriggerEffectGenerator.cs
#
# https://gist.github.com/Nielk1/6d54cc2c00d2201ccb8c2720ad7538db

from typing import TypeVar

from .enums import TriggerModes
from .models import TriggerModel

T = TypeVar("T", int, float)


def clip(value: T, min_value: T, max_value: T) -> T:
    return max(min(max_value, value), min_value)


def ffb_off() -> TriggerModel:
    dst: TriggerModel = TriggerModel()
    dst.mode = TriggerModes.FFB_Off
    return dst


def ffb_feedback(position: int, strength: int) -> TriggerModel:
    dst: TriggerModel = TriggerModel()

    position = clip(position, 0, 9)
    strength = clip(strength, 1, 8)

    force_value = strength - 1
    force_zones = 0
    active_zones = 0
    for i in range(position, 10):
        force_zones |= force_value << (3 * i)
        active_zones |= 1 << i

    dst.mode = TriggerModes.FFB_Feedback
    dst.forces[0] = (active_zones >> 0) & 0xFF
    dst.forces[1] = (active_zones >> 8) & 0xFF
    dst.forces[2] = (force_zones >> 0) & 0xFF
    dst.forces[3] = (force_zones >> 8) & 0xFF
    dst.forces[4] = (force_zones >> 16) & 0xFF
    dst.forces[5] = (force_zones >> 24) & 0xFF

    return dst


def ffb_weapon(start_position: int, end_position: int, strength: int) -> TriggerModel:
    dst: TriggerModel = TriggerModel()

    start_position = clip(start_position, 2, 7)
    end_position = clip(end_position, start_position, 8)
    strength = clip(strength, 1, 8)

    start_and_stop_zone = (1 << start_position) | (1 << end_position)

    dst.mode = TriggerModes.FFB_Weapon
    dst.forces[0] = (start_and_stop_zone >> 0) & 0xFF
    dst.forces[1] = (start_and_stop_zone >> 8) & 0xFF
    dst.forces[2] = strength - 1

    return dst


def ffb_vibration(position: int, amplitude: int, frequency: int) -> TriggerModel:
    dst: TriggerModel = TriggerModel()

    position = clip(position, 0, 9)
    amplitude = clip(amplitude, 1, 8)
    frequency = clip(frequency, 1, 255)

    strength_value = (amplitude - 1) & 0x07
    amplitude_zones = 0
    active_zones = 0

    for i in range(position, 10):
        amplitude_zones |= strength_value << (3 * i)
        active_zones |= 1 << i

    dst.mode = TriggerModes.FFB_Vibration
    dst.forces[0] = (active_zones >> 0) & 0xFF
    dst.forces[1] = (active_zones >> 8) & 0xFF
    dst.forces[2] = (amplitude_zones >> 0) & 0xFF
    dst.forces[3] = (amplitude_zones >> 8) & 0xFF
    dst.forces[4] = (amplitude_zones >> 16) & 0xFF
    dst.forces[5] = (amplitude_zones >> 24) & 0xFF
    # dst.forces[6] = (amplitude_zones >> 32) & 0xFF
    # dst.forces[7] = (amplitude_zones >> 40) & 0xFF
    dst.forces[8] = frequency

    return dst
