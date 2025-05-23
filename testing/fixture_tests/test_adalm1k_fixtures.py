from pytest_analog import ADALM1KWrapper, AnalogChannel, AnalogChannelMode
from _pytest.config import Config
import pytest


def test_adalm1k_fixture(adalm1k: ADALM1KWrapper) -> None:
    assert isinstance(adalm1k, ADALM1KWrapper)
    assert str(adalm1k._device) != ""
    assert (
        adalm1k.get_channel_mode(AnalogChannel.CH_A) == AnalogChannelMode.HI_Z
    )
    assert (
        adalm1k.get_channel_mode(AnalogChannel.CH_B) == AnalogChannelMode.HI_Z
    )
    assert not adalm1k.get_capture_continuous_status()
    assert adalm1k.get_capture_sample_rate() == 100000
    assert adalm1k.get_capture_queue_size() == 100000


def test_adalm1k_voltage_source_fixture(
    adalm1k_voltage_source: ADALM1KWrapper, pytestconfig: Config
) -> None:
    assert isinstance(adalm1k_voltage_source, ADALM1KWrapper)
    assert str(adalm1k_voltage_source._device) != ""
    assert (
        adalm1k_voltage_source.get_channel_mode(AnalogChannel.CH_A)
        == AnalogChannelMode.SVMI
    )
    assert (
        adalm1k_voltage_source.get_channel_mode(AnalogChannel.CH_B)
        == AnalogChannelMode.SVMI
    )
    assert adalm1k_voltage_source.get_capture_continuous_status()
    assert adalm1k_voltage_source.get_capture_sample_rate() == 100000
    assert adalm1k_voltage_source.get_capture_queue_size() == 100000

    # timeout = -1 -> blocking read
    samples = adalm1k_voltage_source.read_all(
        adalm1k_voltage_source.get_capture_queue_size(), -1
    )
    assert len(samples) == adalm1k_voltage_source.get_capture_queue_size()

    exp_voltage_ch_a = float(pytestconfig.getini("adalm1k_ch_a_voltage"))
    exp_voltage_ch_b = float(pytestconfig.getini("adalm1k_ch_b_voltage"))

    for s in samples:
        assert (
            pytest.approx(s[0][0], abs=1.0e-2) == exp_voltage_ch_a
        )  # CH-A voltage
        assert (
            pytest.approx(s[1][0], abs=1.0e-2) == exp_voltage_ch_b
        )  # CH-B voltage


def test_adalm1k_current_source_fixture(
    adalm1k_current_source: ADALM1KWrapper, pytestconfig: Config
) -> None:
    assert isinstance(adalm1k_current_source, ADALM1KWrapper)
    assert str(adalm1k_current_source._device) != ""
    assert (
        adalm1k_current_source.get_channel_mode(AnalogChannel.CH_A)
        == AnalogChannelMode.SIMV
    )
    assert (
        adalm1k_current_source.get_channel_mode(AnalogChannel.CH_B)
        == AnalogChannelMode.SIMV
    )
    assert adalm1k_current_source.get_capture_continuous_status()
    assert adalm1k_current_source.get_capture_sample_rate() == 100000
    assert adalm1k_current_source.get_capture_queue_size() == 100000

    # timeout = -1 -> blocking read
    samples = adalm1k_current_source.read_all(
        adalm1k_current_source.get_capture_queue_size(), -1
    )
    assert len(samples) == adalm1k_current_source.get_capture_queue_size()

    exp_current_ch_a = float(pytestconfig.getini("adalm1k_ch_a_current"))
    exp_current_ch_b = float(pytestconfig.getini("adalm1k_ch_b_current"))
    for s in samples:
        assert (
            pytest.approx(s[0][1], abs=1.0e-2) == exp_current_ch_a
        )  # CH-A current
        assert (
            pytest.approx(s[1][1], abs=1.0e-2) == exp_current_ch_b
        )  # CH-B current
