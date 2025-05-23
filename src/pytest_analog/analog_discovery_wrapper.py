"""Wrapper for working with the digilent analog discovery functions"""

# NOTE: Waveforms software needs to be installed to use the wrapper (last tested version: 3.23.4 )
# NOTE: The wrapper has only been tested with "Analog Discovery 2, 3 / Analog Discovery Pro"

from ctypes import *  # noqa: F403
from .dwfconstants import *  # noqa: F403
import time
import sys
import logging
from typing import Optional, List, Dict, Tuple, Union
from enum import Enum
import numpy as np
import math
import multiprocessing as mp

logger = logging.getLogger("AnalogDiscovery-Wrapper")
logger.setLevel(logging.DEBUG)


class AnalogOutputSignal(Enum):
    """
    Enumeration of available analog output functions in Analog Discovery

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Sine = funcSine.value
    SinePower = funcSinePower.value
    DC = funcDC.value
    Square = funcSquare.value
    Triangle = funcTriangle.value
    RampUp = funcRampUp.value
    RampDown = funcRampDown.value
    Trapezium = funcTrapezium.value
    Noise = funcNoise.value
    Pulse = funcPulse.value
    Play = funcPlay.value
    Custom = funcCustom.value
    CustomPattern = funcCustomPattern.value
    PlayPattern = funcPlayPattern.value


class AnalogAcquisitionMode(Enum):
    """
    Enumeration of available acquisition modes in Analog Discovery

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Single = acqmodeSingle.value
    ScanShift = acqmodeScanShift.value
    ScanScreen = acqmodeScanScreen.value
    Record = acqmodeRecord.value
    Overs = acqmodeOvers.value
    Single1 = acqmodeSingle1.value


class AnalogFilter(Enum):
    """
    Enumeration of available analog acquisition filters for Analog Discovery

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    """Store every Nth ADC conversion, where N = ADC frequency /acquisition frequency"""
    Decimate = filterDecimate.value

    """Store the average of N ADC conversions"""
    Average = filterAverage.value

    """Store interleaved, the minimum and maximum values, of 2xN conversions"""
    MinMax = filterMinMax.value


class FFTWindow(Enum):
    """
    Enumeration of available window functions for FFT calculations

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    RECTANGLE = DwfWindowRectangular.value

    TRIANGLE = DwfWindowTriangular.value

    FLAT_TOP = DwfWindowFlatTop.value

    HAMMING = DwfWindowHamming.value

    COSINE = DwfWindowCosine.value

    BLACKMAN = DwfWindowBlackman.value

    KAISER = DwfWindowKaiser.value

    HANN = DwfWindowHann.value


class AnalogTriggerSource(Enum):
    """
    Enumeration of available triggers in Analog Discovery

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    NoneTrigger = trigsrcNone.value
    PC = trigsrcPC.value
    AnalogInDetector = trigsrcDetectorAnalogIn.value
    DigitalInDetector = trigsrcDetectorDigitalIn.value
    AnalogIn = trigsrcAnalogIn.value
    DigitalIn = trigsrcDigitalIn.value
    DigitalOut = trigsrcDigitalOut.value
    AnalogOut1 = trigsrcAnalogOut1.value
    AnalogOut2 = trigsrcAnalogOut2.value
    AnalogOut3 = trigsrcAnalogOut3.value
    AnalogOut4 = trigsrcAnalogOut4.value
    External1 = trigsrcExternal1.value
    External2 = trigsrcExternal2.value
    External3 = trigsrcExternal3.value
    External4 = trigsrcExternal4.value
    High = trigsrcHigh.value
    Low = trigsrcLow.value
    Clock = trigsrcClock.value


class AnalogTriggerType(Enum):
    """
    Enumeration of available trigger types in Analog Discovery

    This type is used by the AnalogIn instrument to specify the trigger type

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Edge = trigtypeEdge.value
    Pulse = trigtypePulse.value
    Transition = trigtypeTransition.value
    Window = trigtypeWindow.value


class AnalogCouplingType(Enum):
    """
    Enumeration of coupling types in Analog Discovery (AC, DC)

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    AC = DwfAnalogCouplingAC.value
    DC = DwfAnalogCouplingDC.value


class AnalogTriggerSlope(Enum):
    """
    Enumeration of available trigger slopes in Analog Discovery

    This type is used by the AnalogIn, AnalogOut, DigitalIn, and DigitalOut instruments to select
    the trigger slope

    In addition, the AnalogIn instrument uses it to select the slope of the sampling clock

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Rise = DwfTriggerSlopeRise.value
    """Rising trigger slope"""

    Fall = DwfTriggerSlopeFall.value
    """Falling trigger slope"""

    Either = DwfTriggerSlopeEither.value
    """Either rising or falling trigger slope"""


class AnalogOutputChannel(Enum):
    """Enumeration of Wave Gen (output) channels numbers for the Analog Discovery"""

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    WaveGen1 = c_int(0).value
    WaveGen2 = c_int(1).value


class AnalogOutputIdleState(Enum):
    """
    Enumeration type for Analog Output idle mode constants

    This type is used by the AnalogOut instrument to set the idle behavior of an output channel

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Disable = DwfAnalogOutIdleDisable.value
    """When idle, disable the output"""

    Offset = DwfAnalogOutIdleOffset.value
    """When idle, drive the configured analog output offset"""

    Init = DwfAnalogOutIdleInitial.value
    """When idle, drive the initial value of the selected waveform shape"""


class AnalogInputChannel(Enum):
    """Enumeration of Oscilloscope (input) channels numbers for the Analog Discovery"""

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    # NOTE: Analog Discovery 2 has 2 scope channels only
    # Analog Discovery Pro has 4 scope channels
    Channel1 = c_int(0).value
    Channel2 = c_int(1).value
    Channel3 = c_int(2).value
    Channel4 = c_int(3).value


class AnalogInstrumentState(Enum):
    """
    Enumeration of State machines of the Analog Discovery Instrument

    Refer to WaveForms SDK Reference Manual for more details

    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Ready = DwfStateReady.value
    Config = DwfStateConfig.value
    Prefill = DwfStatePrefill.value
    Armed = DwfStateArmed.value
    Wait = DwfStateWait.value
    Running = DwfStateRunning.value
    Triggered = DwfStateTriggered.value
    Done = DwfStateDone.value


class DigitalIOChannel(Enum):
    """Enumeration of digital channels (digital pin numbers)  of the Analog Discovery 2"""

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    DIO_0 = c_int(0).value
    DIO_1 = c_int(1).value
    DIO_2 = c_int(2).value
    DIO_3 = c_int(3).value
    DIO_4 = c_int(4).value
    DIO_5 = c_int(5).value
    DIO_6 = c_int(6).value
    DIO_7 = c_int(7).value
    DIO_8 = c_int(8).value
    DIO_9 = c_int(9).value
    DIO_10 = c_int(10).value
    DIO_11 = c_int(11).value
    DIO_12 = c_int(12).value
    DIO_13 = c_int(13).value
    DIO_14 = c_int(14).value
    DIO_15 = c_int(15).value


class DigitalOutputIdleState(Enum):
    """Enumeration type for Digital Output idle mode constants"""

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    Init = DwfDigitalOutIdleInit.value
    Low = DwfDigitalOutIdleLow.value
    High = DwfDigitalOutIdleHigh.value
    Zet = DwfDigitalOutIdleZet.value


class DwfError(Exception):
    """An empty exception class to categorize errors caused by the DWF API of WaveForms"""


class PyDwfError(DwfError):
    """PyDwfError exception class wraps an error caused by one the DWF API functions"""

    def __init__(self, code: Optional[int], msg: Optional[str]) -> None:
        super().__init__(self)
        self.error_code = code
        self.error_message = msg

    def __str__(self) -> str:
        if self.error_code is None:
            error_string = "An Error has occured during communication with Analog Device. DWF API Error Code: (unspecified)"
        else:
            error_string = "An Error has occured during communication with Analog Device. DWF API Error Code: ({})".format(
                self.error_code
            )
        if self.error_message is not None:
            error_string = "{}: {!r}".format(
                error_string, self.error_message.strip()
            )

        return error_string


# return code 1 indicates no error was returned from DWF API call
SUCCESS_RETURN_CODE = 1


def load_dwf_library():
    """Load dwf library to work with analog discovery devices"""
    if sys.platform.startswith("win"):
        logger.debug("Loading DWF Library from WaveForms SDK")
        dwf = cdll.dwf
    elif sys.platform.startswith("darwin"):
        dwf = cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
    else:
        dwf = cdll.LoadLibrary("libdwf.so")
    return dwf


class AnalogDiscoveryWrapper:
    """Wrapper class for analog discovery instruments from Diglient (based on DWF library)"""

    def __init__(self) -> None:
        """Initialize analog discovery wrapper"""
        self._dwf = load_dwf_library()
        self._hdwf = c_int()
        self._version = create_string_buffer(16)
        self._dwf.FDwfGetVersion(self._version)
        logger.debug(f"DWF Library Version:  {str(self._version.value)}")

    ### Private methods (for internal class/module use) ###
    def _get_auto_configure(self) -> int:
        """
        returns the AutoConfig setting in the device.
        See the function description for FDwfDeviceAutoConfigureSet for details on this setting.
        """
        c_auto_config = c_int()
        result = self._dwf.FDwfDeviceAutoConfigureGet(
            self._hdwf, byref(c_auto_config)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_auto_config.value

    def _disable_auto_configure(self) -> None:
        """
        Disables AutoConfig setting for the instrument
         -> the device will be configured only when calling FDwfAnalogOutConfigure
        """
        result = self._dwf.FDwfDeviceAutoConfigureSet(self._hdwf, c_int(0))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _enable_dynamic_auto_configure(self) -> None:
        """
        Enables dynamic AutoConfig setting for the instrument
        this allows dynamic adjustment of analog out settings like: frequency, amplitude

        Value for this option: 0 disable, 1 enable, 3 dynamic
        """
        result = self._dwf.FDwfDeviceAutoConfigureSet(self._hdwf, c_int(3))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _enable_analog_in_channel(self, channel_node: int) -> None:
        """
        Enables an analog input channel node (Oscilloscope channel)
        """
        result = self._dwf.FDwfAnalogInChannelEnableSet(
            self._hdwf, c_int(channel_node), c_int(1)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _disable_analog_in_channel(self, channel_node: int) -> None:
        """
        Disables an analog input channel node (Oscilloscope channel)
        """
        result = self._dwf.FDwfAnalogInChannelEnableSet(
            self._hdwf, c_int(channel_node), c_int(0)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_analog_input_range(
        self, channel_node: int, volts_range: float
    ) -> None:
        """
        Configures the range for an Analog In channel
        With channel_node = -1, each enabled Analog In channel range
        will be configured to the same, new value
        """
        result = self._dwf.FDwfAnalogInChannelRangeSet(
            self._hdwf, c_int(channel_node), c_double(volts_range)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_range(self, channel_node: int) -> float:
        """
        Gets the real range value for the given channel for an Analog In channel
        """
        c_range = c_double()
        result = self._dwf.FDwfAnalogInChannelRangeGet(
            self._hdwf, c_int(channel_node), byref(c_range)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_range.value

    def _set_analog_input_offset(
        self, channel_node: int, volts_offset: float
    ) -> None:
        """
        Configures the offset for an Analog In channel
        With channel_node = -1, each enabled AnalogIn
        channel offset will be configured to the same level
        """
        result = self._dwf.FDwfAnalogInChannelOffsetSet(
            self._hdwf, c_int(channel_node), c_double(volts_offset)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_offset(self, channel_node: int) -> float:
        """
        Gets the real offset level for a given AnalogIn channel
        """
        c_offset = c_double()
        result = self._dwf.FDwfAnalogInChannelOffsetGet(
            self._hdwf, c_int(channel_node), byref(c_offset)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_offset.value

    def _set_analog_input_acquisition_mode(
        self, acquisition_mode: int
    ) -> None:
        """Sets the acquisition mode for analog inputs to the instrument"""
        result = self._dwf.FDwfAnalogInAcquisitionModeSet(
            self._hdwf, c_int(acquisition_mode)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_acquisition_mode(self) -> AnalogAcquisitionMode:
        """Gets the current acquisition mode for analog inputs to the instrument"""
        c_acq_mode = c_int()
        result = self._dwf.FDwfAnalogInAcquisitionModeGet(
            self._hdwf, byref(c_acq_mode)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogAcquisitionMode(c_acq_mode.value)

    def _set_analog_input_sampling_frequency(
        self, hz_frequency: float
    ) -> None:
        """Sets the sample frequency for the analog inputs to the instruments"""
        result = self._dwf.FDwfAnalogInFrequencySet(
            self._hdwf, c_double(hz_frequency)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_sampling_frequency(self) -> float:
        """Gets the configured sample frequency for the analog inputs to the instruments"""
        c_frequency = c_double()
        result = self._dwf.FDwfAnalogInFrequencyGet(
            self._hdwf, byref(c_frequency)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_frequency.value

    def _set_analog_input_record_length(self, sec_length: float) -> None:
        """Sets the Record length in seconds. With length of zero, the record will run indefinitely"""
        result = self._dwf.FDwfAnalogInRecordLengthSet(
            self._hdwf, c_double(sec_length)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_record_length(self) -> float:
        """Gets the currently set Record length in seconds"""
        c_length = c_double()
        result = self._dwf.FDwfAnalogInRecordLengthGet(
            self._hdwf, byref(c_length)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_length.value

    def _set_analog_input_trigger_position(self, sec_position: float) -> None:
        """Sets the horizontal trigger position in seconds"""
        result = self._dwf.FDwfAnalogInTriggerPositionSet(
            self._hdwf, c_double(sec_position)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_trigger_position(self) -> float:
        """Gets the configured trigger position in seconds"""
        c_position = c_double()
        result = self._dwf.FDwfAnalogInTriggerPositionGet(
            self._hdwf, byref(c_position)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_position.value

    def _set_analog_input_trigger_source(
        self, trigger_source: int, sec_timeout: float
    ) -> None:
        """
        Configures the Analog In acquisition trigger source and its timeout
        To have auto trigger set trigger_source to something other than AnalogTriggerSource.NoneTrigger.value
        and sec_timeout to value greater than zero

        """
        r1 = self._dwf.FDwfAnalogInTriggerAutoTimeoutSet(
            self._hdwf, c_double(sec_timeout)
        )
        r2 = self._dwf.FDwfAnalogInTriggerSourceSet(
            self._hdwf, c_ubyte(trigger_source)
        )

        if r1 != SUCCESS_RETURN_CODE or r2 != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_trigger_source(self) -> AnalogTriggerSource:
        """
        Gets the configured trigger source. The trigger source can be “none” or an internal instrument or
        external trigger
        """
        c_trigger = c_ubyte()
        result = self._dwf.FDwfAnalogInTriggerSourceGet(
            self._hdwf, byref(c_trigger)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogTriggerSource(c_trigger.value)

    def _set_analog_input_trigger_type(
        self, trigger_type: AnalogTriggerType
    ) -> None:
        """Sets the trigger type for the analog in instrument"""
        result = self._dwf.FDwfAnalogInTriggerTypeSet(
            self._hdwf, c_int(trigger_type.value)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_trigger_type(self) -> AnalogTriggerType:
        """Gets the current trigger type for the analog in instrument"""
        c_trig_type = c_int()
        result = self._dwf.FDwfAnalogInTriggerTypeGet(
            self._hdwf, byref(c_trig_type)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogTriggerType(c_trig_type.value)

    def _set_analog_input_trigger_level(self, trigger_level: float) -> None:
        """Sets the analog input trigger voltage level in Volts"""
        result = self._dwf.FDwfAnalogInTriggerLevelSet(
            self._hdwf, c_double(trigger_level)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_analog_input_trigger_hysteresis(
        self, hysteresis_level: float
    ) -> None:
        """Sets the analog input trigger hysteresis level in Volts"""
        result = self._dwf.FDwfAnalogInTriggerHysteresisSet(
            self._hdwf, c_double(hysteresis_level)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_trigger_level(self) -> float:
        """Gets the current analog input trigger voltage level in Volts"""
        c_trig_level = c_double()
        result = self._dwf.FDwfAnalogInTriggerLevelGet(
            self._hdwf, byref(c_trig_level)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return float(c_trig_level.value)

    def _set_analog_input_trigger_condition(
        self, trigger_condition: AnalogTriggerSlope
    ) -> None:
        """Sets the trigger condition for the analog in instrument"""
        result = self._dwf.FDwfAnalogInTriggerConditionSet(
            self._hdwf, c_int(trigger_condition.value)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_trigger_condition(self) -> AnalogTriggerSlope:
        """Gets the current trigger condition for the analog in instrument"""
        c_trig_cond = c_int()
        result = self._dwf.FDwfAnalogInTriggerConditionGet(
            self._hdwf, byref(c_trig_cond)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogTriggerSlope(c_trig_cond.value)

    def _set_analog_input_trigger_channel(
        self, trigger_channel: AnalogInputChannel
    ) -> None:
        """Sets the trigger channel for the analog in instrument"""
        result = self._dwf.FDwfAnalogInTriggerChannelSet(
            self._hdwf, c_int(trigger_channel.value)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_trigger_channel(self) -> AnalogInputChannel:
        """Gets the current trigger channel for the analog in instrument"""
        c_trig_ch = c_int()
        result = self._dwf.FDwfAnalogInTriggerChannelGet(
            self._hdwf, byref(c_trig_ch)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogInputChannel(c_trig_ch.value)

    def _set_analog_input_filter(
        self, channel_node: int, channel_filter: AnalogFilter
    ) -> None:
        """
        Sets the acquisition filter for a specified AnalogIn input channel
        """
        result = self._dwf.FDwfAnalogInChannelFilterSet(
            self._hdwf, c_int(channel_node), c_int(channel_filter.value)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_filter(self, channel_node: int) -> AnalogFilter:
        """
        Gets the currently selected acquisition filter for a specified AnalogIn input channel
        """
        c_filter = c_int()
        result = self._dwf.FDwfAnalogInChannelFilterGet(
            self._hdwf, c_int(channel_node), byref(c_filter)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogFilter(c_filter.value)

    def _set_analog_input_buffer_size(self, buffer_size: int) -> None:
        """
        Sets the AnalogIn instrument buffer size
        """
        result = self._dwf.FDwfAnalogInBufferSizeSet(
            self._hdwf, c_int(buffer_size)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_buffer_size(self) -> int:
        """
        Gets the used AnalogIn instrument buffer size
        """
        c_buffer_size = c_int()
        result = self._dwf.FDwfAnalogInBufferSizeGet(
            self._hdwf, byref(c_buffer_size)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_buffer_size.value

    def _get_analog_input_buffer_size_info(self) -> Tuple[int, int]:
        """
        Gets the the minimum and maximum buffer size for the AnalogIn instrument
        """
        c_min_buffer_size = c_int()
        c_max_buffer_size = c_int()

        result = self._dwf.FDwfAnalogInBufferSizeInfo(
            self._hdwf, byref(c_min_buffer_size), byref(c_max_buffer_size)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return (c_min_buffer_size.value, c_max_buffer_size.value)

    def _start_analog_input(self, reset_auto_trigger_timeout: bool) -> None:
        """Configures the instrument and start the acquisition on enabled Analog In channels"""
        result = self._dwf.FDwfAnalogInConfigure(
            self._hdwf, c_int(reset_auto_trigger_timeout), c_int(1)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _stop_analog_input(self, reset_auto_trigger_timeout: bool) -> None:
        """Configures the instrument and stop the acquisition on enabled Analog In channels"""
        result = self._dwf.FDwfAnalogInConfigure(
            self._hdwf, c_int(reset_auto_trigger_timeout), c_int(0)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _reset_analog_input_config(self) -> None:
        """Resets all AnalogIn instrument parameters to default values"""
        result = self._dwf.FDwfAnalogInReset(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_input_status(self, read_data: bool = True) -> int:
        """
        Checks the state of the acquisition (also polls and reads all information from the Scope instrument)
        To read the data from the device, set read_data to True
        For single acquisition mode, the data will be read only when the acquisition is finished
        """
        read_state = c_ubyte(0)
        result = self._dwf.FDwfAnalogInStatus(
            self._hdwf, c_int(read_data), byref(read_state)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        return read_state.value

    def _get_analog_input_status_sample(self, channel_node: int) -> float:
        """
        Gets the last ADC conversion sample from the specified channel_node on the AnalogIn instrument

        """
        c_sample_reading = c_double()
        result = self._dwf.FDwfAnalogInStatusSample(
            self._hdwf, c_int(channel_node), byref(c_sample_reading)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        return c_sample_reading.value

    def _get_analog_input_valid_samples(self) -> int:
        """
        Retrieves the number of valid/acquired data samples
        """
        valid_samples = c_int(0)
        result = self._dwf.FDwfAnalogInStatusSamplesValid(
            self._hdwf, byref(valid_samples)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        return valid_samples.value

    def _get_analog_input_record_status(self) -> Tuple[int, int, int]:
        """
        Retrieves information about the recording process.

        The data loss occurs when the device acquisition is faster than the read process to PC.
        In this case, the device recording buffer is filled and data samples are overwritten.

        Corrupt samples indicate that the samples have been overwritten by the
        acquisition process during the previous read.

        In this case, try optimizing the loop process for faster  execution or reduce the acquisition frequency or record length
        to be less than or equal to the device buffer size (record length <= buffer size/frequency)
        """
        # status values to be filled with record status
        c_data_available = c_int()
        c_data_lost = c_int()
        c_data_corrupt = c_int()

        result = self._dwf.FDwfAnalogInStatusRecord(
            self._hdwf,
            byref(c_data_available),
            byref(c_data_lost),
            byref(c_data_corrupt),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        data_available = c_data_available.value
        data_lost = c_data_lost.value
        data_corrupt = c_data_corrupt.value

        return (data_available, data_lost, data_corrupt)

    def _get_analog_input_record_data(
        self, channel: int, count: int
    ) -> np.ndarray:
        """
        Gets the acquired data samples from the specified AnalogIn instrument channel.

        This method returns samples as voltages, calculated from the raw, binary sample values as follows:

        .. code-block:: python

            voltages = analogIn.channelOffsetGet(channel_index) + \\
                       analogIn.channelRangeGet(channel_index) * (raw_samples / 65536.0)
        """
        analog_data_samples = np.empty(count, dtype=np.float64)

        analog_data_samples_ptr = analog_data_samples.ctypes.data_as(
            POINTER(c_double)
        )

        result = self._dwf.FDwfAnalogInStatusData(
            self._hdwf, c_int(channel), analog_data_samples_ptr, c_int(count)
        )

        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return analog_data_samples

    def _enable_analog_out_channel(self, channel_node: int) -> None:
        """
        Enables an analog output channel node (WaveGen channel)
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutNodeEnableSet(
            self._hdwf, c_int(channel_node), AnalogOutNodeCarrier, c_int(1)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _disable_analog_out_channel(self, channel_node: int) -> None:
        """
        Disables an analog output channel node (WaveGen channel)
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutNodeEnableSet(
            self._hdwf, c_int(channel_node), AnalogOutNodeCarrier, c_int(0)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_analog_output_generator_function(
        self, channel_node: int, generator_function: int
    ) -> None:
        """
        Sets the generator output function for the specified channel
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutNodeFunctionSet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            c_ubyte(generator_function),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_generator_function(
        self, channel_node: int
    ) -> AnalogOutputSignal:
        """
        Gets the current generator function option for the specified instrument channel
        """
        c_func = c_ubyte()
        result = self._dwf.FDwfAnalogOutNodeFunctionGet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            byref(c_func),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogOutputSignal(c_func.value)

    def _set_analog_output_frequency(
        self, channel_node: int, frequency_hz: float
    ) -> None:
        """
        Sets the analog output signal frequency for the specified channel
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutNodeFrequencySet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            c_double(frequency_hz),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_frequency(self, channel_node: int) -> float:
        """
        Gets the currently set frequency for the specified analog output channel
        """
        c_frequency = c_double()
        result = self._dwf.FDwfAnalogOutNodeFrequencyGet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            byref(c_frequency),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_frequency.value

    def _set_analog_output_amplitude(
        self, channel_node: int, amplitude_volts: float
    ) -> None:
        """
        Sets the analog output signal amplitude or modulation index for the specified channel
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutNodeAmplitudeSet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            c_double(amplitude_volts),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_amplitude(self, channel_node: int) -> float:
        """
        Gets the currently set amplitude or modulation index for the specified channel
        """
        c_amplitude = c_double()
        result = self._dwf.FDwfAnalogOutNodeAmplitudeGet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            byref(c_amplitude),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_amplitude.value

    def _set_analog_output_offset(
        self, channel_node: int, offset_volts: float
    ) -> None:
        """
        Sets the analog output signal offset value for the specified channel
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutNodeOffsetSet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            c_double(offset_volts),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_offset(self, channel_node: int) -> float:
        """
        Gets the current offset value for the specified channel
        """
        c_offset = c_double()
        result = self._dwf.FDwfAnalogOutNodeOffsetGet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            byref(c_offset),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_offset.value

    def _set_analog_output_symmetry(
        self, channel_node: int, percentage_symmetry: float
    ) -> None:
        """
        Sets the symmetry (or duty cycle) for the specified channel-node on the instrument. With channel
        index -1, each enabled Analog Out channel symmetry will be configured to use the same, new
        option.
        """
        result = self._dwf.FDwfAnalogOutNodeSymmetrySet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            c_double(percentage_symmetry),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_symmetry(self, channel_node: int) -> float:
        """
        Gets the current symmetry percentage (duty cycle) for the specified channel
        """
        c_symmetry = c_double()
        result = self._dwf.FDwfAnalogOutNodeSymmetryGet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            byref(c_symmetry),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_symmetry.value

    def _set_analog_output_data(
        self, channel_node: int, data: np.ndarray
    ) -> None:
        """
        Set the custom data or to prefill the buffer with play samples. The samples are double precision
        floating point values normalized to ±1.
        With the custom function option, the data samples: len(data) will be interpolated to the device buffer
        size. The output value will be Offset + Sample*Amplitude, for instance:
            0 value sample will output: Offset.
            +1 value sample will output: Offset + Amplitude.
            -1 value sample will output: Offset – Amplitude.
        NOTE: used with play and custom wavegen functions
        """
        # get analog out minimum and maximum number of samples allowed for custom data generation
        c_samples_min = c_int()
        c_samples_max = c_int()
        result = self._dwf.FDwfAnalogOutNodeDataInfo(
            self._hdwf,
            channel_node,
            AnalogOutNodeCarrier,
            byref(c_samples_min),
            byref(c_samples_max),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # convert to double precision
        double_precision_data = data.astype(np.float64)

        # ctype pointer to custom data
        c_buffer_data = double_precision_data.ctypes.data_as(POINTER(c_double))

        # TODO : CHECK if this is better alternative to declate c_data
        # data_length = double_precision_data.size
        # c_buffer_data = (c_double * data_length)()
        # for index in range(0, len(c_buffer_data)):
        #     c_buffer_data[index] = c_double(double_precision_data[index])

        # if maximum buffer size is greater than loaded data -> then set number of samples to size of data
        c_buffer_data_size = c_int(c_samples_max.value)
        if c_samples_max.value > len(double_precision_data):
            c_buffer_data_size.value = len(double_precision_data)

        result = self._dwf.FDwfAnalogOutNodeDataSet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            c_buffer_data,
            c_buffer_data_size,
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_analog_output_phase(
        self, channel_node: int, degree_phase: float
    ) -> None:
        """
        Sets the analog output signal phase angle (in degrees) for the specified channel
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutNodePhaseSet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            c_double(degree_phase),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_phase(self, channel_node: int) -> float:
        """
        Gets the current phase angle (in degrees) for the specified channel
        """
        c_phase = c_double()
        result = self._dwf.FDwfAnalogOutNodePhaseGet(
            self._hdwf,
            c_int(channel_node),
            AnalogOutNodeCarrier,
            byref(c_phase),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_phase.value

    def _set_analog_output_run_duration(
        self, channel_node: int, duration_sec: float
    ) -> None:
        """
        Sets the run length for the instrument in Seconds
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutRunSet(
            self._hdwf, c_int(channel_node), c_double(duration_sec)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_run_duration(self, channel_node: int) -> float:
        """
        Gets the configured run length for the instrument in Seconds for the specified channel
        """
        c_duration = c_double()
        result = self._dwf.FDwfAnalogOutRunGet(
            self._hdwf, c_int(channel_node), byref(c_duration)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_duration.value

    def _set_analog_output_wait_duration(
        self, channel_node: int, duration_sec: float
    ) -> None:
        """
        Sets the wait length for the channel on instrument
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutWaitSet(
            self._hdwf, c_int(channel_node), c_double(duration_sec)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_wait_duration(self, channel_node: int) -> float:
        """
        Gets the current wait length in Seconds for the specified channel
        """
        c_duration = c_double()
        result = self._dwf.FDwfAnalogOutWaitGet(
            self._hdwf, c_int(channel_node), byref(c_duration)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_duration.value

    def _set_analog_output_repeats_count(
        self, channel_node: int, repeat_count: int
    ) -> None:
        """
        Sets the repeat count
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutRepeatSet(
            self._hdwf, c_int(channel_node), c_int(repeat_count)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_repeats_count(self, channel_node: int) -> int:
        """
        Gets the current repeat count for the specified channel
        """
        c_count = c_int()
        result = self._dwf.FDwfAnalogOutRepeatGet(
            self._hdwf, c_int(channel_node), byref(c_count)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return c_count.value

    def _set_analog_output_trigger_source(
        self, channel_node: int, trigger_source: int
    ) -> None:
        """
        Sets the trigger source for the channel on instrument
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutTriggerSourceSet(
            self._hdwf, c_int(channel_node), c_ubyte(trigger_source)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_trigger_source(
        self, channel_node: int
    ) -> AnalogTriggerSource:
        """
        Gets the current trigger source setting for the specified channel
        """
        c_trigger = c_ubyte()
        result = self._dwf.FDwfAnalogOutTriggerSourceGet(
            self._hdwf, c_int(channel_node), byref(c_trigger)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogTriggerSource(c_trigger.value)

    def _set_analog_output_trigger_slope(
        self, channel_node: int, trigger_slope: int
    ) -> None:
        """
        Sets the trigger slope for the channel on instrument
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutTriggerSlopeSet(
            self._hdwf, c_int(channel_node), c_int(trigger_slope)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message
            )

    def _get_analog_output_trigger_slope(
        self, channel_node: int
    ) -> AnalogTriggerSlope:
        """
        Gets the trigger slope for the channel on instrument
        """
        c_slope = c_int()
        result = self._dwf.FDwfAnalogOutTriggerSlopeGet(
            self._hdwf, c_int(channel_node), byref(c_slope)
        )

        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message
            )

        return AnalogTriggerSlope(c_slope.value)

    def _set_analog_output_idle_state(
        self, channel_node: int, idle_state: int
    ) -> None:
        """
        Sets idle output state of analog output channel while not running (i.e. in Ready, Stopped, Done, or Wait states)

        """
        result = self._dwf.FDwfAnalogOutIdleSet(
            self._hdwf, c_int(channel_node), c_int(idle_state)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message
            )

    def _get_analog_output_idle_state(
        self, channel_node: int
    ) -> AnalogOutputIdleState:
        """Gets the generator idle output option for the specified analog output channel"""
        c_idle_state = c_int()
        result = self._dwf.FDwfAnalogOutIdleGet(
            self._hdwf, c_int(channel_node), byref(c_idle_state)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message
            )

        return AnalogOutputIdleState(c_idle_state.value)

    def _start_analog_output(self, channel_node: int) -> None:
        """
        Configures and/or Starts the analog output from the instrument for the specified channel
        With channel_node = -1, each enabled Analog Out channel will be configured
        """
        result = self._dwf.FDwfAnalogOutConfigure(
            self._hdwf, c_int(channel_node), c_int(1)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _stop_analog_output(self, channel_node: int) -> None:
        """
        Stops the analog output from the instrument for the specified channel
        With channel_node = -1, each enabled Analog Out channel will be configured
        """
        result = self._dwf.FDwfAnalogOutConfigure(
            self._hdwf, c_int(channel_node), c_int(0)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _reset_analog_output_config(self, channel_node: int) -> None:
        """
        Resets analog output parameters to default values for the specified channel.
        To reset instrument parameters across all channels, set channel_node to -1
        """
        result = self._dwf.FDwfAnalogOutReset(self._hdwf, c_int(channel_node))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_analog_output_status(self, channel_node: int) -> int:
        """
        Gets the state of the instrument at an analog output channel
        (also polls and reads all information from the WaveGen instrument)
        """
        read_state = c_ubyte(0)
        result = self._dwf.FDwfAnalogOutStatus(
            self._hdwf, c_int(channel_node), byref(read_state)
        )
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )
        return read_state.value

    def _get_analog_output_repeat_status(self, channel_node: int) -> int:
        """
        Gets the remaining repeat counts. It only returns information from the last FDwfAnalogOutStatus
        function call, it does not read dreictly from the device
        """
        c_repeats_count = c_int()
        result = self._dwf.FDwfAnalogOutRepeatStatus(
            self._hdwf, c_int(channel_node), byref(c_repeats_count)
        )
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )
        return c_repeats_count.value

    def _verify_channels_enable_status(
        self, channels: List[Union[AnalogOutputChannel, AnalogInputChannel]]
    ) -> None:
        """Verfiy list of given analog in / out channels are enabled"""
        for ch in channels:
            state = self.get_analog_channel_enable_state(ch)
            if state != 1:
                raise RuntimeError(
                    f"channel: {ch}:{ch.value} is not enabled. make sure the required channels are enabled"
                )

    def _reset_analog_io_config(self) -> None:
        """
        Resets and configures (by default, having auto configure enabled) all AnalogIO instrument parameters
        to default values
        """
        result = self._dwf.FDwfAnalogIOReset(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _reset_digital_output_config(self) -> None:
        """
        Resets and configures (by default, having auto configure enabled) all the instrument parameters to
        default values
        """
        result = self._dwf.FDwfDigitalOutReset(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _reset_digital_input_config(self) -> None:
        """
        Resets and configures (by default, having auto configure enabled) all DigitalIn instrument parameters
        to default values.
        """
        result = self._dwf.FDwfDigitalInReset(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _reset_digital_io_config(self) -> None:
        """
        Resets and configures (by default, having auto configure enabled) all DigitalIO instrument parameters
        to default values. It sets the output enables to zero (tri-state), output value to zero, and configures
        the DigitalIO instrument
        """
        result = self._dwf.FDwfDigitalIOReset(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_i2c_timeout(self, timeout_sec: float) -> None:
        """Sets the I2C timeout in seconds"""
        result = self._dwf.FDwfDigitalI2cTimeoutSet(
            self._hdwf, c_double(timeout_sec)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_i2c_scl(self, channel: int) -> None:
        """Sets the DIO channel to use for I2C clock"""
        result = self._dwf.FDwfDigitalI2cSclSet(self._hdwf, c_int(channel))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_i2c_sda(self, channel: int) -> None:
        """Sets the DIO channel to use for I2C data"""
        result = self._dwf.FDwfDigitalI2cSdaSet(self._hdwf, c_int(channel))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_i2c_rate(self, rate: float) -> None:
        """Sets the I2C data rate. also enable clock stretching"""
        r1 = self._dwf.FDwfDigitalI2cStretchSet(
            self._hdwf, c_int(1)
        )  # clock stretching enabled
        r2 = self._dwf.FDwfDigitalI2cRateSet(self._hdwf, c_double(rate))
        if r1 != SUCCESS_RETURN_CODE or r2 != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_i2c_nak_read_state(self, Nak_Last_Read_Byte: int = 1) -> None:
        """
        Specifies if the last read byte should be acknowledged or not. The I2C specifications require NAK, this
        parameter set to true by default.
        """
        result = self._dwf.FDwfDigitalI2cReadNakSet(
            self._hdwf, c_int(Nak_Last_Read_Byte)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _get_i2c_spy_status(
        self, max_data_size: int
    ) -> Tuple[int, int, List[int], int]:
        """
        Get I2C spy status

        Args:
            max_data_size: maximum number of bytes to decode

        Returns:
        Tuple[int, int, List[int], int]: A tuple (start, stop, data-values, nak-indicator).

        """
        c_start = c_int()
        c_stop = c_int()
        c_data = (c_ubyte * max_data_size)()
        c_data_size = c_int(max_data_size)
        iNak = c_int()

        state = self._dwf.FDwfDigitalI2cSpyStatus(
            self._hdwf,
            byref(c_start),
            byref(c_stop),
            byref(c_data),
            byref(c_data_size),
            byref(iNak),
        )
        if state == 0:
            logger.error("Communication with the device failed")
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        data_list = list(c_data)[
            : c_data_size.value
        ]  # Only return the first 'c_data_size' bytes.

        return (c_start.value, c_stop.value, data_list, iNak.value)

    def _clear_i2c_bus(self) -> None:
        """
        Verifies and tries to solve eventual bus lockup
        The argument returns true, non-zero value if the bus is free
        """
        iNak = c_int()
        result = self._dwf.FDwfDigitalI2cClear(self._hdwf, byref(iNak))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        if iNak.value == 0:
            raise RuntimeError(
                "I2C bus error. Check the I2C pin(s) / pull-up(s) configuration"
            )

    def _set_spi_frequency(self, clk_frequency: float) -> None:
        """
        Sets the SPI clock frequency in Hz
        """
        result = self._dwf.FDwfDigitalSpiFrequencySet(
            self._hdwf, c_double(clk_frequency)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_spi_scl(self, channel: int) -> None:
        """
        Sets the DIO channel to use for SPI clock
        """
        result = self._dwf.FDwfDigitalSpiClockSet(self._hdwf, c_int(channel))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_spi_cs(self, channel: int, cs_state: int) -> None:
        """
        Sets and Controls the SPI CS signal(s)
        Args:
            channel: DIO channel to use for CS
            cs_state: Set the chip select level: 0 low, 1 high, -1 release (Z, high impedance)
        """
        result = self._dwf.FDwfDigitalSpiSelect(
            self._hdwf, c_int(channel), c_int(cs_state)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_spi_data(self, channel: int, spi_data_bit: int) -> None:
        """
        Sets the DIO channel to use for a given SPI data bit
        Args:
            spi_data_bit: specify data index to set, 0 = DQ0_MOSI_SISO, 1 = DQ1_MISO, 2 = DQ2, 3 = DQ3
        """
        result = self._dwf.FDwfDigitalSpiDataSet(
            self._hdwf, c_int(spi_data_bit), c_int(channel)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_spi_idle_state(self, spi_data_bit: int, idle_mode: int) -> None:
        """
        Sets the idle behavior for an SPI data bit

        it specifies the DQ singal idle output state. DQ2 and 3 may be used for alternative purpose like for write
        protect (should driven low) or for hold (should be in high impendance).

        Args:
            spi_data_bit: data index to configure:
                0 — DQ0 / MOSI / SISO
                1 — DQ1 / MISO
                2 — DQ2
                3 — DQ3

            idle_mode: The idle behavior of spi_data_bit
        """
        result = self._dwf.FDwfDigitalSpiIdleSet(
            self._hdwf, c_int(spi_data_bit), c_int(idle_mode)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_spi_mode(self, spi_mode: int) -> None:
        """
        Sets the SPI mode

        Args:
            spi_mode: The values for CPOL (polarity) and CPHA (phase) to use with the attached slave device:
            0 — CPOL = 0, CPHA = 0
            1 — CPOL = 0, CPHA = 1
            2 — CPOL = 1, CPHA = 0
            3 — CPOL = 1, CPHA = 1

            Refer to the slave device's datasheet to select the correct value
        """
        result = self._dwf.FDwfDigitalSpiModeSet(self._hdwf, c_int(spi_mode))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def _set_spi_endianness(self, bit_order: int) -> None:
        """
        Sets the bit order for SPI data

        Args:
            bit_order: 1: MSB first, 0: LSB first
        """
        result = self._dwf.FDwfDigitalSpiOrderSet(self._hdwf, c_int(bit_order))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    ## Device connection /info / error methods ###
    def open_connection(self, config_index: Optional[int] = None) -> None:
        """Open connection to first analog discovery device with optional configruation"""
        # NOTE: c_int(-1) -> enumerate all connected devices and open the first discovered device
        # config_index is zero based (e.g. to select 1st configuration config_index=0)
        if not config_index:
            logger.info(
                "Opening connection to first analog discovery device ..."
            )
            self._dwf.FDwfDeviceOpen(c_int(-1), byref(self._hdwf))
        else:
            logger.info(
                f"Opening connection to first analog discovery device with configuration index: {config_index} ..."
            )
            self._dwf.FDwfDeviceConfigOpen(
                c_int(-1), c_int(int(config_index)), byref(self._hdwf)
            )

        if self._hdwf.value == hdwfNone.value:
            logger.error(
                "Failed to open connection to analog discovery device. Make sure it is connected and not used by the system"
            )
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def close_connection(self) -> None:
        """Close connection to connected analog discovery device"""
        logger.info("Closing connection to analog discovery device")
        result = self._dwf.FDwfDeviceClose(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def get_devices_info(self) -> Union[List[Dict], None]:
        """
        Get connected devices info

        Builds an internal list of detected devices filtered by the enumfilter parameter.
        It must be called before using other FDwfEnum functions because they obtain information about enumerated devices
        from this list identified by the device index
        """
        devices = []
        c_devices_count = c_int()
        result = self._dwf.FDwfEnum(enumfilterAll, byref(c_devices_count))

        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

        if c_devices_count.value == 0:
            logger.error("No Analog Discovery Devices were detected")
            return None

        # declare buffer variables to store devices info
        id = c_int()
        rev = c_int()
        name_buffer = create_string_buffer(64)
        sn_buffer = create_string_buffer(16)

        for i_device in range(0, c_devices_count.value):
            self._dwf.FDwfEnumDeviceType(
                c_int(i_device), byref(id), byref(rev)
            )
            self._dwf.FDwfEnumDeviceName(c_int(i_device), name_buffer)
            self._dwf.FDwfEnumSN(c_int(i_device), sn_buffer)

            devices.append(
                {
                    "Device": i_device,
                    "Name": str(name_buffer.value.decode()),
                    "SN.": str(sn_buffer.value.decode()),
                    "ID": str(id.value),
                    "Rev": chr(0x40 + (rev.value & 0xF))
                    + " "
                    + hex(rev.value),
                }
            )

        return devices

    def get_device_config_info(self, device_index: int) -> List[Dict]:
        """
        Builds an internal list of detected configurations for the selected device.
        The function above must becalled before using other FDwfEnumConfigInfo function
        because this obtains information about configurations from this list identified
        by the configuration index
        """
        c_config = c_int()  # config enumerator
        configs = []  # list to store config_info(s)
        c_info = c_int()
        result = self._dwf.FDwfEnumConfig(c_int(device_index), byref(c_config))

        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

        for i_config in range(0, c_config.value):
            config_info = {}  # device config

            # DECIAnalogInChannelCount
            self._dwf.FDwfEnumConfigInfo(
                c_int(i_config), c_int(1), byref(c_info)
            )
            config_info["AnalogIn Channel Count"] = c_info.value

            # DECIAnalogInBufferSize
            self._dwf.FDwfEnumConfigInfo(
                c_int(i_config), c_int(7), byref(c_info)
            )
            config_info["AnalogIn Buffer size"] = c_info.value

            # DECIAnalogOutChannelCount
            self._dwf.FDwfEnumConfigInfo(
                c_int(i_config), c_int(2), byref(c_info)
            )
            config_info["AnalogOut Channel Count"] = c_info.value

            # DECIAnalogOutBufferSize
            self._dwf.FDwfEnumConfigInfo(
                c_int(i_config), c_int(8), byref(c_info)
            )
            config_info["AnalogOut Buffer Size"] = c_info.value

            # DECIDigitalInChannelCount
            self._dwf.FDwfEnumConfigInfo(
                c_int(i_config), c_int(4), byref(c_info)
            )
            config_info["DigitalIn Channel Count"] = c_info.value

            # DECIDigitalInBufferSize
            self._dwf.FDwfEnumConfigInfo(
                c_int(i_config), c_int(9), byref(c_info)
            )
            config_info["DigitalIn Buffer Size"] = c_info.value

            # DECIDigitalOutChannelCount
            self._dwf.FDwfEnumConfigInfo(
                c_int(i_config), c_int(5), byref(c_info)
            )
            config_info["DigitalOut Channel Count"] = c_info.value

            # DECIDigitalOutBufferSize
            self._dwf.FDwfEnumConfigInfo(
                c_int(i_config), c_int(10), byref(c_info)
            )
            config_info["DigitalOut Buffer Size"] = c_info.value

            configs.append(config_info)

        logger.info(
            f"Device Index: {device_index} has: {len(configs)} available configurations"
        )

        return configs

    def get_adc_bits_info(self) -> None:
        """
        Gets the fixed the number of bits used by the Analog Input ADC
        for the Analog Discovery 2, this method always returns 14
        """
        c_num_bits = c_int()
        result = self._dwf.FDwfAnalogInBitsInfo(self._hdwf, byref(c_num_bits))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        return c_num_bits.value

    def get_last_error(self) -> int:
        """
        Retrieves the last error code in the calling process.
        The error code is cleared when other API functions
        are called and is only set when an API function fails during execution.
        Error codes are declared in dwfconstants.py

        """
        dwf_error_code = c_int()
        self._dwf.FDwfGetLastError(byref(dwf_error_code))
        return dwf_error_code.value

    def get_last_error_message(self) -> str:
        """
        Retrieves the last error message. This may consist of a chain of messages, separated by a new line
        character, that describe the events leading to the failure.
        """
        c_error_msg = create_string_buffer(512)
        self._dwf.FDwfGetLastErrorMsg(byref(c_error_msg))
        return c_error_msg.value.decode()

    ## Instruments reset methods ###
    def reset_analog_instrument(self) -> None:
        """Resets/Reconfigure all analog instrument parameters to their default values"""
        logger.info(
            "Reseting all Analog Instrument parameters to their defaults"
        )
        self._reset_analog_output_config(-1)
        self._reset_analog_input_config()
        self._reset_analog_io_config()

    def reset_digital_instrument(self) -> None:
        """Resets/Reconfigure all digital instrument parameters to their default values"""
        logger.info(
            "Reseting all Digital Instrument parameters to their defaults"
        )
        self._reset_digital_output_config()
        self._reset_digital_io_config()
        self._reset_digital_input_config()

    ### Power Supplies Instrument ###
    def configure_power_supply(
        self, positive_voltage: float, negative_voltage: Optional[float] = None
    ) -> None:
        """
        Set positive / negative supply voltages for the power supply Analog IO channels (V+ / V-)
        of Analog Discovery 2 and enable the corresponding IO channels

        Note: power supply can be enabled with one supply voltage (i.e. positive supply V+ channel is sufficent)
        if negative_voltage is not defined V- channel will not be enabled

        """
        # set voltage values to be in working range of the analog discovery 2 device (-5, +5 Volts)

        v_plus = max(0, min(5, positive_voltage))
        # set V+
        result = self._dwf.FDwfAnalogIOChannelNodeSet(
            self._hdwf, c_int(0), c_int(1), c_double(v_plus)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        # enable positive supply channel v+
        result = self._dwf.FDwfAnalogIOChannelNodeSet(
            self._hdwf, c_int(0), c_int(0), c_double(True)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        if negative_voltage:
            v_minus = max(-5, min(0, negative_voltage))
            # set V-
            result = self._dwf.FDwfAnalogIOChannelNodeSet(
                self._hdwf, c_int(1), c_int(1), c_double(v_minus)
            )
            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            # enable negative supply channel v-
            result = self._dwf.FDwfAnalogIOChannelNodeSet(
                self._hdwf, c_int(1), c_int(0), c_double(True)
            )
            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

        logger.info(
            f"Set Power Supply Channels: (V+): {positive_voltage} V, (V-): {negative_voltage} V"
        )

    def enable_power_supply(self) -> None:
        """Enable power supply on AnalogDiscovery 2 (i.e. enable AnalogIO master switch )"""
        # master enable
        result = self._dwf.FDwfAnalogIOEnableSet(self._hdwf, c_int(True))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        time.sleep(1)
        logger.info("Enabled power supply master switch")

    def disable_power_supply(self) -> None:
        """Disable power supply on AnalogDiscovery 2 (i.e. disable AnalogIO master switch )"""
        # master disable
        result = self._dwf.FDwfAnalogIOEnableSet(self._hdwf, c_int(False))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        time.sleep(1)
        logger.info("Disabled power supply master switch")

    def get_power_supply_status(self) -> bool:
        """
        Gets the status of the AnalogIO master enable switch for the Analog Discovery 2 supplies
        Returns:
            True -> On
            False -> Off
        """
        # Read and check analog IO status first
        if self._dwf.FDwfAnalogIOStatus(self._hdwf) == 0:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        # query master switch state
        analog_io_state = c_int()
        result = self._dwf.FDwfAnalogIOEnableStatus(
            self._hdwf, byref(analog_io_state)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        logger.info(
            f"Current enable status of Analog IO master switch: {bool(analog_io_state)}"
        )
        return bool(analog_io_state)

    def set_power_supply_voltages(
        self, positive_voltage: float, negative_voltage: Optional[float] = None
    ) -> None:
        """
        Set positive / negative supply voltages for the power supply Analog IO channels (V+ / V-)
        of Analog Discovery 2

        Note: negative_voltage is optional as power supply can be enabled with positive_voltage only
        """
        v_plus = max(0, min(5, positive_voltage))
        # set V+
        result = self._dwf.FDwfAnalogIOChannelNodeSet(
            self._hdwf, c_int(0), c_int(1), c_double(v_plus)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        if negative_voltage:
            v_minus = max(-5, min(0, negative_voltage))
            # set V-
            result = self._dwf.FDwfAnalogIOChannelNodeSet(
                self._hdwf, c_int(1), c_int(1), c_double(v_minus)
            )
            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            # enable negative supply channel v-
            result = self._dwf.FDwfAnalogIOChannelNodeSet(
                self._hdwf, c_int(1), c_int(0), c_double(True)
            )
            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

        time.sleep(1)
        logger.info(
            f"Set Power Supply Voltages: (V+): {positive_voltage} V, (V-): {negative_voltage} V"
        )

    def get_power_supply_voltages(self) -> Tuple[float, float]:
        """
        Gets currently set positive / negative supply voltages for the power supply Analog IO channels (V+ / V-)
        of Analog Discovery 2 in tuple form

        """
        # Read and check analog IO status first
        if self._dwf.FDwfAnalogIOStatus(self._hdwf) == 0:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # create buffer variables
        c_v_plus = c_double()
        c_v_minus = c_double()

        # get V+
        result = self._dwf.FDwfAnalogIOChannelNodeGet(
            self._hdwf, c_int(0), c_int(1), byref(c_v_plus)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # get V-
        result = self._dwf.FDwfAnalogIOChannelNodeGet(
            self._hdwf, c_int(1), c_int(1), byref(c_v_minus)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        logger.info(
            f"Currently Set Power Supply Voltages: (V+): {c_v_plus.value} V, (V-): {c_v_minus.value} V"
        )

        return (c_v_plus.value, c_v_minus.value)

    def get_power_supply_monitor_values(
        self,
    ) -> Tuple[float, float, float, float]:
        """
        Gets the following power supply monitored values from the Analog Discovery 2 in tuple form

        usbVoltage (V) , usbCurrent (A) , auxVoltage (V), auxCurrent (A)

        """
        # Read and check analog IO status first
        if self._dwf.FDwfAnalogIOStatus(self._hdwf) == 0:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # create buffer variables to store the info
        c_usbVoltage = c_double()
        c_usbCurrent = c_double()
        c_auxVoltage = c_double()
        c_auxCurrent = c_double()

        # Get the monitor values
        if (
            self._dwf.FDwfAnalogIOChannelNodeStatus(
                self._hdwf, c_int(2), c_int(0), byref(c_usbVoltage)
            )
            == 0
        ):
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        if (
            self._dwf.FDwfAnalogIOChannelNodeStatus(
                self._hdwf, c_int(2), c_int(1), byref(c_usbCurrent)
            )
            == 0
        ):
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        if (
            self._dwf.FDwfAnalogIOChannelNodeStatus(
                self._hdwf, c_int(3), c_int(0), byref(c_auxVoltage)
            )
            == 0
        ):
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        if (
            self._dwf.FDwfAnalogIOChannelNodeStatus(
                self._hdwf, c_int(3), c_int(1), byref(c_auxCurrent)
            )
            == 0
        ):
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return (
            c_usbVoltage.value,
            c_usbCurrent.value,
            c_auxVoltage.value,
            c_auxCurrent.value,
        )

    ### WaveGen / Scope Instrument ###
    def get_analog_channel_enable_state(
        self, channel: Union[AnalogInputChannel, AnalogOutputChannel]
    ) -> int:
        """
        Gets the enable state of an analog in/out channel

        Returns:
            enabled : 1
            disabled: 0
        """
        c_enable_state = c_int()

        # Input
        if isinstance(channel, AnalogInputChannel):
            result = self._dwf.FDwfAnalogInChannelEnableGet(
                self._hdwf, c_int(channel.value), byref(c_enable_state)
            )

        # Output
        elif isinstance(channel, AnalogOutputChannel):
            result = self._dwf.FDwfAnalogOutNodeEnableGet(
                self._hdwf,
                c_int(channel.value),
                AnalogOutNodeCarrier,
                byref(c_enable_state),
            )

        # Invalid Channel
        else:
            raise RuntimeError(
                f"Invalid channel selection: {channel}. channel must be a valid enum of: {AnalogInputChannel.__name__} or: {AnalogOutputChannel.__name__} "
            )

        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

        return c_enable_state.value

    def get_analog_out_channel_master(self, channel_node: int) -> int:
        """
        Gets the state machine master of the channel generator
        Verifies the parameter set by set_analog_out_channel_master

        Returns:
            int: The index of the master channel which the channel is configured to follow.

        """
        master_ch = c_int()
        result = self._dwf.FDwfAnalogOutMasterGet(
            self._hdwf, c_int(channel_node), byref(master_ch)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        return master_ch.value

    def set_analog_out_channel_master(
        self, channel_node: int, master_channel: int
    ) -> None:
        """
        Sets the state machine master of the channel generator
        With channel_node = -1, each enabled Analog
        Out channel will be configured to use the same, new option
        """
        result = self._dwf.FDwfAnalogOutMasterSet(
            self._hdwf, c_int(channel_node), c_int(master_channel)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def enable_analog_channel(
        self, channel: Union[AnalogInputChannel, AnalogOutputChannel]
    ) -> None:
        """
        Enables an AnalogIn (Oscilloscope) / AnalogOut (WaveGen) channel of the instrument

        args:
            channel: enum of type 'AnalogInputChannel' or 'AnalogOutputChannel'

        """
        # Input
        if isinstance(channel, AnalogInputChannel):
            self._enable_analog_in_channel(channel.value)

        # Output
        elif isinstance(channel, AnalogOutputChannel):
            self._enable_analog_out_channel(channel.value)

        # Invalid Channel
        else:
            raise RuntimeError(
                f"Invalid channel selection: {channel}. channel must be a valid enum of: {AnalogInputChannel.__name__} or: {AnalogOutputChannel.__name__} "
            )

    def disable_analog_channel(
        self, channel: Union[AnalogInputChannel, AnalogOutputChannel]
    ) -> None:
        """
        Disables an AnalogIn / AnalogOut channel of the instrument

        """
        # Input
        if isinstance(channel, AnalogInputChannel):
            self._disable_analog_in_channel(channel.value)

        # Output
        elif isinstance(channel, AnalogOutputChannel):
            self._disable_analog_out_channel(channel.value)

        # Invalid Type
        else:
            raise RuntimeError(
                f"Invalid channel selection: {channel}. channel must be a valid enum of: {AnalogInputChannel.__name__} or: {AnalogOutputChannel.__name__} "
            )

    def play_analog_signal(
        self,
        output_channels: List[AnalogOutputChannel],
        type: AnalogOutputSignal,
        frequency: float,
        amplitude: float,
        analog_data: np.ndarray = None,
        offset: float = 0,
        phase: float = 0,
        symmetry: float = 50,
        play_duration: float = 0,
        repeat_count: int = 0,
        wait_duration: float = 0,
        idle_state: AnalogOutputIdleState = AnalogOutputIdleState.Init,
        trigger_source: Optional[AnalogTriggerSource] = None,
        trigger_slope: AnalogTriggerSlope = AnalogTriggerSlope.Rise,
    ) -> None:
        """
        Starts the play of an analog signal with given configuration
        on a specfied WaveGen (output) channel(s)

        NOTE: This function will direclty return after the play has started.
        The state of the play can be then queried by 'get_play_status'

        args:
            - output_channels: list of analog output channels to play on -> see: 'AnalogOutputChannel'
            - type: generator function -> see: 'AnalogOutputSignal'
            - frequency: frequency in Hz
            - amplitude: amplitude or DC voltage in Volts
            - analog_data: numpy array containing custom data to be played (AnalogOutputSignal.Custom or AnalogOutputSignal.Play)
            - offset: offset level from amplitude in volts (default is 0 volts)
            - phase: phase angle in degrees (default is 0 degrees)
            - symmetry: singal symmetry expressed as percentage (default is 50 %)
            - play_duration: run time in seconds (default is 0 -> infinite play)
            - repeat_count: replays count (default is 0 -> infinite replay)
            - wait_duration: wait time in seconds before the signal is played (default is 0 -> no wait)
            - idle_state: state of the output channels when not running (default is Initial) (see AnalogOutputIdleState)
            - trigger_source: (Optional) setup a trigger source for the instrument (see AnalogTriggerSource)
            - trigger_slope: slope condition to trigger the instrument (default: rising edge)(see AnalogTriggerSlope)
        """

        # Verify analog out channels are passed as a list
        if not isinstance(output_channels, list):
            raise RuntimeError(
                f"Expected a list of AnalogOutputChannel for output_channels. but got: {type(output_channels)}"
            )

        # Verfiy analog out channels are enabled
        self._verify_channels_enable_status(output_channels)

        # Configure
        for ch in output_channels:
            # set output signal
            self._set_analog_output_generator_function(ch.value, type.value)

            # set analog data for custom / play type signals
            if (
                type.value == AnalogOutputSignal.Custom.value
                or type.value == AnalogOutputSignal.Play.value
            ):
                if analog_data:
                    self._set_analog_output_data(ch.value, analog_data)
                else:
                    raise RuntimeError(
                        "analog_data was not defined for custom play"
                    )

            # set output signal frequency, amplitude, offset level, symmetry and phase
            self._set_analog_output_idle_state(ch.value, idle_state.value)
            self._set_analog_output_frequency(ch.value, frequency)
            self._set_analog_output_amplitude(ch.value, amplitude)
            self._set_analog_output_offset(ch.value, offset)
            self._set_analog_output_symmetry(ch.value, symmetry)
            self._set_analog_output_phase(ch.value, phase)

            # set play, wait durations and the number of repeats for the output signal
            self._set_analog_output_run_duration(ch.value, play_duration)
            self._set_analog_output_wait_duration(ch.value, wait_duration)
            self._set_analog_output_repeats_count(ch.value, repeat_count)

            # set trigger options
            if trigger_source:
                self._set_analog_output_trigger_source(
                    ch.value, trigger_source.value
                )
                self._set_analog_output_trigger_slope(
                    ch.value, trigger_slope.value
                )

        # log play configuration for debug
        for ch in output_channels:
            idle_s = self._get_analog_output_idle_state(ch.value)
            logger.debug(
                f"Current analog output idle state for channel : {ch.name} is: {idle_s.name}"
            )

            gen_func = self._get_analog_output_generator_function(ch.value)
            logger.debug(
                f"Current analog output generator function for channel : {ch.name} is: {gen_func.name}"
            )

            ch_frequency = self._get_analog_output_frequency(ch.value)
            logger.debug(
                f"Current analog output frequency for channel : {ch.name} is: {ch_frequency} Hz"
            )

            ch_amplitude = self._get_analog_output_amplitude(ch.value)
            logger.debug(
                f"Current analog output amplitude for channel : {ch.name} is: {ch_amplitude} volts"
            )

            ch_offset = self._get_analog_output_offset(ch.value)
            logger.debug(
                f"Current analog output voltage offset for channel : {ch.name} is: {ch_offset} volts"
            )

            ch_phase = self._get_analog_output_phase(ch.value)
            logger.debug(
                f"Current analog output phase for channel : {ch.name} is: {ch_phase} degrees"
            )

            ch_symmetry = self._get_analog_output_symmetry(ch.value)
            logger.debug(
                f"Current analog output symmetry for channel : {ch.name} is: {ch_symmetry} %"
            )

            ch_run_duration = self._get_analog_output_run_duration(ch.value)
            logger.debug(
                f"Current analog output run duration for channel : {ch.name} is: {ch_run_duration} seconds"
            )

            ch_wait_duration = self._get_analog_output_wait_duration(ch.value)
            logger.debug(
                f"Current analog output wait duration for channel : {ch.name} is: {ch_wait_duration} seconds"
            )

            ch_repeats_count = self._get_analog_output_repeats_count(ch.value)
            logger.debug(
                f"Current analog output repeats count for channel : {ch.name} is: {ch_repeats_count}"
            )

            trig_src = self._get_analog_output_trigger_source(ch.value)
            logger.debug(
                f"Current analog output trigger source for channel : {ch.name} is: {trig_src.name}"
            )

            trig_slope = self._get_analog_output_trigger_slope(ch.value)
            logger.debug(
                f"Current analog output trigger slope for channel : {ch.name} is: {trig_slope.name}"
            )

            # wait at least 2 seconds for the offset to stabilize (recommended by DWF examples)
            time.sleep(2)

        # start WaveGen instrument on output_channels
        for ch in output_channels:
            self._start_analog_output(ch.value)

        return None

    def get_play_status(
        self, output_channel: AnalogOutputChannel
    ) -> Tuple[int, str]:
        """
        Gets the WaveGen instrument latest analog status info for a given analog output channel

        Returns:
            Tuple : (status number, status name) for the instrument (see WaveForms SDK manual for the explanation of the status number)

        NOTE: This function need to be called before getting any analog out readings
        as it loads the latest buffer data from the instrument
        """
        # fetch staus and data from device
        play_status_num = self._get_analog_output_status(output_channel.value)
        play_status_name = AnalogInstrumentState(play_status_num).name
        return (play_status_num, play_status_name)

    def get_analog_input_range_info(self) -> Tuple[float, float, int]:
        """
        Returns analog input channels range info in tuple form: (minimum voltage range, max voltage range, number of range steps)
        """
        c_min_range = c_double()
        c_max_range = c_double()
        c_range_steps = c_double()

        result = self._dwf.FDwfAnalogInChannelRangeInfo(
            self._hdwf,
            byref(c_min_range),
            byref(c_max_range),
            byref(c_range_steps),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return (
            float(c_min_range.value),
            float(c_max_range.value),
            int(c_range_steps.value),
        )

    def get_analog_input_coupling_type(
        self, channel: AnalogInputChannel
    ) -> AnalogCouplingType:
        """
        Returns currently set coupling type for an analog input channel
        """
        c_coupling_type = c_int()

        result = self._dwf.FDwfAnalogInChannelCouplingGet(
            self._hdwf, c_int(channel.value), byref(c_coupling_type)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return AnalogCouplingType(c_coupling_type.value)

    def set_analog_input_coupling_type(
        self, channel: AnalogInputChannel, coupling: AnalogCouplingType
    ) -> None:
        """
        Sets coupling type for an analog input channel
        """
        result = self._dwf.FDwfAnalogInChannelCouplingSet(
            self._hdwf, c_int(channel.value), c_int(coupling.value)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def record_analog_signal(
        self,
        input_channels: List[AnalogInputChannel],
        sampling_frequency: float,
        record_length: float = 0,
        range: float = 5,
        offset: float = 0,
        analog_filter: AnalogFilter = AnalogFilter.Average,
        trigger_source: Optional[AnalogTriggerSource] = None,
        trigger_source_position: float = 0,
        trigger_type: AnalogTriggerType = AnalogTriggerType.Edge,
        trigger_level: float = 0,
        trigger_condition: AnalogTriggerSlope = AnalogTriggerSlope.Rise,
        trigger_timeout: float = 0,
        trigger_hysteresis: float = 0,
    ) -> None:
        """
        Start an analong signal recording (acquisituion) according to a given configuration
        on specified analog input channel(s)

        *In record mode the entire device buffer is used as FIFO

        NOTE: This function will direclty return after the analog channel has started / armed.
        reocrding data need to be fetched by 'get_record_status' and 'read_recorded_data'

        args:
            - input_channels: list of analog input channels to start recording on -> see: 'AnalogInputChannel'
            - sampling_frequency: rate at which data is read by the scope instrument into device buffer (Hz)
            - record_length: record duration in seconds (default: 0 means indefinite recording)
            - range: amplitude range for the captured signal (default: 5 volts)
            - offset: offset level for the amplitude of recorded signal in volts (default 0 volts)
            - analog_filter: a filter to apply for the recorded signal (software-based) (default is Average)
            - trigger_source: (Optional) setup a trigger source for the instrument (see AnalogTriggerSource)
            - trigger_source_position: horizontal trigger position in seconds (default 0 seconds)
            - trigger_type: (default Edge condition) (see AnalogTriggerType)
            - trigger_level: (default 0 volts)
            - trigger_condition: (default rising edge) (see AnalogTriggerSlope)
            - trigger_timeout: (default 0 : disable auto trigger)
            - trigger_hysteresis: (default 0)

        """

        if not isinstance(input_channels, list):
            raise RuntimeError(
                f"Expected a list of AnalogInputChannel for input_channels. but got: {type(input_channels)}"
            )

        # check requested channels are enabled
        self._verify_channels_enable_status(input_channels)

        # the device will only be configured when FDwf###Configure is called
        self._disable_auto_configure()

        # setup acquisition settings
        self._set_analog_input_acquisition_mode(
            AnalogAcquisitionMode.Record.value
        )
        self._set_analog_input_sampling_frequency(sampling_frequency)
        self._set_analog_input_record_length(record_length)

        # setup analog input channels range, offset and applied filter
        for ch in input_channels:
            self._set_analog_input_range(ch.value, range)
            self._set_analog_input_offset(ch.value, offset)
            self._set_analog_input_filter(ch.value, analog_filter)

        # setup trigger options (if trigger source is not defined triggering will be disabled)
        if trigger_source:
            # enable triggering and specify its source
            self._set_analog_input_trigger_source(
                trigger_source.value, sec_timeout=trigger_timeout
            )
            # set trigger position
            self._set_analog_input_trigger_position(trigger_source_position)
            # set trigger type
            self._set_analog_input_trigger_type(trigger_type)
            # set first passed channel as the trigger channel
            self._set_analog_input_trigger_channel(input_channels[0])
            # set trigger level
            self._set_analog_input_trigger_level(trigger_level)
            # set trigger hysteresis
            self._set_analog_input_trigger_hysteresis(trigger_hysteresis)
            # set trigger condition
            self._set_analog_input_trigger_condition(trigger_condition)

        # stop and confgiure analog in
        self._stop_analog_input(reset_auto_trigger_timeout=True)

        # wait at least 2 seconds for the offset to stabilize (recommended by DWF examples)
        time.sleep(2)

        # start Scope instrument acquisition on input_channels
        self._start_analog_input(reset_auto_trigger_timeout=False)

        return None

    def start_analog_screen(
        self,
        input_channels: List[AnalogInputChannel],
        sampling_frequency: float,
        samples_count: int,
        range: float = 5,
        offset: float = 0,
        analog_filter: AnalogFilter = AnalogFilter.Average,
    ) -> None:
        """
        Start "Shift Screen" capture of analong data on a specified Oscilloscope (input) channel(s)
        *for monitoring slow signals continuously

        NOTE: This function will return after the screen has started

        args:
            - input_channels: list of analog input channels to start recording on -> see: 'AnalogInputChannel'
            - sampling_frequency: rate at which data is read by the scope instrument into device buffer (Hz)
            - samples_count: buffer size used for storing data (less than max device buffer for a given config)
            - range: amplitude range for the captured signal (default: 5 volts)
            - offset: offset level for the amplitude of recorded signal in volts (default 0 volts)
            - analog_filter: a filter to apply for the recorded signal (software-based) (default is Average)
        """

        if not isinstance(input_channels, list):
            raise RuntimeError(
                f"Expected a list of AnalogInputChannel for input_channels. but got: {type(input_channels)}"
            )

        # check requested channels are enabled
        self._verify_channels_enable_status(input_channels)

        # check if requested samples count is greater than max buffer size
        # NOTE: samples_count is limited by max buffer size for a given device config
        _, max_buffer_size = self._get_analog_input_buffer_size_info()
        if samples_count > max_buffer_size:
            logger.warning(
                f"requested samples count: {samples_count} is greater than max buffer size of the device: {max_buffer_size}. max buffer size will be used"
            )
            samples_count = max_buffer_size

        # the device will only be configured when FDwf###Configure is called
        self._disable_auto_configure()

        # setup acquisition settings
        self._set_analog_input_buffer_size(samples_count)
        self._set_analog_input_acquisition_mode(
            AnalogAcquisitionMode.ScanShift.value
        )
        self._set_analog_input_sampling_frequency(sampling_frequency)

        # setup analog input channels range, offset and applied filter
        for ch in input_channels:
            self._set_analog_input_range(ch.value, range)
            self._set_analog_input_offset(ch.value, offset)
            self._set_analog_input_filter(ch.value, analog_filter)

        # stop and confgiure analog in
        self._stop_analog_input(reset_auto_trigger_timeout=True)

        # wait at least 2 seconds for the offset to stabilize (recommended by DWF examples)
        time.sleep(2)

        # start Scope instrument acquisition on input_channels
        self._start_analog_input(reset_auto_trigger_timeout=False)

    def retrieve_analog_screen(
        self,
        input_channels: List[AnalogInputChannel],
        samples_count: int,
        scan_duration_sec: float,
    ) -> List[np.ndarray]:
        """
        Retrieves for 'scan_duration_sec' captured analog data of size 'samples_count' from device buffer for an ongoing analog screen.
        returns data array for each input channel

        *Precondition: an analog screen has started (i.e. call after: start_analog_screen)
        *NOTE: It is recommended to select analog discovery config with largest memory for scope instrument to avoid loss
        *of data at higher sampling rates
        """

        # create list to store channels data
        channels_data = []
        for ch in input_channels:
            channels_data.append((c_double * samples_count)())

        cValid = c_int(0)
        sts = c_byte()

        # start shift screen of analog data
        t_start = time.perf_counter()
        while time.perf_counter() - t_start < scan_duration_sec:
            # fetch analog instrument status
            return_code = self._dwf.FDwfAnalogInStatus(
                self._hdwf, c_int(1), byref(sts)
            )
            return_code = self._dwf.FDwfAnalogInStatusSamplesValid(
                self._hdwf, byref(cValid)
            )

            # fetch channels analog data
            for i, ch in enumerate(input_channels):
                return_code = self._dwf.FDwfAnalogInStatusData(
                    self._hdwf,
                    c_int(ch.value),
                    byref(channels_data[i]),
                    cValid,
                )

        if return_code != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return [
            np.fromiter(samples, dtype=np.float64) for samples in channels_data
        ]

    def get_record_status(self) -> Tuple[int, str]:
        """
        Gets the Scope instrument latest analog status info (acquisition state)

        Returns:
            Tuple : (status number, status name) for the instrument (see WaveForms SDK manual for the explanation of the status number)

        NOTE: This function need to be called before getting any analog in readings
        as it loads the latest buffer data from the instrument

        """
        # fetch staus and data from device
        record_status_num = self._get_analog_input_status(read_data=True)
        record_status_name = AnalogInstrumentState(record_status_num).name
        return (record_status_num, record_status_name)

    def read_recorded_data(
        self, input_channel: AnalogInputChannel
    ) -> np.ndarray:
        """
        Fetch the captured analog data during an analog signal record process.
        The analog data fetched is based on the buffer recieved from the last get_record_status call.
        *Precondition: an analog recording has started (i.e. call after: record_analog_signal, get_record_status)
        """
        # fetch the record status info
        available, lost, corrupt = self._get_analog_input_record_status()
        if lost:
            logger.warning("Recording samples were lost! Reduce frequency")
        if corrupt:
            logger.warning(
                "Recording samples could be corrupted! Reduce frequency"
            )

        # now fetch the recorded data
        data_samples = self._get_analog_input_record_data(
            input_channel.value, available
        )

        return data_samples

    def fill_recorded_samples(
        self, input_channel: AnalogInputChannel, samples_count: int
    ) -> np.ndarray:
        """
        Continously fetch captured analog data in FIFO form until 'samples_count' is collected.
        In case of buffer overflow, warnings are generated to reduce sampling_frequnecy of the recording

        *Precondition: an analog recording has started (i.e. call after: record_analog_signal)
        *NOTE: It is recommended to select analog discovery config with largest memory for scope instrument to avoid loss
        *of data at higher sampling rates

        """
        # state variables to store record info
        cSamples = 0
        cLost = 0
        cCorrupted = 0
        rgSamples = (c_int16 * samples_count)()

        # used to convert adc data to raw voltages (see waveforms SDK reference manual)
        conversion_factor = self._get_analog_input_range(
            input_channel.value
        ) / (65536)
        ch_offset = self._get_analog_input_offset(input_channel.value)

        while cSamples < samples_count:
            # fetch buffer status and data
            status = self._get_analog_input_status(read_data=True)
            if cSamples == 0 and (
                status == DwfStateConfig.value
                or status == DwfStatePrefill.value
                or status == DwfStateArmed.value
            ):
                # Acquisition not yet started.
                continue

            # get record state counters
            cAvailable, cLost, cCorrupted = (
                self._get_analog_input_record_status()
            )

            # increment samples counter to consider lost samples
            cSamples += cLost

            # if no samples available yet continue
            if cAvailable == 0:
                continue

            # reduce number of requested samples if samples_count will be excedded
            if cSamples + cAvailable > samples_count:
                cAvailable = samples_count - cSamples

            # fetch recorded data from buffer
            result = self._dwf.FDwfAnalogInStatusData16(
                self._hdwf,
                c_int(input_channel.value),
                byref(rgSamples, sizeof(c_int16) * cSamples),
                c_int(0),
                c_int(cAvailable),
            )

            # increment samples counter to consider available fetched samples
            cSamples += cAvailable

        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # indicates fifo overflow, try to improve the loop performance, reduce sample rate
        if cLost > 0:
            logger.warning(
                f"{cLost} Recording Samples were lost during the fetch process! -> Reduce sampling frequency"
            )
        if cCorrupted > 0:
            logger.warning(
                f"{cCorrupted} Recording Samples could be corrupted during the fetch process! -> Reduce sampling frequency"
            )

        results_array = np.fromiter(rgSamples, dtype=np.int16) * (
            conversion_factor
        )
        return results_array + ch_offset

    def fill_recorded_samples_on_channels(
        self, input_channels: List[AnalogInputChannel], samples_count: int
    ) -> List[np.ndarray]:
        """
        Continously fetch captured analog data on (from multiple channels) in FIFO form until 'samples_count' is collected.
        In case of buffer overflow, warnings are generated to reduce sampling_frequnecy of the recording

        *Precondition: an analog recording has started (i.e. call after: record_analog_signal)
        *NOTE: It is recommended to select analog discovery config with largest memory for scope instrument to avoid loss
        *of data at higher sampling rates

        """
        # state variables to store record info
        cSamples = 0
        cLost = 0
        cCorrupted = 0

        # create list to store channels data
        channels_data = []
        for ch in input_channels:
            channels_data.append((c_int16 * samples_count)())

        # used to convert adc data to raw voltages (see waveforms SDK reference manual)
        conversion_factor = self._get_analog_input_range(
            input_channels[0].value
        ) / (65536)
        ch_offset = self._get_analog_input_offset(input_channels[0].value)

        while cSamples < samples_count:
            # fetch buffer status and data
            status = self._get_analog_input_status(read_data=True)
            if cSamples == 0 and (
                status == DwfStateConfig.value
                or status == DwfStatePrefill.value
                or status == DwfStateArmed.value
            ):
                # Acquisition not yet started.
                continue

            # get record state counters
            cAvailable, cLost, cCorrupted = (
                self._get_analog_input_record_status()
            )

            # increment samples counter to consider lost samples
            cSamples += cLost

            # if no samples available yet continue
            if cAvailable == 0:
                continue

            # reduce number of requested samples if samples_count will be excedded
            if cSamples + cAvailable > samples_count:
                cAvailable = samples_count - cSamples

            # fetch recorded data from buffer
            for i, ch in enumerate(input_channels):
                result = self._dwf.FDwfAnalogInStatusData16(
                    self._hdwf,
                    c_int(ch.value),
                    byref(channels_data[i], sizeof(c_int16) * cSamples),
                    c_int(0),
                    c_int(cAvailable),
                )

            # increment samples counter to consider available fetched samples
            cSamples += cAvailable

        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # indicates fifo overflow, try to improve the loop performance, reduce sample rate
        if cLost > 0:
            logger.warning(
                f"{cLost} Recording Samples were lost during the fetch process! -> Reduce sampling frequency"
            )
        if cCorrupted > 0:
            logger.warning(
                f"{cCorrupted} Recording Samples could be corrupted during the fetch process! -> Reduce sampling frequency"
            )

        return [
            (
                (np.fromiter(samples, dtype=np.int16) * (conversion_factor))
                + ch_offset
            )
            for samples in channels_data
        ]

    def fill_recorded_samples_2(
        self, input_channel: AnalogInputChannel, samples_count: int
    ) -> np.ndarray:
        """
        Continously fetch captured analog data in circular form until reocrding state is done and returns a
        recording array of size: 'samples_count'.
        In case of buffer overflow, warnings are generated to reduce sampling_frequnecy of the recording

        *Precondition: an analog recording/acquisition has started (i.e. call after: record_analog_signal)
        *NOTE: It is recommended to select analog discovery config with largest memory for scope instrument to avoid loss
        *of data at higher sampling rates

        """
        iSample = 0
        cSamples = 0
        cCorrupted = 0
        cLost = 0
        rgSamples = (c_int16 * samples_count)()

        # used to convert adc data to raw voltages
        conversion_factor = self._get_analog_input_range(
            input_channel.value
        ) / (65536)
        ch_offset = self._get_analog_input_offset(input_channel.value)

        while True:
            status = self._get_analog_input_status(read_data=True)
            cAvailable, cLost, cCorrupted = (
                self._get_analog_input_record_status()
            )

            iSample += cLost
            iSample %= samples_count

            iBuffer = 0
            while cAvailable > 0:
                cSamples = cAvailable
                # we are using circular sample buffer, make sure to not overflow
                if iSample + cAvailable > samples_count:
                    cSamples = samples_count - iSample
                result = self._dwf.FDwfAnalogInStatusData16(
                    self._hdwf,
                    c_int(input_channel.value),
                    byref(rgSamples, sizeof(c_int16) * iSample),
                    c_int(iBuffer),
                    c_int(cSamples),
                )
                iBuffer += cSamples
                cAvailable -= cSamples
                iSample += cSamples
                iSample %= samples_count

            if status == 2:  # done
                break

            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

        # indicates fifo overflow, try to improve the loop performance, reduce sample rate
        if cLost > 0:
            logger.warning(
                f"{cLost} Recording Samples were lost during the fetch process! -> Reduce sampling frequency"
            )
        if cCorrupted > 0:
            logger.warning(
                f"{cCorrupted} Recording Samples could be corrupted during the fetch process! -> Reduce sampling frequency"
            )

        # align recorded data
        if iSample != 0:
            rgSamples = rgSamples[iSample:] + rgSamples[:iSample]

        results_array = np.fromiter(rgSamples, dtype=np.int16) * (
            conversion_factor
        )
        return results_array + ch_offset

    def perform_single_analog_acquisition(
        self,
        input_channel: AnalogInputChannel,
        sampling_frequency: float,
        samples_count: int,
        range: float = 5,
        offset: float = 0,
        analog_filter: AnalogFilter = AnalogFilter.Decimate,
        trigger_source: Optional[AnalogTriggerSource] = None,
        trigger_source_position: float = 0,
        trigger_type: AnalogTriggerType = AnalogTriggerType.Edge,
        trigger_level: float = 0,
        trigger_condition: AnalogTriggerSlope = AnalogTriggerSlope.Rise,
        trigger_hysteresis: float = 0,
    ) -> np.ndarray:
        """
        start acquisition and collection of analog data samples of given count on an analog input channel
        see also: record_analog_signal
        # NOTE: This function will only return when the acquisition state is Done

        args:
            - input_channel: analog input channel to start capture on -> see: 'AnalogInputChannel'
            - sampling_frequency: rate at which data is read by the scope instrument into device buffer (Hz)
            - samples_count: number of data points to collect (less than max device buffer for a given config)
            - range: amplitude range for the captured signal (default: 5 volts)
            - offset: offset level for the amplitude of recorded signal in volts (default 0 volts)
            - analog_filter: a filter to apply for the recorded signal (software-based) (default is Decimate)
            - trigger_source: (Optional) setup a trigger source for the instrument (see AnalogTriggerSource)
            - trigger_source_position: horizontal trigger position in seconds (default 0 seconds)
            - trigger_type: (default Edge condition) (see AnalogTriggerType)
            - trigger_level: (default 0 volts)
            - trigger_condition: (default rising edge) (see AnalogTriggerSlope)
            - trigger_hysteresis: (default 0)
        """

        # check requested channel is enabled
        self._verify_channels_enable_status([input_channel])

        # setup acquisition settings
        # check if requested samples count is greater than max buffer size
        # NOTE: samples_count is limited by max buffer size for a given device config
        _, max_buffer_size = self._get_analog_input_buffer_size_info()
        if samples_count > max_buffer_size:
            logger.warning(
                f"requested samples count: {samples_count} is greater than max buffer size of the device: {max_buffer_size}. max buffer size will be used"
            )
            samples_count = max_buffer_size

        # the device will only be configured when FDwf###Configure is called
        self._disable_auto_configure()

        self._set_analog_input_buffer_size(samples_count)
        self._set_analog_input_sampling_frequency(sampling_frequency)

        # setup analog input channels range, offset and applied filter
        self._set_analog_input_range(input_channel.value, range)
        self._set_analog_input_offset(input_channel.value, offset)
        self._set_analog_input_filter(input_channel.value, analog_filter)

        # setup trigger options (if trigger source is not defined triggering will be disabled)
        if trigger_source:
            # enable triggering and specify its source
            self._set_analog_input_trigger_source(
                trigger_source.value, sec_timeout=0
            )  # disable auto trigger
            # set trigger position
            self._set_analog_input_trigger_position(trigger_source_position)
            # set trigger type
            self._set_analog_input_trigger_type(trigger_type)
            # set channel 1 as the trigger channel
            self._set_analog_input_trigger_channel(input_channel)
            # set trigger level
            self._set_analog_input_trigger_level(trigger_level)
            # set trigger hysteresis
            self._set_analog_input_trigger_hysteresis(trigger_hysteresis)
            # set trigger condition
            self._set_analog_input_trigger_condition(trigger_condition)

        # wait for the offset to stabilize, before the first reading after device open or offset/range change
        time.sleep(1)

        # create buffer array
        buffer_data = (c_double * c_int(samples_count).value)()

        # start Scope instrument acquisition on input_channel
        self._start_analog_input(reset_auto_trigger_timeout=True)

        # capture analog data samples on input_channel
        while True:
            # read data to an internal buffer
            status = self._get_analog_input_status(read_data=True)
            # check internal buffer status
            if status == DwfStateDone.value:
                # exit loop when acquisition is done
                break

        # copy device internal buffer to buffer_data
        result = self._dwf.FDwfAnalogInStatusData(
            self._hdwf,
            c_int(input_channel.value),
            buffer_data,
            c_int(samples_count),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # convert to numpy array
        collected_samples = np.fromiter(buffer_data, dtype=np.float64)

        return collected_samples

    def start_analog_acquisition(
        self,
        input_channels: List[AnalogInputChannel],
        sampling_frequency: float,
        samples_count: int,
        range: float = 5,
        offset: float = 0,
        analog_filter: AnalogFilter = AnalogFilter.Decimate,
        trigger_source: Optional[AnalogTriggerSource] = None,
        trigger_source_position: float = 0,
        trigger_type: AnalogTriggerType = AnalogTriggerType.Edge,
        trigger_level: float = 0,
        trigger_condition: AnalogTriggerSlope = AnalogTriggerSlope.Rise,
        trigger_hysteresis: float = 0,
        single_acquisition=False,
    ) -> None:
        """
        start acquisition on an analog input channel
        see also: perform_single_analog_acquisition
        # NOTE: This function will return after analog channel has started / armed

        args:
            - input_channels: list of analog input channels to start capture on -> see: 'AnalogInputChannel'
            - sampling_frequency: rate at which data is read by the scope instrument into device buffer (Hz)
            - samples_count: number of data points to collect (less than max device buffer for a given config)
            - range: amplitude range for the captured signal (default: 5 volts)
            - offset: offset level for the amplitude of recorded signal in volts (default 0 volts)
            - analog_filter: a filter to apply for the recorded signal (software-based) (default is Decimate)
            - trigger_source: (Optional) setup a trigger source for the instrument (see AnalogTriggerSource)
            - trigger_source_position: horizontal trigger position in seconds (default 0 seconds)
            - trigger_type: (default Edge condition) (see AnalogTriggerType)
            - trigger_level: (default 0 volts)
            - trigger_condition: (default rising edge) (see AnalogTriggerSlope)
            - trigger_timeout: (default 0 : disable auto trigger)
            - trigger_hysteresis: (default 0)
            - single_acquisition: (default False) if set to True then perform a single buffer acquisition without rearming the instrument
        """

        # check requested channel is enabled
        self._verify_channels_enable_status(input_channels)

        # setup acquisition settings
        # check if requested samples count is greater than max buffer size
        # NOTE: samples_count is limited by max buffer size for a given device config
        _, max_buffer_size = self._get_analog_input_buffer_size_info()
        if samples_count > max_buffer_size:
            logger.warning(
                f"requested samples count: {samples_count} is greater than max buffer size of the device: {max_buffer_size}. max buffer size will be used"
            )
            samples_count = max_buffer_size

        # the device will only be configured when FDwf###Configure is called
        self._disable_auto_configure()

        self._set_analog_input_buffer_size(samples_count)
        self._set_analog_input_sampling_frequency(sampling_frequency)

        if single_acquisition:
            self._set_analog_input_acquisition_mode(
                AnalogAcquisitionMode.Single1.value
            )

        # setup analog input channels range, offset and applied filter
        for ch in input_channels:
            self._set_analog_input_range(ch.value, range)
            self._set_analog_input_offset(ch.value, offset)
            self._set_analog_input_filter(ch.value, analog_filter)

        # setup trigger options (if trigger source is not defined triggering will be disabled)
        if trigger_source:
            # enable triggering and specify its source
            self._set_analog_input_trigger_source(
                trigger_source.value, sec_timeout=0
            )  # disable auto trigger
            # set trigger position
            self._set_analog_input_trigger_position(trigger_source_position)
            # set trigger type
            self._set_analog_input_trigger_type(trigger_type)
            # set first passed channel as the trigger channel
            self._set_analog_input_trigger_channel(input_channels[0])
            # set trigger level
            self._set_analog_input_trigger_level(trigger_level)
            # set trigger hysteresis
            self._set_analog_input_trigger_hysteresis(trigger_hysteresis)
            # set trigger condition
            self._set_analog_input_trigger_condition(trigger_condition)

        # stop and confgiure analog in
        self._stop_analog_input(reset_auto_trigger_timeout=True)

        # wait for the offset to stabilize, before the first reading after device open or offset/range change
        time.sleep(1)

        # start Scope instrument acquisition on input_channel
        self._start_analog_input(reset_auto_trigger_timeout=False)

        return None

    def retrieve_analog_acquisitions(
        self,
        input_channels: List[AnalogInputChannel],
        samples_count: int,
        n_captures: int = 1,
    ) -> List[Tuple[List[np.ndarray], str]]:
        """
        Retrieves captured analog data of size 'samples_count' from device buffer for an ongoing analog acquisition.
        returns data array for each input channel and the trigger time as measured by the instrument

        n_captures can be set to > 1 for repeated fetch of data based on reucrring trigger condition

        returns list that contains for each capture a tuple with the following content:
            - Lists of fetched data for the input_channels
            - trigger_time of the instrument for the measurement

        *Precondition: an analog acquisition has started (i.e. call after: start_analog_acquisition)
        *NOTE: It is recommended to select analog discovery config with largest memory for scope instrument to avoid loss
        *of data at higher sampling rates

        """
        sec = c_uint()
        tick = c_uint()
        ticksec = c_uint()
        capture_events = []
        channels_data = []

        for i in range(len(input_channels)):
            channels_data.append([])
            for _ in range(n_captures):
                channels_data[i].append((c_double * samples_count)())

        for i in range(n_captures):
            # new acquisition is started automatically after done state in case of repeated acquisition
            while True:
                # read data to an internal buffer
                status = self._get_analog_input_status(read_data=True)
                # check internal buffer status
                if status == DwfStateDone.value:
                    # exit loop when acquisition is done
                    break

            # fetch channels analog data
            for j, ch in enumerate(input_channels):
                return_code = self._dwf.FDwfAnalogInStatusData(
                    self._hdwf,
                    c_int(ch.value),
                    byref(channels_data[j][i]),
                    c_int(samples_count),
                )

            # get the trigger time
            return_code = self._dwf.FDwfAnalogInStatusTime(
                self._hdwf, byref(sec), byref(tick), byref(ticksec)
            )
            if return_code != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

            # calculate trigger time to nano second resolution
            s = time.localtime(sec.value)
            ns = 1e9 / ticksec.value * tick.value
            ms = math.floor(ns / 1e6)
            ns -= ms * 1e6
            us = math.floor(ns / 1e3)
            ns -= us * 1e3
            ns = math.floor(ns)
            trigger_time = (
                time.strftime("%Y-%m-%d %H:%M:%S", s)
                + "."
                + str(ms).zfill(3)
                + "."
                + str(us).zfill(3)
                + "."
                + str(ns).zfill(3)
            )

            # convert c_arrary into numpy arrays and append the trigger time for the captured event
            capture_events.append(
                (
                    [
                        np.fromiter(channels_data[k][i], dtype=np.float64)
                        for k in range(len(input_channels))
                    ],
                    trigger_time,
                )
            )

        return capture_events

    def read_analog_signal_voltage(
        self, input_channel: AnalogInputChannel
    ) -> float:
        """
        reads an analog singal measured voltage (in volts) on an analog input channel
        """
        # configure the analog in instrument for sample reading without starting acuqistion
        self._stop_analog_input(reset_auto_trigger_timeout=False)
        # read analog in status data
        self._get_analog_input_status(read_data=False)
        # Get single sample reading from analog input channel
        sample_reading = self._get_analog_input_status_sample(
            input_channel.value
        )

        return sample_reading

    def perform_ac_rms_data_logging(
        self,
        input_channel: AnalogInputChannel,
        logging_rate: float,
        samples_count: int,
        logging_duration: float,
        amp_range: float = 5,
    ) -> List[float]:
        """
        Collect raw voltage readings from analog in channel and caclulate AC rms values
        for given duration and logging rate

        Args:
            input_channel: analog input channels to start recording on -> see: 'AnalogInputChannel'
            logging_rate: interval to make readings in seconds
            samples_count: buffer size for the measurement (e.g. 8000 samples)
            logging_duration: duration window in seconds for making the readings
            amp_range: amplitude range for the analog in measurend signal

        Returns:
            list of AC RMS values
        """

        # check requested channels are enabled
        self._verify_channels_enable_status([input_channel])

        # NOTE: samples_count is limited by max buffer size for a given device config
        _, max_buffer_size = self._get_analog_input_buffer_size_info()
        if samples_count > max_buffer_size:
            logger.warning(
                f"requested samples count: {samples_count} is greater than max buffer size of the device: {max_buffer_size}. max buffer size will be used"
            )
            samples_count = max_buffer_size

        # setup acquisition settings
        self._set_analog_input_acquisition_mode(
            AnalogAcquisitionMode.ScanShift.value
        )
        self._set_analog_input_sampling_frequency(
            float(samples_count / logging_rate)
        )
        self._set_analog_input_buffer_size(samples_count)

        # setup analog input channels range
        self._set_analog_input_range(input_channel.value, amp_range)

        # configure instrument and reset auto timeout
        self._stop_analog_input(reset_auto_trigger_timeout=True)

        # wait at least 2 seconds for the offset to stabilize
        time.sleep(2)

        # a list to hold the collected rms results for the input channel
        rms_results = []

        # start Scope instrument acquisition on input_channels
        self._start_analog_input(reset_auto_trigger_timeout=False)

        # capture analog data and calculate ac / dc rms values
        start_time = time.time()
        while (time.time() - start_time) <= logging_duration:
            time.sleep(logging_rate)
            self._get_analog_input_status(read_data=True)
            valid_samples = self._get_analog_input_valid_samples()
            rgdSamples = self._get_analog_input_record_data(
                input_channel.value, valid_samples
            )
            dc = 0
            for i in range(samples_count):
                dc += rgdSamples[i]
            dc /= samples_count
            dcrms = 0
            acrms = 0
            for i in range(samples_count):
                dcrms += rgdSamples[i] ** 2
                acrms += (rgdSamples[i] - dc) ** 2
            dcrms /= samples_count
            dcrms = math.sqrt(dcrms)
            acrms /= samples_count
            acrms = math.sqrt(acrms)

            rms_results.append(acrms)

        return rms_results

    def perform_fft_measurements(
        self,
        input_channel: AnalogInputChannel,
        sampling_frequency: float,
        window_func: FFTWindow = FFTWindow.FLAT_TOP,
        amp_range: float = 5,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Collect raw voltage readings from analog in channel and caclulate FFT bins / phase
        on the recorded data

        Args:
            input_channel: analog input channels to start recording on -> see: 'AnalogInputChannel'
            sampling_frequency: rate at which data is read by the scope instrument into device buffer (Hz)
            window_func: window function used in fft calculations (see: FFTWindow. default: FFTWindow.FLAT_TOP)
            amp_range: amplitude range for the analog in measurend signal

        Returns:
            tuple of: frequency axis (MHz), frequency_bins (dbV), phase (degrees)
        """

        # check requested channels are enabled
        self._verify_channels_enable_status([input_channel])

        # the device will only be configured when FDwf###Configure is called
        self._disable_auto_configure()

        # get max buffer size for the current device config and capture up to 32k samples if possible
        _, max_buffer_size = self._get_analog_input_buffer_size_info()
        n_samples = min(32768, max_buffer_size)
        n_samples = int(2 ** round(math.log2(max_buffer_size)))

        # setup acquisition settings
        self._set_analog_input_sampling_frequency(sampling_frequency)
        self._set_analog_input_buffer_size(n_samples)

        # setup analog input channel range
        self._set_analog_input_range(input_channel.value, amp_range)

        # configure instrument and reset auto timeout
        self._stop_analog_input(reset_auto_trigger_timeout=True)

        # wait at least 2 seconds for the offset to stabilize
        time.sleep(2)

        # start Scope instrument acquisition on input_channels
        self._start_analog_input(reset_auto_trigger_timeout=True)

        hzRate = self._get_analog_input_sampling_frequency()

        # capture analog data and calculate fft
        while True:
            # read data to an internal buffer
            status = self._get_analog_input_status(read_data=True)
            # check internal buffer status
            if status == DwfStateDone.value:
                # exit loop when acquisition is done
                break

        # create empty buffer array
        buffer_data = (c_double * c_int(n_samples).value)()

        # copy device internal buffer to buffer_data
        result = self._dwf.FDwfAnalogInStatusData(
            self._hdwf,
            c_int(input_channel.value),
            buffer_data,
            c_int(n_samples),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        hzTop = hzRate / 2
        rgdWindow = (c_double * n_samples)()
        vBeta = c_double(1.0)  # used only for Kaiser window
        vNEBW = c_double()  # noise equivalent bandwidth

        # generate window function
        result = self._dwf.FDwfSpectrumWindow(
            byref(rgdWindow),
            c_int(n_samples),
            window_func.value,
            vBeta,
            byref(vNEBW),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # scale by window data
        for i in range(n_samples):
            buffer_data[i] = buffer_data[i] * rgdWindow[i]

        # requires power of two number of samples and BINs of samples/2+1
        nBins = int(n_samples / 2 + 1)
        rgdBins1 = (c_double * nBins)()
        rgdPhase1 = (c_double * nBins)()

        # perform FFT
        result = self._dwf.FDwfSpectrumFFT(
            byref(buffer_data),
            n_samples,
            byref(rgdBins1),
            byref(rgdPhase1),
            nBins,
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        sqrt2 = math.sqrt(2)
        for i in range(nBins):
            rgdBins1[i] = 20.0 * math.log10(rgdBins1[i] / sqrt2)  # to dBV

        for i in range(nBins):
            if rgdBins1[i] < -60:
                rgdPhase1[i] = 0  # mask phase at low magnitude
            else:
                rgdPhase1[i] = (
                    rgdPhase1[i] * 180.0 / math.pi
                )  # radian to degree
            if rgdPhase1[i] < 0:
                rgdPhase1[i] = 180.0 + rgdPhase1[i]

        rgMHz = []
        for i in range(nBins):
            rgMHz.append(hzTop * i / (nBins - 1) / 1e6)

        rgBins1 = np.fromiter(rgdBins1, dtype=np.float64)
        rgPhase1 = np.fromiter(rgdPhase1, dtype=np.float64)

        iPeak1 = 0
        vMax = float("-inf")
        for i in range(5, nBins):  # skip DC
            if rgBins1[i] < vMax:
                continue
            vMax = rgBins1[i]
            iPeak1 = i

        logger.info(
            f"Analog {input_channel.name} fft measured peak at frequency: {hzTop * iPeak1 / (nBins - 1) / 1000} kHz"
        )

        return (rgMHz, rgBins1, rgPhase1)

    def perform_spectrum_measurements(
        self,
        input_channel: AnalogInputChannel,
        sampling_frequency: float,
        window_func: FFTWindow = FFTWindow.FLAT_TOP,
        amp_range: float = 5,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Collect raw voltage readings from analog in channel and peforms FFT or CZT on data array and returns BINs and Phase

        Args:
            input_channel: analog input channels to start recording on -> see: 'AnalogInputChannel'
            sampling_frequency: rate at which data is read by the scope instrument into device buffer (Hz)
            window_func: window function used in fft calculations (see: FFTWindow. default: FFTWindow.FLAT_TOP)
            amp_range: amplitude range for the analog in measurend signal

        Returns:
            tuple of: frequency axis (MHz), frequency_bins (dbV)
        """

        # check requested channels are enabled
        self._verify_channels_enable_status([input_channel])

        # the device will only be configured when FDwf###Configure is called
        self._disable_auto_configure()

        # get max buffer size for the current device config and capture up to 32k samples if possible
        _, max_buffer_size = self._get_analog_input_buffer_size_info()
        n_samples = min(32768, max_buffer_size)

        # setup acquisition settings
        self._set_analog_input_sampling_frequency(sampling_frequency)
        self._set_analog_input_buffer_size(n_samples)

        # setup analog input channel range
        self._set_analog_input_range(input_channel.value, amp_range)

        # configure instrument and reset auto timeout
        self._stop_analog_input(reset_auto_trigger_timeout=True)

        # wait at least 2 seconds for the offset to stabilize
        time.sleep(2)

        # start Scope instrument acquisition on input_channels
        self._start_analog_input(reset_auto_trigger_timeout=True)

        hzRate = self._get_analog_input_sampling_frequency()

        # capture analog data and calculate fft
        while True:
            # read data to an internal buffer
            status = self._get_analog_input_status(read_data=True)
            # check internal buffer status
            if status == DwfStateDone.value:
                # exit loop when acquisition is done
                break

        # create empty buffer array
        buffer_data = (c_double * c_int(n_samples).value)()

        # copy device internal buffer to buffer_data
        result = self._dwf.FDwfAnalogInStatusData(
            self._hdwf,
            c_int(input_channel.value),
            buffer_data,
            c_int(n_samples),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        hzTop = hzRate / 2
        rgdWindow = (c_double * n_samples)()
        vBeta = c_double(1.0)  # used only for Kaiser window
        vNEBW = c_double()  # noise equivalent bandwidth

        # generate window function
        result = self._dwf.FDwfSpectrumWindow(
            byref(rgdWindow),
            c_int(n_samples),
            window_func.value,
            vBeta,
            byref(vNEBW),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # scale by window data
        for i in range(n_samples):
            buffer_data[i] = buffer_data[i] * rgdWindow[i]

        # Using power of two number of samples, BINs of samples/2+1, first 0.0 and last 1.0;
        # otherwise it will be a more resource hungry algorithm used.
        # The first and last can limit the output frequency range.
        # With 0/1 the BINs range from DC-0Hz to sample rate/2. With 0.2/0.5 the BINs will range from rate/10 to rate/4.
        # The BIN output is peak voltage and phase in radian units.
        iFirst = 0.0
        iLast = 1.0
        nBins = int(n_samples / 2 + 1)
        rgdBins1 = (c_double * nBins)()

        # Compute FFT Spectrum
        result = self._dwf.FDwfSpectrumTransform(
            byref(buffer_data),
            n_samples,
            byref(rgdBins1),
            None,
            nBins,
            c_double(iFirst),
            c_double(iLast),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        sqrt2 = math.sqrt(2)
        for i in range(nBins):
            rgdBins1[i] = 20.0 * math.log10(rgdBins1[i] / sqrt2)  # to dBV

        rgMHz = []
        MHzFirst = hzTop * iFirst / 1e6
        MHzStep = hzTop * (iLast - iFirst) / (nBins - 1) / 1e6
        for i in range(nBins):
            rgMHz.append(MHzFirst + MHzStep * i)

        rgBins1 = np.fromiter(rgdBins1, dtype=np.float64)

        return (rgMHz, rgBins1)

    def perform_sine_sweep_measurements(
        self,
        output_channel: AnalogOutputChannel,
        input_channel: AnalogInputChannel,
        freq_start: float,
        freq_stop: float,
        sweep_duration: float,
        sweep_amplitude: float,
        offset: float = 0.0,
        amp_range: float = 5,
        sampling_frequency: float = 1.0e6,
        samples_count: int = 8192,
    ) -> np.ndarray:
        """
        Play a sine sweep signal to DUT on an analog output channel and capture DUT output on an analog input channel

        Args:
            output_channel: analog output channel to play on -> see: 'AnalogOutputChannel'
            input_channel: analog input channels to start acuqisition on -> see: 'AnalogInputChannel'
            freq_start: start frequency for the sine sweep (Hz)
            freq_stop: stop frequency for the sine sweep (Hz)
            sweep_duration: duration of the sine sweep (Sec)
            sweep_amplitude: amplitude of the sine signal during the sweep (Volts)
            offset: applied offset to output signal (Volts) (default: 0.0)
            amp_range: amplitude range for the analog in measurend signal (default: 5.0 Volts)
            sampling_frequency: rate at which data is read by the scope instrument into device buffer (Hz) (default: 1 MHz)
            samples_count: number of data points to collect (less than max device buffer for a given config) (default: 8192)

        Returns:
            numpy array of captured output on input_channel during the sweeep
        """

        # check requested channels are enabled
        self._verify_channels_enable_status([input_channel, output_channel])

        # check samples_count < max_buffer_size
        _, max_buffer_size = self._get_analog_input_buffer_size_info()
        if samples_count > max_buffer_size:
            logger.warning(
                f"requested samples count: {samples_count} is greater than max buffer size of the device: {max_buffer_size}. max buffer size will be used"
            )
            samples_count = max_buffer_size

        # the device will only be configured when FDwf###Configure is called
        self._disable_auto_configure()

        # setup output_channel settings (Carrier)
        freq_mid = (freq_start + freq_stop) / 2
        self._set_analog_output_generator_function(
            output_channel.value, AnalogOutputSignal.Sine.value
        )
        self._set_analog_output_frequency(output_channel.value, freq_mid)
        self._set_analog_output_amplitude(
            output_channel.value, sweep_amplitude
        )
        self._set_analog_output_offset(output_channel.value, offset)

        # setup output_channel settings (FM)
        reutrn_codes = []
        reutrn_codes.append(
            self._dwf.FDwfAnalogOutNodeEnableSet(
                self._hdwf, output_channel.value, AnalogOutNodeFM, c_int(1)
            )
        )
        reutrn_codes.append(
            self._dwf.FDwfAnalogOutNodeFunctionSet(
                self._hdwf, output_channel.value, AnalogOutNodeFM, funcRampUp
            )
        )
        reutrn_codes.append(
            self._dwf.FDwfAnalogOutNodeFrequencySet(
                self._hdwf,
                output_channel.value,
                AnalogOutNodeFM,
                c_double(1.0 / sweep_duration),
            )
        )
        reutrn_codes.append(
            self._dwf.FDwfAnalogOutNodeAmplitudeSet(
                self._hdwf,
                output_channel.value,
                AnalogOutNodeFM,
                c_double(100.0 * (freq_stop - freq_mid) / freq_mid),
            )
        )
        reutrn_codes.append(
            self._dwf.FDwfAnalogOutNodeSymmetrySet(
                self._hdwf,
                output_channel.value,
                AnalogOutNodeFM,
                c_double(50.0),
            )
        )

        # check configuration success
        for r in reutrn_codes:
            if r != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

        # set sweep duration and repeat count to 1
        self._set_analog_output_run_duration(
            output_channel.value, sweep_duration
        )
        self._set_analog_output_repeats_count(output_channel.value, 1)

        # setup acquisition settings
        self._set_analog_input_sampling_frequency(sampling_frequency)
        self._set_analog_input_buffer_size(samples_count)
        self._set_analog_input_range(input_channel.value, amp_range)
        self._set_analog_input_trigger_source(
            AnalogTriggerSource.AnalogOut1.value, 0
        )
        self._set_analog_input_trigger_position(
            (0.3 * samples_count / sampling_frequency)
        )  # trigger position at 20%, 0.5-0.3

        # start Scope instrument acquisition on input_channel
        self._start_analog_input(reset_auto_trigger_timeout=True)

        # check analog in channel in armed state
        while True:
            # read data to an internal buffer
            status = self._get_analog_input_status(read_data=True)
            if status == DwfStateArmed.value:
                break
            time.sleep(0.1)

        logger.info(f"Analog input channel: {input_channel.name} is armed")

        time.sleep(2.0)  # wait for the offsets to stabilize

        # start output
        self._start_analog_output(output_channel.value)

        # capture analog in data
        while True:
            status = self._get_analog_input_status(read_data=True)
            if status == DwfStateDone.value:
                break
            time.sleep(0.1)

        logger.info(
            f"Analog Acquisition completed on channel: {input_channel.name}"
        )

        # create empty buffer array
        buffer_data = (c_double * c_int(samples_count).value)()

        # copy device internal buffer to buffer_data
        result = self._dwf.FDwfAnalogInStatusData(
            self._hdwf,
            c_int(input_channel.value),
            buffer_data,
            c_int(samples_count),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return np.fromiter(buffer_data, dtype=np.float64)

    def perform_netwrok_analysis(
        self,
        freq_start: float,
        freq_stop: float,
        steps: int,
        amplitude: float,
        impedance_mode: int = 0,
        reference_resistance: float = 0,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        The Network Analyzer is used to analyze transfer functions (the ratio between an output function and an input function)
        Typical usage of Network Analyzer: the WaveGen 1 output and Oscilloscope Channel 1 input of the device is connected to the filter input,
        while the Oscilloscope Channel 2 is connected to the filter output

        The analysis is performed from start to stop frequency in the specified number of steps.
        For each step, the WaveGen channel is set to a constant frequency and the Oscilloscope performs an acquisition

        Args:
            freq_start: start frequency (Hz)
            freq_stop: stop frequency (Hz)
            steps: the number of frequency steps used for the analysis
            amplitude: the amplitude of the generated signal, the peak to peak is twice of amplitude (Volts)
            impedance_mode: 0 = W1-C1-DUT-C2-R-GND, 1 = W1-C1-R-C2-DUT-GND, 8 = AD IA adapter (see WaveForms SDK reference)
            reference_resistance: the reference resistor to be used for imepdance analysis
                                when using the impedance analyzer adapter, the resistor is selected by
                                relays controlled by power supplies and digital IOs (Ohms) (default: 0)

        Returns:
           A tuple of arrays: (frequency steps ,reference gain channel 1, relative gain channel 2, phase data channel 2)
        """

        # enable dynamic adjustment of analog out settings like: frequency, amplitude...
        self._enable_dynamic_auto_configure()

        # setup netowrk (impedance) analysis settings
        reutrn_codes = []
        reutrn_codes.append(self._dwf.FDwfAnalogImpedanceReset(self._hdwf))
        reutrn_codes.append(
            self._dwf.FDwfAnalogImpedanceModeSet(
                self._hdwf, c_int(impedance_mode)
            )
        )
        reutrn_codes.append(
            self._dwf.FDwfAnalogImpedanceReferenceSet(
                self._hdwf, c_double(reference_resistance)
            )
        )
        reutrn_codes.append(
            self._dwf.FDwfAnalogImpedanceFrequencySet(
                self._hdwf, c_double(freq_start)
            )
        )
        reutrn_codes.append(
            self._dwf.FDwfAnalogImpedanceAmplitudeSet(
                self._hdwf, c_double(amplitude)
            )
        )

        # check configuration success
        for r in reutrn_codes:
            if r != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

        # start impedance analysis
        result = self._dwf.FDwfAnalogImpedanceConfigure(self._hdwf, c_int(1))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        time.sleep(2)

        # define arrays to hold status / measurements
        sts = c_byte()
        rgHz = [0.0] * steps
        rgGaC1 = [0.0] * steps
        rgGaC2 = [0.0] * steps
        rgPhC2 = [0.0] * steps

        # perform measurements over frequency steps range
        for i in range(steps):
            hz = freq_stop * pow(
                10.0,
                1.0
                * (1.0 * i / (steps - 1) - 1)
                * math.log10(freq_stop / freq_start),
            )  # exponential frequency steps
            rgHz[i] = hz

            result = self._dwf.FDwfAnalogImpedanceFrequencySet(
                self._hdwf, c_double(hz)
            )  # frequency in Hertz
            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

            time.sleep(0.01)

            # ignore last capture since we changed the frequency
            result = self._dwf.FDwfAnalogImpedanceStatus(self._hdwf, None)
            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

            # retrieve impedance data / status
            while True:
                result = self._dwf.FDwfAnalogImpedanceStatus(
                    self._hdwf, byref(sts)
                )
                if result != SUCCESS_RETURN_CODE:
                    raise PyDwfError(
                        self.get_last_error(), self.get_last_error_message()
                    )
                if sts.value == DwfStateDone.value:
                    break

            gain1 = c_double()
            gain2 = c_double()
            phase2 = c_double()

            # collect gain on analog channel 1 (relative to Wave 1)
            result = self._dwf.FDwfAnalogImpedanceStatusInput(
                self._hdwf, c_int(0), byref(gain1), 0
            )  # relative to FDwfAnalogImpedanceAmplitudeSet Amplitude/C1
            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

            result = self._dwf.FDwfAnalogImpedanceStatusInput(
                self._hdwf, c_int(1), byref(gain2), byref(phase2)
            )  # relative to Channel 1, C1/C#
            if result != SUCCESS_RETURN_CODE:
                raise PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )

            rgGaC1[i] = 1.0 / gain1.value
            rgGaC2[i] = 1.0 / gain2.value
            rgPhC2[i] = -phase2.value * 180 / math.pi

            # check for out of range warnings on scope channels (C1, C2)
            for iCh in range(2):
                warn = c_int()
                result = self._dwf.FDwfAnalogImpedanceStatusWarning(
                    self._hdwf, c_int(iCh), byref(warn)
                )
                if result != SUCCESS_RETURN_CODE:
                    raise PyDwfError(
                        self.get_last_error(), self.get_last_error_message()
                    )
                if warn.value:
                    dOff = c_double()
                    dRng = c_double()
                    result = self._dwf.FDwfAnalogInChannelOffsetGet(
                        self._hdwf, c_int(iCh), byref(dOff)
                    )
                    if result != SUCCESS_RETURN_CODE:
                        raise PyDwfError(
                            self.get_last_error(),
                            self.get_last_error_message(),
                        )
                    result = self._dwf.FDwfAnalogInChannelRangeGet(
                        self._hdwf, c_int(iCh), byref(dRng)
                    )
                    if result != SUCCESS_RETURN_CODE:
                        raise PyDwfError(
                            self.get_last_error(),
                            self.get_last_error_message(),
                        )
                    if warn.value & 1:
                        logging.warning(
                            f"Out of range on Channel :{str(iCh + 1)} <= {str(dOff.value - dRng.value / 2)} V"
                        )
                    if warn.value & 2:
                        logging.warning(
                            f"Out of range on Channel: {str(iCh + 1)} >= {str(dOff.value + dRng.value / 2)} V"
                        )

        # stop impedance measurement
        result = self._dwf.FDwfAnalogImpedanceConfigure(self._hdwf, c_int(0))
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        return (
            np.fromiter(rgHz, dtype=np.float64),
            np.fromiter(rgGaC1, dtype=np.float64),
            np.fromiter(rgGaC2, dtype=np.float64),
            np.fromiter(rgPhC2, dtype=np.float64),
        )

    ### I2C Protocol Instrument ###
    def configure_i2c(
        self,
        sda_channel: DigitalIOChannel,
        scl_channel: DigitalIOChannel,
        rate: float,
    ) -> None:
        """Configure the Analog Discovery 2 I2C instrument"""
        self._set_i2c_scl(scl_channel.value)
        self._set_i2c_sda(sda_channel.value)
        self._set_i2c_rate(rate)
        self._set_i2c_nak_read_state()
        self._clear_i2c_bus()

        time.sleep(0.100)

    def reset_i2c(self) -> None:
        """Resets the I2C configuration to default value"""
        result = self._dwf.FDwfDigitalI2cReset(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        time.sleep(0.100)

    def i2c_read(
        self, address: int, bytes_count: int
    ) -> Tuple[int, List[int]]:
        """
        Performs an I2C read

            address (int): The I2C address of the target device (the given address is later shifted to 8 bit address)
            bytes_count (int): The number of read bytes

            Returns:
            Tuple[int, List[int]]:
                The first element is the NAK indication; the second element is a list of bytes received

        """

        c_nak = c_int()
        rx_buffer = (c_ubyte * bytes_count)()
        # 8 bit address
        result = self._dwf.FDwfDigitalI2cRead(
            self._hdwf,
            c_int(address << 1),
            rx_buffer,
            c_int(bytes_count),
            byref(c_nak),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        time.sleep(0.1)

        return (c_nak.value, list(rx_buffer))

    def i2c_write(self, address: int, bytes_list: List[int]) -> int:
        """
        Performs an I2C write

            address (int): The I2C address of the target device (the given address is later shifted to 8 bit address)
            bytes_list (List[int]): list of bytes to send

        Returns:
            int: The NAK indication

        """
        c_nak = c_int()
        bytes_count = len(bytes_list)

        tx_buffer = (c_ubyte * bytes_count)(*bytes_list)
        # 8 bit address
        result = self._dwf.FDwfDigitalI2cWrite(
            self._hdwf,
            c_int(address << 1),
            tx_buffer,
            c_int(bytes_count),
            byref(c_nak),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        time.sleep(0.1)

        return c_nak.value

    def start_i2c_spy(self) -> None:
        """
        Starts an I2C Spy Session
        """
        result = self._dwf.FDwfDigitalI2cSpyStart(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

    def read_i2c_spy_data(self, max_data_size: int) -> List[Union[int, str]]:
        """
        Reads I2C data from a running spy session and return it as a standard i2c message

        Args:
            max_data_size: maximum number of bytes to decode


        Returns:
            i2c_msg: list containing Read/Write/Stop conditions with transferred bytes on the bus
        """
        start, stop, data, nak = self._get_i2c_spy_status(max_data_size)

        # create a friendly i2c message out of the status data
        i2c_msg = []
        if start == 1:
            i2c_msg.append("Start")
        elif start == 2:
            i2c_msg.append("ReStart")

        for i in range(len(data)):
            # first data is address when start is not zero
            if i == 0 and start != 0:
                i2c_msg.append(hex(data[i] >> 1))
                if data[i] & 1:
                    i2c_msg.append("RD")
                else:
                    i2c_msg.append("WR")
            else:
                i2c_msg.append(hex(data[i]))

        if stop != 0:
            i2c_msg.append("Stop")

        # NAK of data index + 1 or negative error
        if nak > 0:
            i2c_msg.append("NAK: " + str(nak))
        elif nak < 0:
            i2c_msg.append("Error: " + str(nak))

        time.sleep(0.001)

        return i2c_msg

    ### SPI Protocol Instrument ###
    def configure_spi(
        self,
        cs: DigitalIOChannel,
        scl: DigitalIOChannel,
        spi_frequency: float,
        miso: DigitalIOChannel,
        mosi: DigitalIOChannel,
        spi_mode: int = 0,
        bit_order: int = 1,
    ) -> None:
        """Configure the Analog Discovery 2 SPI instrument
        Args:
        - cs (DIO line used for chip select)
        - scl (DIO line used for serial clock)
        - miso (DIO line used for master in - slave out)
        - mosi (DIO line used for master out - slave)
        - frequency (communication frequency in Hz)
        - mode (SPI mode: 0: CPOL=0, CPHA=0; 1: CPOL-0, CPHA=1; 2: CPOL=1, CPHA=0; 3: CPOL=1, CPHA=1)
        - bit_order (endianness) (1 means MSB first (default), 0 means LSB first)
        """
        # set clock frequency
        self._set_spi_frequency(spi_frequency)

        # set the clock pin
        self._set_spi_scl(scl.value)

        # set miso/mosi lines and their initial state to Zet (high impedance)
        self._set_spi_data(mosi.value, 0)
        self._set_spi_idle_state(0, DigitalOutputIdleState.Zet.value)
        self._set_spi_data(miso.value, 1)
        self._set_spi_idle_state(1, DigitalOutputIdleState.Zet.value)

        # set the SPI mode
        self._set_spi_mode(spi_mode)

        # set endianness
        self._set_spi_endianness(bit_order)

        # set chip select line to high state
        self._set_spi_cs(cs.value, 1)

        return

    def spi_one_read(
        self, bits_count: int, cs: DigitalIOChannel, transfer_line: int = 1
    ) -> int:
        """Reads a single SPI word (up to 32) bits given bits count and chip select pin number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """

        # set chip select line low to enable it
        self._set_spi_cs(cs.value, 0)

        # variable to store recieved bits
        read_bits = c_uint()

        # read one word
        result = self._dwf.FDwfDigitalSpiReadOne(
            self._hdwf,
            c_int(transfer_line),
            c_int(bits_count),
            byref(read_bits),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # set chip select line high to disable it
        self._set_spi_cs(cs.value, 1)

        return read_bits.value

    def spi_8_bits_read(
        self, bytes_count: int, cs: DigitalIOChannel, transfer_line: int = 1
    ) -> List[int]:
        """Read 8 bits data-words from SPI bus given bytes count and chip select pin number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """

        # set chip select line low to enable it
        self._set_spi_cs(cs.value, 0)

        # create buffer to store data
        buffer = (c_ubyte * bytes_count)()

        # read array of 8 bit elements
        result = self._dwf.FDwfDigitalSpiRead(
            self._hdwf,
            c_int(transfer_line),
            c_int(8),
            buffer,
            c_int(len(buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # set chip select line high to disable it
        self._set_spi_cs(cs.value, 1)

        # place buffer data in a list
        read_data = [int(element) for element in buffer]

        return read_data

    def spi_16_bits_read(
        self, bytes_count: int, cs: DigitalIOChannel, transfer_line: int = 1
    ) -> List[int]:
        """
        Read 16 bits data-words from SPI bus given bytes count and chip select pin number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """

        # set chip select line low to enable it
        self._set_spi_cs(cs.value, 0)

        # create buffer to store data
        buffer = (c_ubyte * bytes_count)()

        # read array of 16 bit elements
        result = self._dwf.FDwfDigitalSpiRead16(
            self._hdwf,
            c_int(transfer_line),
            c_int(16),
            buffer,
            c_int(len(buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # set chip select line high to disable it
        self._set_spi_cs(cs.value, 1)

        # place buffer data in a list
        read_data = [int(element) for element in buffer]

        return read_data

    def spi_32_bits_read(
        self, bytes_count: int, cs: DigitalIOChannel, transfer_line: int = 1
    ) -> List[int]:
        """
        Read 32 bits data-words from SPI bus given bytes count and chip select pin number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """

        # set chip select line low to enable it
        self._set_spi_cs(cs.value, 0)

        # create buffer to store data
        buffer = (c_ubyte * bytes_count)()

        # read array of 32 bit elements
        result = self._dwf.FDwfDigitalSpiRead32(
            self._hdwf,
            c_int(transfer_line),
            c_int(32),
            buffer,
            c_int(len(buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # set chip select line high to disable it
        self._set_spi_cs(cs.value, 1)

        # place buffer data in a list
        read_data = [int(element) for element in buffer]

        return read_data

    def spi_one_write(
        self,
        bits_count: int,
        word: int,
        cs: DigitalIOChannel,
        transfer_line: int = 1,
    ) -> None:
        """
        Writes a single SPI word (up to 32) bits given bits count, word to transmit and chip select pin number
        transfer_line can be one of:
            0 — SISO
            1 — MOSI/MISO (default)
            2 — dual
            3 — quad
        """

        # set chip select line low to enable it
        self._set_spi_cs(cs.value, 0)

        # write one word
        result = self._dwf.FDwfDigitalSpiWriteOne(
            self._hdwf, c_int(transfer_line), c_int(bits_count), c_uint(word)
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # set chip select line high to disable it
        self._set_spi_cs(cs.value, 1)

        return

    def spi_8_bits_write(
        self, data: list, cs: DigitalIOChannel, transfer_line: int = 1
    ) -> None:
        """
        Writes 8 bits data through SPI bus given data-words list to send and chip select line number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """

        # enable chip select line
        self._set_spi_cs(cs.value, 0)

        # create buffer to write
        bytes_data = bytes(data, "utf-8")
        buffer = (c_ubyte * len(bytes_data))()
        for index in range(0, len(buffer)):
            buffer[index] = c_ubyte(bytes_data[index])

        result = self._dwf.FDwfDigitalSpiWrite(
            self._hdwf,
            c_int(transfer_line),
            c_int(8),
            buffer,
            c_int(len(buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # disable chip select line
        self._set_spi_cs(cs.value, 1)

        return

    def spi_16_bits_write(
        self, data: list, cs: DigitalIOChannel, transfer_line: int = 1
    ) -> None:
        """
        Writes 16 bits data through SPI bus given data-words list to send and chip select line number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """

        # enable chip select line
        self._set_spi_cs(cs.value, 0)

        # create buffer to write
        bytes_data = bytes(data, "utf-8")
        buffer = (c_ubyte * len(bytes_data))()
        for index in range(0, len(buffer)):
            buffer[index] = c_ubyte(bytes_data[index])

        result = self._dwf.FDwfDigitalSpiWrite16(
            self._hdwf,
            c_int(transfer_line),
            c_int(16),
            buffer,
            c_int(len(buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # disable chip select line
        self._set_spi_cs(cs.value, 1)

        return

    def spi_32_bits_write(
        self, data: list, cs: DigitalIOChannel, transfer_line: int = 1
    ) -> None:
        """
        Writes 32 bits data through SPI bus given data-words list to send and chip select line number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """

        # enable chip select line
        self._set_spi_cs(cs.value, 0)

        # create buffer to write
        bytes_data = bytes(data, "utf-8")
        buffer = (c_ubyte * len(bytes_data))()
        for index in range(0, len(buffer)):
            buffer[index] = c_ubyte(bytes_data[index])

        result = self._dwf.FDwfDigitalSpiWrite32(
            self._hdwf,
            c_int(transfer_line),
            c_int(32),
            buffer,
            c_int(len(buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # disable chip select line
        self._set_spi_cs(cs.value, 1)

        return

    def spi_8_bits_exchnage(
        self,
        data,
        bytes_count: int,
        cs: DigitalIOChannel,
        transfer_line: int = 1,
    ) -> List[int]:
        """
        Sends and recieves 8 bits data-words through SPI given data list to send, number of bytes to read and chip select line number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """
        # enable chip select line
        self._set_spi_cs(cs.value, 0)

        # create buffer to store read data
        rx_buffer = (c_ubyte * bytes_count)()

        # create buffer to write
        bytes_data = bytes(data, "utf-8")
        tx_buffer = (c_ubyte * len(bytes_data))()
        for index in range(0, len(tx_buffer)):
            tx_buffer[index] = c_ubyte(bytes_data[index])

        # perform spi transfer
        result = self._dwf.FDwfDigitalSpiWriteRead(
            self._hdwf,
            c_int(transfer_line),
            c_int(8),
            tx_buffer,
            c_int(len(tx_buffer)),
            rx_buffer,
            c_int(len(rx_buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # place rx_buffer data in a list
        read_data = [int(element) for element in rx_buffer]

        # disable chip select line
        self._set_spi_cs(cs.value, 1)

        return read_data

    def spi_16_bits_exchnage(
        self,
        data,
        bytes_count: int,
        cs: DigitalIOChannel,
        transfer_line: int = 1,
    ) -> List[int]:
        """
        Sends and recieves 16 bits data-words through SPI given data list to send, number of bytes to read and chip select line number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """
        # enable chip select line
        self._set_spi_cs(cs.value, 0)

        # create buffer to store read data
        rx_buffer = (c_ubyte * bytes_count)()

        # create buffer to write
        bytes_data = bytes(data, "utf-8")
        tx_buffer = (c_ubyte * len(bytes_data))()
        for index in range(0, len(tx_buffer)):
            tx_buffer[index] = c_ubyte(bytes_data[index])

        # perform spi transfer
        result = self._dwf.FDwfDigitalSpiWriteRead16(
            self._hdwf,
            c_int(transfer_line),
            c_int(16),
            tx_buffer,
            c_int(len(tx_buffer)),
            rx_buffer,
            c_int(len(rx_buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # place rx_buffer data in a list
        read_data = [int(element) for element in rx_buffer]

        # disable chip select line
        self._set_spi_cs(cs.value, 1)

        return read_data

    def spi_32_bits_exchnage(
        self,
        data,
        bytes_count: int,
        cs: DigitalIOChannel,
        transfer_line: int = 1,
    ) -> List[int]:
        """
        Sends and recieves 32 bits data-words through SPI given data list to send, number of bytes to read and chip select line number
        transfer_line can be one of:
        0 — SISO
        1 — MOSI/MISO (default)
        2 — dual
        3 — quad
        """

        # enable chip select line
        self._set_spi_cs(cs.value, 0)

        # create buffer to store read data
        rx_buffer = (c_ubyte * bytes_count)()

        # create buffer to write
        bytes_data = bytes(data, "utf-8")
        tx_buffer = (c_ubyte * len(bytes_data))()
        for index in range(0, len(tx_buffer)):
            tx_buffer[index] = c_ubyte(bytes_data[index])

        # perform spi transfer
        result = self._dwf.FDwfDigitalSpiWriteRead32(
            self._hdwf,
            c_int(transfer_line),
            c_int(32),
            tx_buffer,
            c_int(len(tx_buffer)),
            rx_buffer,
            c_int(len(rx_buffer)),
        )
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )

        # place rx_buffer data in a list
        read_data = [int(element) for element in rx_buffer]

        # disable chip select line
        self._set_spi_cs(cs.value, 1)

        return read_data

    def reset_spi(self) -> None:
        """Resets the SPI configuration to default value"""
        result = self._dwf.FDwfDigitalSpiReset(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise PyDwfError(
                self.get_last_error(), self.get_last_error_message()
            )
        time.sleep(0.100)

    ### Digital StaticIO Instrument ###

    def get_digital_io_channel_state(self, channel: DigitalIOChannel) -> bool:
        """
        Gets the input states of all digital I/O channels and returns the current
        digital state of a channel in boolen form

        Returns:
            True: if channel is in HIGH state
            False:  if channel is in LOW state

        """
        # load internal buffer with current state of the pins (important to call first to get latest staus data)
        result = self._dwf.FDwfDigitalIOStatus(self._hdwf)
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

        # get the current state of the pins
        state = c_uint32()  # variable for this current state
        result = self._dwf.FDwfDigitalIOInputStatus(self._hdwf, byref(state))
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

        # convert the state to a 16 character binary string
        data = list(bin(state.value)[2:].zfill(16))

        # check the required bit
        if data[15 - channel.value] != "0":
            ch_state = True
        else:
            ch_state = False

        return ch_state

    def set_digital_io_channel_state(
        self, channel: DigitalIOChannel, state: bool
    ) -> None:
        """
        Sets the output logic value on a digital I/O channel specified in boolen form

        state:
            True: channel is set to HIGH state
            False: channel is set to LOW state

        """
        # load current state of the output state buffer
        mask = c_uint16()
        result = self._dwf.FDwfDigitalIOOutputGet(self._hdwf, byref(mask))
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

        # convert mask to list
        mask = list(bin(mask.value)[2:].zfill(16))

        # set bit in mask to requested state
        if state:
            mask[15 - channel.value] = "1"  # High
        else:
            mask[15 - channel.value] = "0"  # Low

        # convert mask to number
        mask = "".join(element for element in mask)
        mask = int(mask, 2)

        # set the channel state
        result = self._dwf.FDwfDigitalIOOutputSet(self._hdwf, c_int(mask))
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

    def get_digital_io_channel_mode(self, channel: DigitalIOChannel) -> bool:
        """
        Gets current digital I/O channel mode

        Return:
            True: channel is currently set as Output
            False: channel is currently set as Input

        """
        # load current state of the output enable buffer
        mask = c_uint16()
        result = self._dwf.FDwfDigitalIOOutputEnableGet(
            self._hdwf, byref(mask)
        )
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

        # convert mask to list
        mask = list(bin(mask.value)[2:].zfill(16))

        # check the required bit
        if mask[15 - channel.value] != "0":
            ch_state = True
        else:
            ch_state = False

        return ch_state

    def set_digital_io_channel_mode(
        self, channel: DigitalIOChannel, mode: bool
    ) -> None:
        """
        Set digital I/O channel mode as Input/Output based on boolean value

        mode:
            True: channel is set as Output
            False: channel is set as Input

        """
        # load current state of the output enable buffer
        mask = c_uint16()
        result = self._dwf.FDwfDigitalIOOutputEnableGet(
            self._hdwf, byref(mask)
        )
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )

        # convert mask to list
        mask = list(bin(mask.value)[2:].zfill(16))

        # set bit in mask to request mode
        if mode:
            mask[15 - channel.value] = "1"  # Output
        else:
            mask[15 - channel.value] = "0"  # Input

        # convert mask to number
        mask = "".join(element for element in mask)
        mask = int(mask, 2)

        # set the pin to output
        result = self._dwf.FDwfDigitalIOOutputEnableSet(
            self._hdwf, c_int(mask)
        )
        if result != SUCCESS_RETURN_CODE:
            raise (
                PyDwfError(
                    self.get_last_error(), self.get_last_error_message()
                )
            )


## Context managers for the Analog Discovery instruments ###
class AnalogDiscoveryScopeWaveGenContext:
    """
    Context manager of the Analog Disocvery during waveform generation / acquistion of analog data
    """

    # initialize the context manager
    def __init__(
        self,
        channels: List[Union[AnalogInputChannel, AnalogOutputChannel]],
        ad_config_n: int = 1,
    ):
        """
        Context constructor
        args:
            ad_config_n: analog disocvery configuration to use for the session (see WaveForms SDK Reference Manual)
            channels: list of AnalogInputChannel/AnalogOutputChannel channels to enable in the context
        """
        self.ad_config_n = ad_config_n
        self.channels = channels
        self.ad_wrapper = AnalogDiscoveryWrapper()

    def __enter__(self):
        self.ad_wrapper.open_connection(self.ad_config_n)
        for ch in self.channels:
            self.ad_wrapper.enable_analog_channel(ch)
        return self.ad_wrapper

    def __exit__(self, exc_type, exc_value, traceback):
        self.ad_wrapper._enable_dynamic_auto_configure()
        self.ad_wrapper._reset_analog_input_config()
        for ch in self.channels:
            self.ad_wrapper._reset_analog_output_config(ch.value)
        self.ad_wrapper.close_connection()


class AnalogDiscoveryI2CContext:
    """
    Context manger to control the I2C digital interface of the Analog Discovery
    """

    def __init__(
        self,
        SDA_channel: DigitalIOChannel,
        SCL_channel: DigitalIOChannel,
        I2C_rate_hz: float = 1e5,
        ad_config_n: int = 1,
    ):
        """
        Context constructor

        args:
            SDA_channel: Data digital channel to use (enum of type DigitalIOChannel)
            SCL_channel: Clock digital channel to use (enum of type DigitalIOChannel)
            I2C_rate_hz: I2C operating frequency in Hz (default 100 kHZ)
            ad_config_n: analog disocvery configuration to use for the session (see WaveForms SDK Reference Manual)

        """
        self.SDA_channel = SDA_channel
        self.SCL_channel = SCL_channel
        self.I2C_rate_hz = I2C_rate_hz
        self.ad_config_n = ad_config_n
        self.ad_wrapper = AnalogDiscoveryWrapper()

    def __enter__(self):
        self.ad_wrapper.open_connection(self.ad_config_n)
        try:
            self.ad_wrapper.configure_i2c(
                self.SDA_channel, self.SCL_channel, self.I2C_rate_hz
            )
            return self.ad_wrapper
        except RuntimeError:
            self.ad_wrapper.close_connection()
            raise

    def __exit__(self, exc_type, exc_value, traceback):
        self.ad_wrapper.reset_i2c()
        self.ad_wrapper.close_connection()


class AnalogDiscoveryDigitalIOContext:
    """
    Context manger to control the digital IO channels of
    the Analog Discovery
    """

    def __init__(
        self,
        digital_input_channels: List[DigitalIOChannel],
        digital_output_channels: List[DigitalIOChannel],
        ad_config_n: int = 1,
    ):
        """
        Context constructor

        args:
            digital_input_channels: digital channels to be set as inputs
            digital_output_channels: digital channels to be set as outputs
            ad_config_n: analog disocvery configuration to use for the session (see WaveForms SDK Reference Manual)

        """
        self.dio_inputs = digital_input_channels
        self.dio_outputs = digital_output_channels
        self.ad_config_n = ad_config_n
        self.ad_wrapper = AnalogDiscoveryWrapper()

    def __enter__(self):
        self.ad_wrapper.open_connection(self.ad_config_n)
        # digital inputs
        for ch in self.dio_inputs:
            self.ad_wrapper.set_digital_io_channel_mode(ch, False)

        # digital outputs
        for ch in self.dio_outputs:
            self.ad_wrapper.set_digital_io_channel_mode(ch, True)

        return self.ad_wrapper

    def __exit__(self, exc_type, exc_value, traceback):
        logger.debug("Resetting Digital IO Instrument ...")
        self.ad_wrapper._reset_digital_io_config()
        self.ad_wrapper.close_connection()


class AnalogDiscoveryPowerSupplyContext:
    """
    Context manger to control the supplies of
    the Analog Discovery 2, 3
    """

    def __init__(
        self,
        positive_supply_voltage: float,
        negative_supply_voltage: Optional[float] = None,
        ad_config_n: int = 1,
    ):
        """
        Context constructor

        args:
            positive_supply_voltage: V+ value to set in volts
            negative_supply_voltage: V- value to set in volts (by default the negative supply is disabled if V- is none)
            ad_config_n: analog disocvery configuration to use for the session (see WaveForms SDK Reference Manual)

        """
        self.positive_supply_voltage = positive_supply_voltage
        self.negative_supply_voltage = negative_supply_voltage
        self.ad_wrapper = AnalogDiscoveryWrapper()
        self.ad_config_n = ad_config_n

    def __enter__(self):
        self.ad_wrapper.open_connection(self.ad_config_n)
        self.ad_wrapper.configure_power_supply(
            self.positive_supply_voltage, self.negative_supply_voltage
        )
        return self.ad_wrapper

    def __exit__(self, exc_type, exc_value, traceback):
        self.ad_wrapper._reset_analog_io_config()
        self.ad_wrapper.close_connection()


class AnalogDiscoverySPIContext:
    """
    Context manger to control the SPI digital interface of
    the Analog Discovery
    """

    def __init__(
        self,
        clk_channel: DigitalIOChannel,
        cs_channel: DigitalIOChannel,
        frequency_hz: float,
        miso: DigitalIOChannel,
        mosi: DigitalIOChannel,
        mode: int = 0,
        bit_order: int = 1,
        ad_config_n: int = 1,
    ):
        """
        Context constructor

        args:
            - clk_channel: Clock digital channel to use (enum of type DigitalIOChannel)
            - cs_channel: Chip select digital channel to use (enum of type DigitalIOChannel)
            - miso (DIO line used for master in - slave out)(enum of type DigitalIOChannel)
            - mosi (DIO line used for master out - slave)(enum of type DigitalIOChannel)
            - frequency_hz (communication frequency in Hz)
            - mode (SPI mode: 0: CPOL=0, CPHA=0; 1: CPOL-0, CPHA=1; 2: CPOL=1, CPHA=0; 3: CPOL=1, CPHA=1)
            - bit_order (endianness) (1 means MSB first (default), 0 means LSB first)
            - ad_config_n: analog disocvery configuration to use for the session (see WaveForms SDK Reference Manual)


        """
        self.spi_cs = cs_channel
        self.spi_clk = clk_channel
        self.spi_frequency = frequency_hz
        self.miso = miso
        self.mosi = mosi
        self.mode = mode
        self.bit_order = bit_order
        self.ad_wrapper = AnalogDiscoveryWrapper()
        self.ad_config_n = ad_config_n

    def __enter__(self):
        self.ad_wrapper.open_connection(self.ad_config_n)
        self.ad_wrapper.configure_spi(
            self.spi_cs,
            self.spi_clk,
            self.spi_frequency,
            self.miso,
            self.mosi,
            self.mode,
            self.bit_order,
        )
        return self.ad_wrapper

    def __exit__(self, exc_type, exc_value, traceback):
        self.ad_wrapper.reset_spi()
        self.ad_wrapper.close_connection()


### Multiprocessing worker Analog Discovery ###
class AnalogDiscoveryScopeWorker(mp.Process):
    """A subclass of process class to run analog discovery scope function in parallel process"""

    def __init__(self, reuest_queue, response_queue, ad_config_n: int = 1):
        super(AnalogDiscoveryScopeWorker, self).__init__()
        self.request_queue = reuest_queue
        self.response_queue = response_queue
        self.ad_config_n = ad_config_n

    def run(self):
        # handle incoming requests from the request queue until STOP condition
        for request in iter(self.request_queue.get, "STOP"):
            (
                scope_mode,
                scope_channels,
                n_samples,
                sampling_frequency,
                scope_range,
                scan_duration,
            ) = request
            with AnalogDiscoveryScopeWaveGenContext(
                scope_channels, self.ad_config_n
            ) as scope:
                if scope_mode == "RECORD":
                    scope.record_analog_signal(
                        scope_channels, sampling_frequency, range=scope_range
                    )
                    response = scope.fill_recorded_samples_on_channels(
                        scope_channels, n_samples
                    )
                    self.response_queue.put(response)
                elif scope_mode == "SCAN":
                    scope.start_analog_screen(
                        scope_channels,
                        sampling_frequency,
                        n_samples,
                        scope_range,
                    )
                    response = scope.retrieve_analog_screen(
                        scope_channels, n_samples, scan_duration
                    )
                    self.response_queue.put(response)
