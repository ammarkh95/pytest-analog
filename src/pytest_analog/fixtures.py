import pytest
from _pytest.config import Config
from .analog_discovery_wrapper import (
    AnalogDiscoveryWrapper,
    AnalogInputChannel,
    AnalogOutputChannel,
)
from .adalm1k_wrapper import ADALM1KWrapper, AnalogChannel, AnalogChannelMode
from typing import Generator
import logging
import time


# Fixtures for the Analog Discovery
#########################################################
@pytest.fixture(scope="session")
def analog_discovery(
    pytestconfig: Config,
) -> Generator[AnalogDiscoveryWrapper, None, None]:
    """Initialize an instance of AnalogDiscoveryWrapper and opens connection to first connected analog device"""
    analog_discovery_wrapper = AnalogDiscoveryWrapper()
    analog_discovery_wrapper.open_connection(
        pytestconfig.getini("analog_discovery_config_number")
    )
    yield analog_discovery_wrapper
    analog_discovery_wrapper.close_connection()


@pytest.fixture
def analog_discovery_supplies(
    analog_discovery: AnalogDiscoveryWrapper, pytestconfig: Config
) -> Generator[AnalogDiscoveryWrapper, None, None]:
    """Enable power supply Analog IO channels of analog discovery with iniitial set voltages"""
    # NOTE: this fixture works for analog discovery 2 , 3 models
    if not pytestconfig.getini(
        "analog_discovery_supplies_positive_voltage"
    ) or not pytestconfig.getini("analog_discovery_supplies_negative_voltage"):
        raise RuntimeError(
            "Undefined value(s) for analog discovery supplies positive / negative voltage. Please provide both supply voltages"
        )

    analog_discovery.configure_power_supply(
        float(
            pytestconfig.getini("analog_discovery_supplies_positive_voltage")
        ),
        float(
            pytestconfig.getini("analog_discovery_supplies_negative_voltage")
        ),
    )
    analog_discovery.enable_power_supply()
    yield analog_discovery
    analog_discovery.disable_power_supply()


@pytest.fixture
def analog_discovery_scope_wavegen(
    analog_discovery: AnalogDiscoveryWrapper,
) -> Generator[AnalogDiscoveryWrapper, None, None]:
    """Enables all scope / wavegen Analog channels of analog discovery"""
    scope_and_wavegen_channles = [
        AnalogInputChannel.Channel1,
        AnalogInputChannel.Channel2,
        AnalogOutputChannel.WaveGen1,
        AnalogOutputChannel.WaveGen2,
    ]
    for ch in scope_and_wavegen_channles:
        analog_discovery.enable_analog_channel(ch)
    yield analog_discovery
    analog_discovery._enable_dynamic_auto_configure()
    analog_discovery._reset_analog_input_config()
    for ch in scope_and_wavegen_channles:
        analog_discovery._reset_analog_output_config(ch.value)


# Fixtures for ADALM1K (Source Measure Unit Module)
###################################################
@pytest.fixture
def adalm1k() -> Generator[ADALM1KWrapper, None, None]:
    """Initialize ADALM1K wrapper and setup connection with a detect ADALM1K board"""
    adalm1k_wrapper = ADALM1KWrapper()
    adalm1k_wrapper.open()
    yield (adalm1k_wrapper)
    adalm1k_wrapper.close()


@pytest.fixture
def adalm1k_voltage_source(
    adalm1k: ADALM1KWrapper, pytestconfig: Config
) -> Generator[ADALM1KWrapper, None, None]:
    """Setup ADALM1K analog channels to output a specifed voltage [source voltage / measure current] mode"""

    ch_a_v = pytestconfig.getini("adalm1k_ch_a_voltage")
    ch_b_v = pytestconfig.getini("adalm1k_ch_b_voltage")

    if not ch_a_v or not ch_b_v:
        raise RuntimeError(
            "Undefined value(s) for adalm1k channels voltage source. Please provide both chennels voltages"
        )

    logging.info(
        f"Setting ADALM1K Channels to Source Voltage / Measure Current: CH A {ch_a_v} V, CH B {ch_b_v} V"
    )
    adalm1k.set_channel_mode(AnalogChannel.CH_A, AnalogChannelMode.SVMI)
    adalm1k.set_channel_mode(AnalogChannel.CH_B, AnalogChannelMode.SVMI)
    adalm1k.flush()
    adalm1k.set_channel_constant_output(AnalogChannel.CH_A, float(ch_a_v))
    adalm1k.set_channel_constant_output(AnalogChannel.CH_B, float(ch_b_v))
    time.sleep(1)  # allow sometime for output to stabilize
    adalm1k.start_capture()
    yield adalm1k
    adalm1k.set_channel_mode(AnalogChannel.CH_A, AnalogChannelMode.HI_Z)
    adalm1k.set_channel_mode(AnalogChannel.CH_B, AnalogChannelMode.HI_Z)
    adalm1k.end_capture()


@pytest.fixture
def adalm1k_current_source(
    adalm1k: ADALM1KWrapper, pytestconfig: Config
) -> Generator[ADALM1KWrapper, None, None]:
    """Setup ADALM1K analog channels to output a specifed current [source current / measure voltage] mode"""

    ch_a_i = pytestconfig.getini("adalm1k_ch_a_current")
    ch_b_i = pytestconfig.getini("adalm1k_ch_b_current")

    if not ch_a_i or not ch_b_i:
        raise RuntimeError(
            "Undefined value(s) for adalm1k channels current source. Please provide both channels currents"
        )

    logging.info(
        f"Setting ADALM1K Channels to Source Current / Measure Voltage: CH A {ch_a_i} mA, CH B {ch_b_i} mA"
    )
    adalm1k.set_channel_mode(AnalogChannel.CH_A, AnalogChannelMode.SIMV)
    adalm1k.set_channel_mode(AnalogChannel.CH_B, AnalogChannelMode.SIMV)
    adalm1k.flush()
    adalm1k.set_channel_constant_output(AnalogChannel.CH_A, float(ch_a_i))
    adalm1k.set_channel_constant_output(AnalogChannel.CH_B, float(ch_b_i))
    time.sleep(1)  # allow sometime for output to stabilize
    adalm1k.start_capture()

    yield adalm1k

    adalm1k.set_channel_mode(AnalogChannel.CH_A, AnalogChannelMode.HI_Z)
    adalm1k.set_channel_mode(AnalogChannel.CH_B, AnalogChannelMode.HI_Z)
    adalm1k.end_capture()
