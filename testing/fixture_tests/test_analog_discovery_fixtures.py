from pytest_analog import (
    AnalogDiscoveryWrapper,
    AnalogInputChannel,
    AnalogOutputChannel,
)
from _pytest.config import Config


def test_analog_discovery_fixture(
    analog_discovery: AnalogDiscoveryWrapper,
) -> None:
    assert isinstance(analog_discovery, AnalogDiscoveryWrapper)
    assert analog_discovery._get_auto_configure() == 1
    assert analog_discovery.get_last_error() == 0
    assert analog_discovery.get_adc_bits_info() == 14
    assert analog_discovery.get_devices_info()


def test_analog_discovery_supplies_fixture(
    analog_discovery_supplies: AnalogDiscoveryWrapper, pytestconfig: Config
) -> None:
    assert analog_discovery_supplies.get_power_supply_status()
    v_plus, v_minus = analog_discovery_supplies.get_power_supply_voltages()
    assert (
        float(
            pytestconfig.getini("analog_discovery_supplies_positive_voltage")
        )
        == v_plus
    )
    assert (
        float(
            pytestconfig.getini("analog_discovery_supplies_negative_voltage")
        )
        == v_minus
    )
    analog_discovery_supplies.disable_power_supply()
    assert not analog_discovery_supplies.get_power_supply_status()


def test_analog_discovery_scope_wavegen_fixture(
    analog_discovery_scope_wavegen: AnalogDiscoveryWrapper,
) -> None:
    assert (
        analog_discovery_scope_wavegen.get_analog_channel_enable_state(
            AnalogOutputChannel.WaveGen1
        )
        == 1
    )
    assert (
        analog_discovery_scope_wavegen.get_analog_channel_enable_state(
            AnalogOutputChannel.WaveGen2
        )
        == 1
    )
    assert (
        analog_discovery_scope_wavegen.get_analog_channel_enable_state(
            AnalogInputChannel.Channel1
        )
        == 1
    )
    assert (
        analog_discovery_scope_wavegen.get_analog_channel_enable_state(
            AnalogInputChannel.Channel2
        )
        == 1
    )
