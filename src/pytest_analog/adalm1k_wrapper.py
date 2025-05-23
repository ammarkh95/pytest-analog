"""
Wrapper for ADALM1K SMU/Scope Module

The wrapper uses the libSMU library bindings to communicate with the module
https://wiki.analog.com/university/tools/m1k

# Important: libsmu need to be installed:
# (https://wiki.analog.com/university/tools/m1k/libsmu)
# (https://test.pypi.org/project/pysmu)

"""

import logging
import time
import multiprocessing as mp
from enum import Enum
from typing import List, Tuple

logger = logging.getLogger("ADALM1K-Wrapper")
logger.setLevel(logging.DEBUG)

try:
    from pysmu import Session, Mode
except ModuleNotFoundError:
    raise ModuleNotFoundError(
        "pysmu /libsmu library not insalled for ADALM1K. please install package and drivers from: https://test.pypi.org/project/pysmu / https://wiki.analog.com/university/tools/m1k/libsmu"
    )


class AnalogChannel(Enum):
    """
    Enumeration of ADALM1K analog channels
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    CH_A = "A"
    CH_B = "B"


class AnalogChannelMode(Enum):
    """
    Available modes for Analog channels
    """

    @classmethod
    def list(cls):
        return list(map(lambda c: cls.__name__ + "." + c.name, cls))

    HI_Z = Mode.HI_Z  # floating
    SVMI = Mode.SVMI  # source voltage, measure current
    SIMV = Mode.SIMV  # source current, measure voltage
    HI_Z_SPLIT = Mode.HI_Z_SPLIT  # floating with Split I/Os
    SVMI_SPLIT = (
        Mode.SVMI_SPLIT
    )  # source voltage, measure current with Split I/Os
    SIMV_SPLIT = (
        Mode.SIMV_SPLIT
    )  # source voltage, measure current with Split I/Os


class ADALM1KWrapper:
    """Wrapper class for utilitzing the source control and measure functions of ADALM1K module"""

    def __init__(self) -> None:
        """Iniitalize libsmu session to connect to ADALM1K module"""
        self._session = Session()
        self._device = None

    def open(self) -> None:
        """Opens the connection to first detected ADALM-M1K"""
        if self._session.devices:
            # Grab the first device from the session.
            self._device = self._session.devices[0]
            logger.info(
                f"Opened connection to ADALM1K device: {str(self._device)}"
            )

        else:
            raise RuntimeError(
                "Could not detect any ADALM-M1K devices. Make sure it is connected via USB"
            )

    def close(self) -> None:
        """Closes the connection session to connected device"""
        self._session._close()
        logger.info("Closed connection session to ADALM1K device")

    def get_overcurrent_status(self) -> bool:
        """Return the overcurrent status related to the most recent data acquisition"""
        return bool(self._device.overcurrent)

    def get_channel_mode(self, channel: AnalogChannel) -> AnalogChannelMode:
        """Get analog channel mode"""
        return AnalogChannelMode(self._device.channels[channel.value].mode)

    def set_channel_mode(
        self, channel: AnalogChannel, mode: AnalogChannelMode
    ) -> None:
        """Set analog channel mode"""
        self._device.channels[channel.value].mode = mode.value

    def set_channel_constant_output(
        self, channel: AnalogChannel, value: float
    ) -> None:
        """Set analog channel output to a constant waveform"""
        self._device.channels[channel.value].constant(value)

    def set_channel_square_output(
        self,
        channel: AnalogChannel,
        mid_point: float,
        peak: float,
        period: float,
        phase: float,
        duty: float,
        cyclic=True,
    ) -> None:
        """
        Set analog channel output to a square waveform
        Args:
            mid_point: value at the middle of the wave
            peak: maximum value of the wave
            period: number of samples the wave takes for one cycle
            phase: position in time (sample number) that the wave starts at
            duty: duty cycle of the waveform (fraction of time in which the
                signal is active, e.g. 0.5 is half the time)
            cyclic (boolean, default: True): repeat the waveform when arriving at its end
        """
        self._device.channels[channel.value].square(
            mid_point, peak, period, phase, duty, cyclic=cyclic
        )

    def set_channel_sawtooth_output(
        self,
        channel: AnalogChannel,
        mid_point: float,
        peak: float,
        period: float,
        phase: float,
        cyclic=True,
    ) -> None:
        """
        Set analog channel output to a sawtooth waveform
        Args:
            mid_point: value at the middle of the wave
            peak: maximum value of the wave
            period: number of samples the wave takes for one cycle
            phase: position in time (sample number) that the wave starts at
            cyclic (boolean, default: True): repeat the waveform when arriving at its end
        """
        self._device.channels[channel.value].sawtooth(
            mid_point, peak, period, phase, cyclic=cyclic
        )

    def set_channel_stairstep_output(
        self,
        channel: AnalogChannel,
        mid_point: float,
        peak: float,
        period: float,
        phase: float,
        cyclic=True,
    ) -> None:
        """
        Set analog channel output to a stairstep waveform
        Args:
            mid_point: value at the middle of the wave
            peak: maximum value of the wave
            period: number of samples the wave takes for one cycle
            phase: position in time (sample number) that the wave starts at
            cyclic (boolean, default: True): repeat the waveform when arriving at its end
        """
        self._device.channels[channel.value].stairstep(
            mid_point, peak, period, phase, cyclic=cyclic
        )

    def set_channel_sine_output(
        self,
        channel: AnalogChannel,
        mid_point: float,
        peak: float,
        period: float,
        phase: float,
        cyclic=True,
    ) -> None:
        """
        Set analog channel output to a sine waveform
        Args:
            mid_point: value at the middle of the wave
            peak: maximum value of the wave
            period: number of samples the wave takes for one cycle
            phase: position in time (sample number) that the wave starts at
            cyclic (boolean, default: True): repeat the waveform when arriving at its end
        """
        self._device.channels[channel.value].sine(
            mid_point, peak, period, phase, cyclic=cyclic
        )

    def set_channel_triangle_output(
        self,
        channel: AnalogChannel,
        mid_point: float,
        peak: float,
        period: float,
        phase: float,
        cyclic=True,
    ) -> None:
        """
        Set analog channel output to a triangle waveform

        Args:
            mid_point: value at the middle of the wave
            peak: maximum value of the wave
            period: number of samples the wave takes for one cycle
            phase: position in time (sample number) that the wave starts at
            cyclic (boolean, default: True): repeat the waveform when arriving at its end
        """
        self._device.channels[channel.value].triangle(
            mid_point, peak, period, phase, cyclic=cyclic
        )

    def set_leds(self, leds: int) -> None:
        """Set device LEDs.

        Args:
            leds: an integer number, the bits of the number represents the states of the leds (1-on 0-off) in order (RGB or DS3,DS2,DS1 on rev F)
        """
        self._device.set_led(leds)

    def get_channel_signal_info(
        self, channel: AnalogChannel
    ) -> Tuple[str, float, float, float]:
        """Get analog channel configured signal properties"""
        ch_signal_info = self._device.channels[channel.value].signal
        return (
            ch_signal_info.label,
            ch_signal_info.min,
            ch_signal_info.max,
            ch_signal_info.resolution,
        )

    def read_all(
        self, n_samples: int, timeout: float = 0
    ) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Acquire all signal samples from a device.

        Args:
        n_samples (int): number of samples to read
        timeout (int, optional): amount of time in milliseconds to wait for samples to be available.
        - If 0 (the default), return immediately.
        - If -1, block indefinitely until the requested number of samples is returned.

        """
        data = self._device.read(n_samples, timeout=timeout)
        return data

    def read(
        self, channel: AnalogChannel, n_samples: int, timeout: float = 0
    ) -> List[Tuple[float, float]]:
        """
        acquires samples from a channel

        Args:
            n_samples (int): number of samples to read
            timeout (int, optional): amount of time in milliseconds to wait for samples to be available.
            - If 0 (the default), return immediately.
            - If -1, block indefinitely until the requested number of samples is returned.

        """
        data = self._device.channels[channel.value].read(
            n_samples, timeout=timeout
        )
        return data

    def write(
        self, channel: AnalogChannel, data: List, cyclic: bool = False
    ) -> None:
        """
        write data to a channel

        Args:
            data: iterable of sample values
            cyclic (bool, default: False): continuously iterate over the same buffer

        """
        self._device.channels[channel.value].write(data, cyclic=cyclic)

    def flush_channel_write(self, channel: AnalogChannel) -> None:
        """Flush a channel write queue"""
        self._device.channels[channel.value].flush()

    def flush(self) -> None:
        """Flush the read and write queues for all devices in a session"""
        self._session.flush()

    def control_transfer(
        self,
        bm_request_type: int,
        b_request: int,
        wValue: int,
        wIndex: int,
        data: int,
        wLength: int,
        timeout,
    ) -> List:
        """Perform raw USB control transfers.

        The arguments map directly to those of the underlying
        libusb_control_transfer call.

        Args:
            bm_request_type: the request type field for the setup packet
            b_request: the request field for the setup packet
            wValue: the value field for the setup packet
            wIndex: the index field for the setup packet
            data: a suitably-sized data buffer for either input or output
            wLength: the length field for the setup packet
            timeout: timeout (in milliseconds) that this function should wait
                before giving up due to no response being received

        Returns: the number of bytes actually transferred
        """
        return_bytes = self._device.ctrl_transfer(
            bm_request_type, b_request, wValue, wIndex, data, wLength, timeout
        )
        return return_bytes

    def get_samples_all(
        self, n_samples: int
    ) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Acquire all signal samples from a device in a non-continuous fashion.

        Blocks until the requested number of samples is available.

        Two channels worth of data.
        Each channel's sample contains a voltage and current value.
        """
        samples = self._device.get_samples(n_samples)
        return samples

    def get_samples(
        self, channel: AnalogChannel, n_samples: int
    ) -> List[Tuple[float, float]]:
        """
        Acquire samples from a channel in a non-continuous fashion.
        Blocks until the requested number of samples is available.

        Each sample contains a voltage and current value.

        """
        samples = self._device.channels[channel.value].get_samples(n_samples)
        return samples

    def start_capture(self, n_samples: int = 0) -> None:
        """
        Start the currently configured capture, but do not wait for it to complete.

        Args:
            n_samples (int): Number of samples to capture before stopping.
                            If 0 (default) run in continuous mode.
        """
        self._session.start(int(n_samples))

    def run_capture(self, n_samples: int = 0) -> None:
        """Run the configured capture for a certain number of samples.

        Args:
            samples (int): Number of samples to run the session for.
                If 0, run in continuous mode.
        """
        self._session.run(int(n_samples))

    def cancel_capture(self) -> None:
        """Cancel the current capture and block while waiting for completion"""
        self._session.cancel()

    def end_capture(self) -> None:
        """Block until all devices have completed, then turn off the devices"""
        self._session.end()

    def get_capture_continuous_status(self) -> bool:
        """Continuous status of a session."""
        return bool(self._session.continuous)

    def get_capture_cancel_status(self) -> bool:
        """Cancellation status of a session."""
        return bool(self._session.cancelled)

    def get_capture_sample_rate(self) -> int:
        """Session sample rate in Hz"""
        return int(self._session.sample_rate)

    def set_capture_sample_rate(self, sample_rate: int) -> None:
        """Session sample rate in Hz"""
        self._session.configure(sample_rate)

    def get_capture_queue_size(self) -> int:
        """Input/output sample queue size."""
        return int(self._session.queue_size)


### Context manager for the ADALM1K ###
class SMUContext:
    """
    Context manger to access adalm1k board and configure its channels
    """

    def __init__(
        self,
        ch_a_mode: AnalogChannelMode,
        ch_b_mode: AnalogChannelMode,
        ch_a_dc_output: float = 0.0,
        ch_b_dc_output: float = 0.0,
        n_samples: int = 0,
    ):  # n_samples = 0 runs the device capture in continous mode
        self.adalm1k = ADALM1KWrapper()
        self.ch_a_mode = ch_a_mode
        self.ch_b_mode = ch_b_mode
        self.ch_a_dc_output = ch_a_dc_output
        self.ch_b_dc_output = ch_b_dc_output
        self.n_samples = n_samples

    def __enter__(self):
        self.adalm1k.open()
        self.adalm1k.set_channel_mode(AnalogChannel.CH_A, self.ch_a_mode)
        self.adalm1k.set_channel_mode(AnalogChannel.CH_B, self.ch_b_mode)
        self.adalm1k.set_channel_constant_output(
            AnalogChannel.CH_A, self.ch_a_dc_output
        )
        self.adalm1k.set_channel_constant_output(
            AnalogChannel.CH_B, self.ch_b_dc_output
        )
        time.sleep(1)  # allow sometime for output to stabilize
        self.adalm1k.start_capture(self.n_samples)

        return self.adalm1k

    def __exit__(self, exc_type, exc_value, traceback):
        self.adalm1k.set_channel_mode(
            AnalogChannel.CH_A, AnalogChannelMode.HI_Z
        )
        self.adalm1k.set_channel_mode(
            AnalogChannel.CH_B, AnalogChannelMode.HI_Z
        )
        self.adalm1k.end_capture()
        self.adalm1k.close()


### Multiprocessing Worker ADALM1K ###
class SMUWorker(mp.Process):
    """A subclass of process class to run adalm1k source/measure function in parallel process"""

    def __init__(self, reuest_queue, response_queue):
        super(SMUWorker, self).__init__()
        self.request_queue = reuest_queue
        self.response_queue = response_queue

    def run(self):
        self.adalm1k = ADALM1KWrapper()
        self.adalm1k.open()
        # handle incoming requests from the request queue until STOP condition
        for request in iter(self.request_queue.get, "STOP"):
            ch_a_mode, ch_b_mode, ch_a_dc_output, ch_b_dc_output, n_samples = (
                request
            )
            # configure adalm1k channels
            self.adalm1k.set_channel_mode(AnalogChannel.CH_A, ch_a_mode)
            self.adalm1k.set_channel_mode(AnalogChannel.CH_B, ch_b_mode)
            self.adalm1k.set_channel_constant_output(
                AnalogChannel.CH_A, ch_a_dc_output
            )
            self.adalm1k.set_channel_constant_output(
                AnalogChannel.CH_B, ch_b_dc_output
            )

            # start adalm1k session, get samples and put result on the response queue
            response = self.adalm1k.get_samples_all(n_samples)
            self.response_queue.put(response)

        # STOP condition
        self.adalm1k.set_channel_mode(
            AnalogChannel.CH_A, AnalogChannelMode.HI_Z
        )
        self.adalm1k.set_channel_mode(
            AnalogChannel.CH_B, AnalogChannelMode.HI_Z
        )
        self.adalm1k.close()
