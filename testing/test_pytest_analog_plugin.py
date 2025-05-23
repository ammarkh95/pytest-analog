import pytest
import pathlib
from pytest_analog import (
    SMUContext,
    AnalogChannelMode,
    ADALM1KWrapper,
    AnalogChannel,
    SMUWorker,
    AnalogDiscoveryScopeWaveGenContext,
    AnalogDiscoveryPowerSupplyContext,
    AnalogDiscoveryI2CContext,
    DigitalIOChannel,
    AnalogDiscoverySPIContext,
    AnalogOutputSignal,
    AnalogAcquisitionMode,
    AnalogInputChannel,
    AnalogOutputChannel,
    AnalogInstrumentState,
    AnalogDiscoveryScopeWorker,
)
import time
import multiprocessing as mp
import logging
import random
import math


@pytest.fixture
def read_pytest_ini(request):
    return pathlib.Path(request.config.rootdir, "pytest.ini").read_text()


@pytest.mark.pytester_example_path("fixture_tests")
def test_adalm1k_fixtures(testdir, read_pytest_ini) -> None:
    testdir.makeini(read_pytest_ini)
    testdir.copy_example()
    logging.info("Running ADALM1K Fixtures Tests")
    result = testdir.runpytest()
    assert result.ret == 0
    result.stdout.fnmatch_lines_random(["*passed*"])
    result.assert_outcomes(passed=3)


def test_adalm1k_context_manager() -> None:
    logging.info(
        "::::::Running ADALM1K Context Manager DisContinuous Capture::::::"
    )
    # Discontinuous Capture
    with SMUContext(
        ch_a_mode=AnalogChannelMode.HI_Z,
        ch_b_mode=AnalogChannelMode.SVMI,
        ch_a_dc_output=0.0,
        ch_b_dc_output=1.0,
        n_samples=1000,
    ) as smu:
        assert isinstance(smu, ADALM1KWrapper)
        assert (
            smu.get_channel_mode(AnalogChannel.CH_A) == AnalogChannelMode.HI_Z
        )
        assert (
            smu.get_channel_mode(AnalogChannel.CH_B) == AnalogChannelMode.SVMI
        )
        samples = smu.read_all(1000, timeout=-1)  # blocking read

        for s in samples:
            assert pytest.approx(s[0][0], abs=5.0e-1) == 0.0  # CH-A voltage
            assert pytest.approx(s[1][0], abs=1.0e-2) == 1.0  # CH-B voltage

        assert not smu.get_capture_continuous_status()  # finished the capture
        assert not smu.get_capture_cancel_status()  # capture not canceled
        samples = smu.read_all(1000)  # further read returns no further data
        assert samples == []

    logging.info(
        "::::::Running ADALM1K Context Manager Continuous Capture::::::"
    )
    # Continuous Capture
    with SMUContext(
        ch_a_mode=AnalogChannelMode.SIMV,
        ch_b_mode=AnalogChannelMode.HI_Z,
        ch_a_dc_output=0.0,
        ch_b_dc_output=0.0,
    ) as smu:
        assert isinstance(smu, ADALM1KWrapper)
        assert (
            smu.get_channel_mode(AnalogChannel.CH_A) == AnalogChannelMode.SIMV
        )
        assert (
            smu.get_channel_mode(AnalogChannel.CH_B) == AnalogChannelMode.HI_Z
        )
        time.sleep(0.5)
        samples = smu.read_all(1000)  # non-blocking read
        assert len(samples) != 0
        assert smu.get_capture_continuous_status()  # capture ongoing
        assert not smu.get_capture_cancel_status()  # capture not canceled
        samples = smu.read_all(1000, timeout=-1)  # blocking read
        assert len(samples) == 1000

        for s in samples:
            assert pytest.approx(s[0][1], abs=1.0e-2) == 0.0  # CH-A current
            assert pytest.approx(s[1][1], abs=1.0e-2) == 0.0  # CH-B current


def test_adalm1k_multiprocess_worker() -> None:
    # create queues to send request and recieve results from adalm1k worker child process
    request_queue = mp.Queue()
    response_queue = mp.Queue()

    # place request jon on the queue -> see "SMUWorker" to understand the request arguments
    request_queue.put(
        (AnalogChannelMode.SVMI, AnalogChannelMode.SVMI, 1.0, 2.0, 10000)
    )
    # start process and halt main process short to allow worker to pick queue
    logging.info(
        "Starting ADALM1K Worker In Seperate Process and Make a Request"
    )
    smu_worker = SMUWorker(request_queue, response_queue)
    smu_worker.start()

    logging.info("Doing Other Tasks Meanwhile on Main Process ...")
    time.sleep(random.randint(2, 5))

    logging.info("Wait on ADALM1K Worker Process Response ....")
    samples = response_queue.get()
    assert len(samples) == 10000
    for s in samples:
        assert pytest.approx(s[0][0], abs=1.0e-2) == 1.0  # CH-A voltage
        assert pytest.approx(s[1][0], abs=1.0e-2) == 2.0  # CH-B voltage

    logging.info("Placing a New Request For ADALM1K Worker")
    request_queue.put(
        (AnalogChannelMode.HI_Z, AnalogChannelMode.HI_Z, 0.0, 0.0, 100)
    )

    logging.info("Doing Other Tasks Meanwhile on Main Process ...")
    time.sleep(random.randint(2, 5))

    logging.info("Wait on ADALM1K Worker Process Response ....")
    samples = response_queue.get()
    assert len(samples) == 100
    for s in samples:
        assert pytest.approx(s[0][0], abs=5.0e-1) == 0.0  # CH-A voltage
        assert pytest.approx(s[1][0], abs=5.0e-1) == 0.0  # CH-B voltage

    # stop and join SMU Worker process
    request_queue.put("STOP")
    smu_worker.join()

    request_queue_state = request_queue.empty()
    logging.info(f"Checking Request Queue is cleared ? {request_queue_state}")
    assert request_queue_state


@pytest.mark.pytester_example_path("fixture_tests")
def test_analog_discovery_fixtures(testdir, read_pytest_ini) -> None:
    testdir.makeini(read_pytest_ini)
    testdir.copy_example()
    logging.info("Running Analog Discovery Fixtures Tests")
    result = testdir.runpytest()
    assert result.ret == 0
    result.stdout.fnmatch_lines_random(["*passed*"])
    result.assert_outcomes(passed=3)


def test_analog_discovery_context_managers() -> None:
    # Analog Play Settings
    PLAY_FREQUENCY = 50  # Hz (50 Hz)
    PLAY_AMPLITUDE = 1.41  # volts
    PLAY_OFFSET = 1.41  # volts
    PLAY_SIGNAL = AnalogOutputSignal.Sine  # generated function
    ANALOG_IN_CHANNEL = AnalogInputChannel.Channel2
    ANALOG_OUT_CHANNEL = AnalogOutputChannel.WaveGen1

    # Analog Recording Settings
    SAMPLE_FREQUENCY = 50000  # Hz (50 kHz)
    SAMPLES_COUNT = 32000  # number of samples to capture (32k)

    logging.info(
        "::::::Running Analog Discovery Scope/Wavegen Context Manager::::::"
    )
    with AnalogDiscoveryScopeWaveGenContext(
        [ANALOG_OUT_CHANNEL, ANALOG_IN_CHANNEL]
    ) as player_recorder:
        ##### start Continuous play of sine wave on ANALOG_OUT_CHANNEL #####
        logging.info(f"Starting play on: {ANALOG_OUT_CHANNEL.name}")
        player_recorder.play_analog_signal(
            output_channels=[ANALOG_OUT_CHANNEL],
            type=PLAY_SIGNAL,
            amplitude=PLAY_AMPLITUDE,
            frequency=PLAY_FREQUENCY,
            offset=PLAY_OFFSET,
        )

        # assert wavegen instrument started playing on channel 1 only
        status_val, _ = player_recorder.get_play_status(ANALOG_OUT_CHANNEL)
        assert status_val == AnalogInstrumentState.Running.value
        status_val, _ = player_recorder.get_play_status(
            AnalogOutputChannel.WaveGen2
        )
        assert status_val == AnalogInstrumentState.Ready.value
        assert (
            player_recorder._get_analog_output_generator_function(
                ANALOG_OUT_CHANNEL.value
            ).value
            == AnalogOutputSignal.Sine.value
        )

        ##### start a Continuous recording on ANALOG_IN_CHANNEL #####
        logging.info(f"Starting record on {ANALOG_IN_CHANNEL.name}")
        player_recorder.record_analog_signal(
            input_channels=[ANALOG_IN_CHANNEL],
            range=2 * PLAY_AMPLITUDE,
            offset=PLAY_OFFSET,
            sampling_frequency=SAMPLE_FREQUENCY,
        )

        # collect recordded data acquired by the scope
        samples = player_recorder.fill_recorded_samples(
            ANALOG_IN_CHANNEL, SAMPLES_COUNT
        )
        assert len(samples) == SAMPLES_COUNT
        status_val, _ = player_recorder.get_record_status()
        assert status_val == AnalogInstrumentState.Running.value
        assert (
            player_recorder._get_analog_input_acquisition_mode().value
            == AnalogAcquisitionMode.Record.value
        )

    # start power supply context with given v+ / (optional) v- voltages on Analog IO channels
    logging.info(
        "::::::Running Analog Discovery Supplies Context Manager::::::"
    )
    with AnalogDiscoveryPowerSupplyContext(1.0, -1.0) as power_supply:
        # assert the status of power supply when switched on / off
        assert not power_supply.get_power_supply_status()
        power_supply.enable_power_supply()
        assert power_supply.get_power_supply_status()
        power_supply.disable_power_supply()
        assert not power_supply.get_power_supply_status()

        # assert the positive / neagitve supply voltages values set internally
        v_plus, v_minus = power_supply.get_power_supply_voltages()
        assert math.isclose(v_plus, 1.0)
        assert math.isclose(v_minus, -1.0)

        # change the positive / negative supply voltages and assert new values are set internally
        power_supply.set_power_supply_voltages(2.0, -0.5)
        v_plus, v_minus = power_supply.get_power_supply_voltages()
        assert math.isclose(v_plus, 2.0)
        assert math.isclose(v_minus, -0.5)

    logging.info(
        "::::::Running Analog Discovery I2C Protocol Context Manager::::::"
    )
    try:
        with AnalogDiscoveryI2CContext(
            DigitalIOChannel.DIO_5, DigitalIOChannel.DIO_0
        ) as i2c_controller:
            i2c_controller.start_i2c_spy()
            time.sleep(3)
            i2c_data = i2c_controller.read_i2c_spy_data(16)
            logging.info(f"Collected i2c messages: {i2c_data}")
    # no i2c devices / pull ups connected
    except RuntimeError as e:
        assert "I2C bus error" in str(e)

    logging.info(
        "::::::Running Analog Discovery SPI Protocol Context Manager::::::"
    )
    CS_PIN = DigitalIOChannel.DIO_0
    with AnalogDiscoverySPIContext(
        DigitalIOChannel.DIO_1,
        CS_PIN,
        1e3,
        DigitalIOChannel.DIO_2,
        DigitalIOChannel.DIO_3,
    ) as spi_controller:
        spi_controller.spi_8_bits_write("\x1b[j", CS_PIN)


def test_analog_discovery_multiprocess_worker() -> None:
    request_queue = mp.Queue()
    response_queue = mp.Queue()

    scope_range = 1  # V
    sampling_frequency = 16000  # Hz
    scan_duration = 5  # sec
    samples_count = 16000

    request_queue.put(
        (
            "RECORD",
            [AnalogInputChannel.Channel1, AnalogInputChannel.Channel2],
            samples_count,
            sampling_frequency,
            scope_range,
            None,
        )
    )
    logging.info(
        "Starting Analog Discovery Worker In Seperate Process and Make a Request"
    )
    ad_worker = AnalogDiscoveryScopeWorker(request_queue, response_queue)
    ad_worker.start()

    logging.info("Doing Other Tasks Meanwhile on Main Process ...")
    time.sleep(random.randint(2, 5))

    logging.info("Wait on Analog Discovery Worker Process Response ....")
    samples = response_queue.get()
    assert len(samples) == 2  # tuple for 2 channels
    assert len(samples[0]) == samples_count
    assert len(samples[1]) == samples_count

    logging.info("Placing a New Request For Analog Discovery Worker")
    request_queue.put(
        (
            "SCAN",
            [AnalogInputChannel.Channel1, AnalogInputChannel.Channel2],
            samples_count,
            sampling_frequency,
            scope_range,
            scan_duration,
        )
    )

    logging.info("Doing Other Tasks Meanwhile on Main Process ...")
    time.sleep(random.randint(2, 5))

    logging.info("Wait on Analog Discovery Worker Process Response ....")
    samples = response_queue.get()
    assert len(samples) == 2  # tuple for 2 channels
    assert len(samples[0]) == samples_count
    assert len(samples[1]) == samples_count

    # stop and join SMU Worker process
    request_queue.put("STOP")
    ad_worker.join()

    request_queue_state = request_queue.empty()
    logging.info(f"Checking Request Queue is cleared ? {request_queue_state}")
    assert request_queue_state
