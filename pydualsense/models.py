from typing import List

from pydualsense.checksum import compute
from .enums import BatteryState, Brightness, ConnectionType, LedOptions, PlayerID, PulseOptions, TriggerModes
from pydantic import BaseModel, Field


class TouchpaModel(BaseModel):
    isActive: bool = False
    ID: int = 0
    X: int = 0
    Y: int = 0

    def __eq__(self, other) -> bool:
        return (
            (self.isActive == other.isActive) and (self.ID == other.ID) and (self.X == other.X) and (self.Y == other.Y)
        )


class VectorModel(BaseModel):
    X: float = 0
    Y: float = 0
    Z: float = 0

    def __str__(self) -> str:
        return f"X: {self.X:7.3f}, Y: {self.Y:7.3f}, Z: {self.Z:7.3f}"


class DSBatteryModel(BaseModel):
    State: BatteryState = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
    Level: int = 0


class JoystickModel(BaseModel):
    X: float = 0
    Y: float = 0
    pressed: bool = False


class DpadModel(BaseModel):
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False

    def from_state(self, state: int):
        if state == 0:
            self.up = True
            self.down, self.left, self.right = False, False, False

        elif state == 1:
            self.up, self.right = True, True
            self.down, self.left = False, False

        elif state == 2:
            self.right = True
            self.up, self.down, self.left = False, False, False

        elif state == 3:
            self.right, self.down = True, True
            self.up, self.left = False, False

        elif state == 4:
            self.down = True
            self.up, self.right, self.left = False, False, False

        elif state == 5:
            self.down, self.left = True, True
            self.up, self.right = False, False

        elif state == 6:
            self.left = True
            self.up, self.down, self.right = False, False, False

        elif state == 7:
            self.left, self.up = True, True
            self.down, self.right = False, False

        else:
            self.up, self.down, self.left, self.right = False, False, False, False


class TriggerModel(BaseModel):
    mode: TriggerModes = TriggerModes.Off
    forces: List[int] = Field(default_factory=lambda: [0 for i in range(10)])

    def setForce(self, forceID: int = 0, force: int = 0):
        """
        Sets the forces of the choosen force parameter

        Args:
            forceID (int, optional): force parameter. Defaults to 0.
            force (int, optional): applied force to the parameter. Defaults to 0.

        Raises:
            TypeError: wrong type of forceID or force
            Exception: choosen a false force parameter
        """
        if not isinstance(forceID, int) or not isinstance(force, int):
            raise TypeError("forceID and force needs to be type int")

        if forceID > 6 or forceID < 0:
            raise Exception("only 7 parameters available")

        self.forces[forceID] = force


class LedState(BaseModel):
    R: float = 0
    G: float = 0
    B: float = 0


class DeviceInputState(BaseModel):
    L1: bool = False
    L2: float = 0
    L3: bool = False

    R1: bool = False
    R2: float = 0
    R3: bool = False

    left_joystick: JoystickModel = JoystickModel()
    right_joystick: JoystickModel = JoystickModel()

    triangle: bool = False
    circle: bool = False
    cross: bool = False
    square: bool = False

    dpad: DpadModel = DpadModel()

    options: bool = False
    share: bool = False
    ps: bool = False
    mic: bool = False

    accel: VectorModel = VectorModel()
    gyroscope: VectorModel = VectorModel()

    trackPadTouch0: TouchpaModel = TouchpaModel()
    trackPadTouch1: TouchpaModel = TouchpaModel()

    battery: DSBatteryModel = DSBatteryModel()
    
    def from_state(self, state: bytearray):
        states = list(state)

        # states 0 is always 1
        self.left_joystick.X = (states[1] - 127) / 127.0
        self.left_joystick.Y = (states[2] - 127) / 127.0
        self.right_joystick.X = (states[3] - 127) / 127.0
        self.right_joystick.Y = (states[4] - 127) / 127.0
        self.L2 = states[5]
        self.R2 = states[6]

        # state 7 always increments -> not used anywhere
        buttonState = states[8]
        self.triangle = (buttonState & (1 << 7)) != 0
        self.circle = (buttonState & (1 << 6)) != 0
        self.cross = (buttonState & (1 << 5)) != 0
        self.square = (buttonState & (1 << 4)) != 0

        # dpad
        self.dpad.from_state(buttonState & 0x0F)

        misc = states[9]
        self.R3 = (misc & (1 << 7)) != 0
        self.L3 = (misc & (1 << 6)) != 0
        self.options = (misc & (1 << 5)) != 0
        self.share = (misc & (1 << 4)) != 0
        self.right_joystick.pressed = (misc & (1 << 3)) != 0
        self.left_joystick.pressed = (misc & (1 << 2)) != 0
        self.R1 = (misc & (1 << 1)) != 0
        self.L1 = (misc & (1 << 0)) != 0

        misc2 = states[10]
        self.ps = (misc2 & (1 << 0)) != 0
        self.touchBtn = (misc2 & 0x02) != 0
        self.micBtn = (misc2 & 0x04) != 0

        # trackpad touch
        self.trackPadTouch0.ID = states[33] & 0x7F
        self.trackPadTouch0.isActive = (states[33] & 0x80) == 0
        self.trackPadTouch0.X = ((states[35] & 0x0F) << 8) | (states[34])
        self.trackPadTouch0.Y = ((states[36]) << 4) | ((states[35] & 0xF0) >> 4)

        # trackpad touch
        self.trackPadTouch1.ID = states[37] & 0x7F
        self.trackPadTouch1.isActive = (states[37] & 0x80) == 0
        self.trackPadTouch1.X = ((states[39] & 0x0F) << 8) | (states[38])
        self.trackPadTouch1.Y = ((states[40]) << 4) | ((states[39] & 0xF0) >> 4)

        # accelerometer
        self.gyroscope.X = int.from_bytes(([states[16], states[17]]), byteorder="little", signed=True) / 8192.0
        self.gyroscope.Y = int.from_bytes(([states[18], states[19]]), byteorder="little", signed=True) / 8192.0
        self.gyroscope.Z = int.from_bytes(([states[20], states[21]]), byteorder="little", signed=True) / 8192.0

        # gyrometer
        self.accel.X = int.from_bytes(([states[22], states[23]]), byteorder="little", signed=True) / 8192.0
        self.accel.Y = int.from_bytes(([states[24], states[25]]), byteorder="little", signed=True) / 8192.0
        self.accel.Z = int.from_bytes(([states[26], states[27]]), byteorder="little", signed=True) / 8192.0

        # from kit-nya
        battery = states[53]
        self.battery.State = BatteryState((battery & 0xF0) >> 4)
        self.battery.Level = min((battery & 0x0F) * 10 + 5, 100)


class PlayerLed(BaseModel):
    brightness: float = 0
    player_count: int = 0

    def get_player_id(self) -> PlayerID:
        if self.player_count == 1:
            return PlayerID.PLAYER_1

        elif self.player_count == 2:
            return PlayerID.PLAYER_2

        elif self.player_count == 3:
            return PlayerID.PLAYER_3

        elif self.player_count == 4:
            return PlayerID.PLAYER_4

        raise ValueError("Player count must be between 1 and 4")

    def get_led_option(self) -> LedOptions:
        return LedOptions.PlayerLedBrightness

    def get_brightness(self) -> Brightness:
        if self.brightness > 0.5:
            return Brightness.high

        elif self.brightness > 0.2:
            return Brightness.medium

        return Brightness.low

    def get_pulse_options(self) -> PulseOptions:
        return PulseOptions.Off


class DeviceOutputState(BaseModel):
    right_motor: float = 0
    left_motor: float = 0

    microphone_led: bool = False
    microphone_mute: bool = False

    triggerR: TriggerModel = TriggerModel()
    triggerL: TriggerModel = TriggerModel()

    rgb_led: LedState = LedState()
    player_led: PlayerLed = PlayerLed()

    def prepareReport(self, connection_type: ConnectionType) -> list:
        outReport = [0] * connection_type.get_out_report_length()  # create empty list with range of output report
        outReport[0] = connection_type.get_type()  # bt type

        if connection_type == ConnectionType.USB:
            # flags determing what changes this packet will perform
            # 0x01 set the main motors (also requires flag 0x02); setting this by itself will 
            # allow rumble to gracefully terminate and then re-enable audio haptics, whereas not setting it will kill
            # the rumble instantly and re-enable audio haptics.
            # 0x02 set the main motors (also requires flag 0x01; without bit 0x01 motors are 
            # allowed to time out without re-enabling audio haptics)
            # 0x04 set the right trigger motor
            # 0x08 set the left trigger motor
            # 0x10 modification of audio volume
            # 0x20 toggling of internal speaker while headset is connected
            # 0x40 modification of microphone volume
            outReport[1] = 0xFF  # [1]

            # further flags determining what changes this packet will perform
            # 0x01 toggling microphone LED
            # 0x02 toggling audio/mic mute
            # 0x04 toggling LED strips on the sides of the touchpad
            # 0x08 will actively turn all LEDs off? Convenience flag? (if so, third
            # parties might not support it properly)
            # 0x10 toggling white player indicator LEDs below touchpad
            # 0x20 ???
            # 0x40 adjustment of overall motor/effect power (index 37 - read note on triggers)
            # 0x80 ???
            outReport[2] = 0x1 | 0x2 | 0x4 | 0x10 | 0x40  # [2]

            outReport[3] = int(self.right_motor)  # right low freq motor 0-255 # [3]
            outReport[4] = int(self.left_motor)  # left low freq motor 0-255 # [4]

            # outReport[5] - outReport[8] audio related

            # set Micrphone LED, setting doesnt effect microphone settings
            outReport[9] = self.microphone_led  # [9]

            outReport[10] = 0x10 if self.microphone_mute is True else 0x00

            # add right trigger mode + parameters to packet
            outReport[11] = self.triggerR.mode.value
            outReport[12] = self.triggerR.forces[0]
            outReport[13] = self.triggerR.forces[1]
            outReport[14] = self.triggerR.forces[2]
            outReport[15] = self.triggerR.forces[3]
            outReport[16] = self.triggerR.forces[4]
            outReport[17] = self.triggerR.forces[5]
            outReport[18] = self.triggerR.forces[6]
            outReport[19] = self.triggerR.forces[7]
            outReport[20] = self.triggerR.forces[8]
            outReport[21] = self.triggerR.forces[9]

            outReport[22] = self.triggerL.mode.value
            outReport[23] = self.triggerL.forces[0]
            outReport[24] = self.triggerL.forces[1]
            outReport[25] = self.triggerL.forces[2]
            outReport[26] = self.triggerL.forces[3]
            outReport[27] = self.triggerL.forces[4]
            outReport[28] = self.triggerL.forces[5]
            outReport[29] = self.triggerL.forces[6]
            outReport[30] = self.triggerL.forces[7]
            outReport[31] = self.triggerL.forces[8]
            outReport[32] = self.triggerL.forces[9]

            outReport[39] = self.player_led.get_led_option()
            outReport[42] = self.player_led.get_pulse_options()
            outReport[43] = self.player_led.get_brightness()
            outReport[44] = self.player_led.get_player_id()
            outReport[45] = int(self.rgb_led.R * 255)
            outReport[46] = int(self.rgb_led.G * 255)
            outReport[47] = int(self.rgb_led.B * 255)

        elif connection_type == ConnectionType.BT:
            outReport[1] = 0x02

            # flags determing what changes this packet will perform
            # 0x01 set the main motors (also requires flag 0x02); setting this by itself will allow
            # rumble to gracefully terminate and then re-enable audio haptics, whereas not setting it
            # will kill the rumble instantly and re-enable audio haptics.
            # 0x02 set the main motors (also requires flag 0x01; without bit 0x01 motors are allowed 
            # to time out without re-enabling audio haptics)
            # 0x04 set the right trigger motor
            # 0x08 set the left trigger motor
            # 0x10 modification of audio volume
            # 0x20 toggling of internal speaker while headset is connected
            # 0x40 modification of microphone volume
            outReport[2] = 0xFF  # [1]

            # further flags determining what changes this packet will perform
            # 0x01 toggling microphone LED
            # 0x02 toggling audio/mic mute
            # 0x04 toggling LED strips on the sides of the touchpad
            # 0x08 will actively turn all LEDs off? Convenience flag? (if so, third 
            # parties might not support it properly)
            # 0x10 toggling white player indicator LEDs below touchpad
            # 0x20 ???
            # 0x40 adjustment of overall motor/effect power (index 37 - read note on triggers)
            # 0x80 ???
            if not self.bt_led_initialized:
                outReport[3] = 0x1 | 0x2 | 0x4 | 0x8 | 0x10 | 0x40  # [2]
                self.bt_led_initialized = True
            else:
                outReport[3] = 0x1 | 0x2 | 0x4 | 0x10 | 0x40  # [2]

            outReport[4] = int(self.right_motor)  # right low freq motor 0-255 # [3]
            outReport[5] = int(self.left_motor)  # left low freq motor 0-255 # [4]

            # outReport[5] - outReport[8] audio related

            # set Micrphone LED, setting doesnt effect microphone settings
            outReport[10] = self.microphone_led  # [9]

            outReport[11] = 0x10 if self.microphone_mute is True else 0x00

            # add right trigger mode + parameters to packet
            outReport[12] = self.triggerR.mode.value
            outReport[13] = self.triggerR.forces[0]
            outReport[14] = self.triggerR.forces[1]
            outReport[15] = self.triggerR.forces[2]
            outReport[16] = self.triggerR.forces[3]
            outReport[17] = self.triggerR.forces[4]
            outReport[18] = self.triggerR.forces[5]
            outReport[21] = self.triggerR.forces[6]

            outReport[23] = self.triggerL.mode.value
            outReport[24] = self.triggerL.forces[0]
            outReport[25] = self.triggerL.forces[1]
            outReport[26] = self.triggerL.forces[2]
            outReport[27] = self.triggerL.forces[3]
            outReport[28] = self.triggerL.forces[4]
            outReport[29] = self.triggerL.forces[5]
            outReport[32] = self.triggerL.forces[6]

            outReport[40] = self.player_led.get_led_option()
            outReport[43] = self.player_led.get_pulse_options()
            outReport[44] = self.player_led.get_brightness()
            outReport[45] = self.player_led.get_player_id()
            outReport[46] = int(self.rgb_led.R * 255)
            outReport[47] = int(self.rgb_led.G * 255)
            outReport[48] = int(self.rgb_led.B * 255)

            crcChecksum = compute(outReport)

            outReport[74] = crcChecksum & 0x000000FF
            outReport[75] = (crcChecksum & 0x0000FF00) >> 8
            outReport[76] = (crcChecksum & 0x00FF0000) >> 16
            outReport[77] = (crcChecksum & 0xFF000000) >> 24

        return outReport
