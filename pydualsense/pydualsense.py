import logging
import os
import sys
from sys import platform

from pydualsense.models import DeviceOutputState, DeviceInputState

if platform.startswith("Windows") and sys.version_info >= (3, 8):
    os.add_dll_directory(os.getcwd())

import hidapi
from .enums import ConnectionType  # type: ignore
import threading

logger = logging.getLogger()
FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.INFO)


class pydualsense:
    report_thread: threading.Thread | None = None
    kill_thread: bool = False

    def __init__(self, verbose: bool = False) -> None:
        """
        initialise the library but dont connect to the controller. call :func:`init() <pydualsense.pydualsense.init>`
        to connect to the controller

        Args:
            verbose (bool, optional): display verbose out (debug prints of input and output). Defaults to False.
        """
        # TODO: maybe add a init function to not automatically allocate controller when class is declared
        self.verbose = verbose

        if self.verbose:
            logger.setLevel(logging.DEBUG)

        self.bt_led_initialized = False

        self.device: hidapi.Device = self.__find_device()

        self.input_state = DeviceInputState()  # controller states
        self.output_state = DeviceOutputState()  # controller states

        self.conType = self.determineConnectionType()  # determine USB or BT connection

        self.report_thread = threading.Thread(target=self.read_task, daemon=True)
        self.report_thread.start()

    def determineConnectionType(self) -> ConnectionType:
        """
        Determine the connection type of the controller. eg USB or BT.

        We ask the controller for an input report with a length up to 100 bytes
        and afterwords check the lenght of the received input report.
        The connection type determines the length of the report.

        This way of determining is not pretty but it works..

        Returns:
            ConnectionType: Detected connection type of the controller.
        """

        dummy_report = self.device.read(100)
        input_report_length = len(dummy_report)  # type: ignore

        if input_report_length == ConnectionType.USB.get_in_report_length():
            return ConnectionType.USB
        elif input_report_length == ConnectionType.BT.get_in_report_length():
            return ConnectionType.BT
        else:
            raise Exception("Could not determine connection type")

    def close(self) -> None:
        """
        Stops the report thread and closes the HID device
        """
        # TODO: reset trigger effect to default

        if self.report_thread:
            self.kill_thread = True

            self.report_thread.join()
            self.device.close()
            self.report_thread = None

    def __find_device(self) -> hidapi.Device:
        """
        find HID dualsense device and open it

        Raises:
            Exception: HIDGuardian detected
            Exception: No device detected

        Returns:
            hid.Device: returns opened controller device
        """
        # TODO: detect connection mode, bluetooth has a bigger write buffer
        # TODO: implement multiple controllers working
        if sys.platform.startswith("win32"):
            import pydualsense.hidguardian as hidguardian

            if hidguardian.check_hide():
                raise Exception(
                    "HIDGuardian detected. Delete the controller from HIDGuardian "
                    "and restart PC to connect to controller"
                )

        detected_device: hidapi.Device | None = None

        devices = hidapi.enumerate(vendor_id=0x054C)
        for device in devices:
            if device.vendor_id == 0x054C and device.product_id == 0x0CE6:
                detected_device = device

        if detected_device is None:
            raise Exception("No device detected")

        dual_sense = hidapi.Device(vendor_id=detected_device.vendor_id, product_id=detected_device.product_id)  # type: ignore
        return dual_sense

    def read_task(self) -> None:
        """background thread handling the reading of the device and updating its states"""
        while True:
            if self.kill_thread:
                break

            # read data from the input report of the controller
            inReport = self.device.read(self.conType.get_in_report_length())
            if self.verbose:
                logger.debug(inReport)

            assert isinstance(inReport, bytearray)

            # decrypt the packet and bind the inputs
            if self.conType == ConnectionType.BT:
                # the reports for BT and USB are structured the same,
                # but there is one more byte at the start of the bluetooth report.
                # We drop that byte, so that the format matches up again.
                self.input_state.from_state(inReport[1:])
            else:  # USB
                self.input_state.from_state(inReport)

            # prepare new report for device
            outReport = self.output_state.prepareReport(self.conType)

            # write the report to the device
            self.device.write(bytes(outReport))  # type: ignore
