# pytest-analog

Python library / Pytest plugin for experimenting /testing with HW electronics and embedded systems using the following equipments:

- [Analog Discovery](https://digilent.com/shop/analog-discovery-3/) by Digilent (USB mixed signal oscilliscope, signal generator and logic analyzer)
- [ADALM1000](https://www.analog.com/en/resources/evaluation-hardware-and-software/evaluation-boards-kits/adalm1000.html) by Analog Devices (Electronic learning module with source measure unit functionality)

## Required Installations

You need to install the following dependencies on your system so pytest-analog can communicate with the attached test equipment

| Component           | Tested Version           | Description                                                              
|---------------------|---------------|----------------------------------------------|
|  [WaveForms / WaveForms SDK](https://cloud.digilent.com/myproducts/waveform?pc=1&tab=2)  |  3.23.4 | Software / SDK for Analog Discovery functions
|  [Adept](https://cloud.digilent.com/myproducts/Adept?pc=1&tab=2)  |  2.27.9 | Runtimne library for communication with Analog Discovery
|  [libsmu](https://github.com/analogdevicesinc/libsmu/releases)  |  1.0.4 | library for USB communication with ADALM M1000 
|  [pysmu](https://github.com/analogdevicesinc/libsmu/releases)  |  1.0.4 | Python bindings package for libsmu


## Installation Instructions
- From the above dependencies install **WaveForms, Adept and libsmu** on your system
- Create a Python virtual environment using your Python3.x interpreter:

  ```bash
  python3 -m venv venv # on Unix based OS
  ```
  ```powershell
  python -m venv venv # on Windows
  ```
- Activate the Python virtual environment

  ```bash
  . venv/bin/activate # on Unix based OS
  ```
  ```powershell
  . venv/Scripts/activate # on Windows
  ```

- Install pysmu either from github source page or published wheel packages on [test.pypi](https://test.pypi.org/project/pysmu/#description)

  **Note:** for libsmu /pysmu there are no ready to install wheel packages / bindings for ARM platform, therefore you need to build them from source using the instructions on their [github page](https://github.com/analogdevicesinc/libsmu)


- Install pytest_analog from test.pypi repository (**Currently the library is in testing and published only under test.pypi**)

  ```bash
  python3 -m pip install --extra-index-url https://test.pypi.org/simple/ pytest-analog # on Unix based OS
  ```
  ```powershell
  python -m pip install --extra-index-url https://test.pypi.org/simple/ pytest-analog # on Windows
  ```

## Usage
You can use pytest-analog to setup automated testing for your projects using the pytest framework. Alternatively you can use it as a supporting library for your custom python project(s) by utilizing the implmented wrappers

### Pytest fixtures for automated testing
- You can list available fixtures from pytest_analog by running the command and looking at the section: ***fixtures defined from pytest_analog.fixtures*** :

  ```bash
  pytest --fixtures 
  ```

- A number of fixtures are implemented to help setup predefined workflow(s) for the instrument at the begining / end of the test (e.g. setup ADALM1K to source a predefined voltage / current to your DUT, do a measurement based on your test context and then do a teardown / reset of the instrument at the end of the test)

- You can combine fixtures from different instruments (e.g. Analog Discovery + ADALM1K) to create more advanced testing scenarios 

  The example below illustrates a simple test where analog discovery scope channels are used to measure the voltage output set by ADALM1K source channels:

  ```python
  ###########################################
  # pytest.ini -> here provide fixtures configuration

  # ADALM1000 Fixtures Options
  # Voltage Source
  adalm1k_ch_a_voltage = 3.70
  adalm1k_ch_b_voltage = 1.0

  # Analog Discovery Fixtures Options
  analog_discovery_config_number = 1

  ###########################################
  # test_analog_discovery_adalm1k_combined.py -> here write your test case
  def test_analog_discovery_adalm1k_combined(adalm1k_voltage_source: ADALM1KWrapper,
                              analog_discovery_scope_wavegen: AnalogDiscoveryWrapper,
                              pytestconfig: Config) -> None:

      ###
      # IMPORTANT: for this test the following connections are required between ADALM1K and Analog Discovery
      ## (ADALM1k) CH-A -> (Anlaog Discovery) +1
      ## (ADALM1k) CH-B -> (Anlaog Discovery) +2
      ## (ADALM1k) GND -> (Anlaog Discovery) -1
      ## (ADALM1k) GND -> (Anlaog Discovery) -2
      ###

      # read 100 samples from adalm1k instrument in blocking fashion
      adalm1k_samples = adalm1k_voltage_source.read_all(100, -1)

      # get configured values in pytest.ini
      exp_voltage_ch_a = float(pytestconfig.getini("adalm1k_ch_a_voltage"))
      exp_voltage_ch_b = float(pytestconfig.getini("adalm1k_ch_b_voltage"))

      # assert measured voltages are close to expected ones configured by the fixture
      for s in adalm1k_samples:
          assert pytest.approx(s[0][0], abs=1.0e-2) == exp_voltage_ch_a # CH-A voltage 
          assert pytest.approx(s[1][0], abs=1.0e-2) == exp_voltage_ch_b  # CH-B voltage

      # use analog discovery analog in channels (1, 2) to measure output voltages from ADALM1K channels (A, B)
      analog_discovery_scope_wavegen.record_analog_signal(
          input_channels = [AnalogInputChannel.Channel1, AnalogInputChannel.Channel2],
          range= 10,                                   
          sampling_frequency= 100e3)
      
      # read 100 samples from analog disocvery in blocking fashion
      ad_samples = analog_discovery_scope_wavegen.fill_recorded_samples_on_channels(
          [AnalogInputChannel.Channel1, AnalogInputChannel.Channel2],
          100)
      
      # assert measured voltages by analog discovery are close to the ones set by adalm1k
      for ch1_s, ch2_s in zip(ad_samples[0],  ad_samples[1]):
          assert pytest.approx(ch1_s, abs=5.0e-2) == exp_voltage_ch_a # CH-A voltage 
          assert pytest.approx(ch2_s, abs=5.0e-2) == exp_voltage_ch_b # CH-B voltage
  ```

### Context managers to control hardware setup / taerdown
- context managers can be used to safely configure and allocate resources of the test equipment in Python
This makes it easy to perform multiple workflows without having to call many setup functions to configure the instrument. In addtion the instrument is reset to its initial configuration when the context manager is no longer in scope

- The following examples demonsrate the use of implemeneted context managers for ADALM1K and Analog Discovery wrappers:

  ```python
    # ADALM1k context manager to start continous source / capture with predefined config for channels A,B
    from pytest_analog import SMUContext, AnalogChannelMode

    with SMUContext(ch_a_mode= AnalogChannelMode.SIMV,
                    ch_b_mode= AnalogChannelMode.HI_Z,
                    ch_a_dc_output= 0.0,
                    ch_b_dc_output= 0.0) as smu:
        
        # perform your wished workflow inside this block
        # for example: non-blocking read of 1000 captured measurements
        samples = smu.read_all(1000) 
  ```

  ```python
    # Analog Discovery context manager to control wavegen / scope instruments
    from pytest_analog import AnalogDiscoveryScopeWaveGenContext, AnalogOutputSignal, AnalogInputChannel, AnalogOutputChannel

    # Analog Play Settings
    PLAY_FREQUENCY  = 50 # Hz (50 Hz)
    PLAY_AMPLITUDE = 1.41 # volts
    PLAY_OFFSET = 1.41 # volts
    PLAY_SIGNAL = AnalogOutputSignal.Sine # generated function
    ANALOG_IN_CHANNEL = AnalogInputChannel.Channel2
    ANALOG_OUT_CHANNEL = AnalogOutputChannel.WaveGen1

    # Analog Recording Settings
    SAMPLE_FREQUENCY = 50000 # Hz (50 kHz)
    SAMPLES_COUNT = 32000 # number of samples to capture (32k)

    with AnalogDiscoveryScopeWaveGenContext([ANALOG_OUT_CHANNEL, ANALOG_IN_CHANNEL]) as player_recorder:
        ##### start Continuous play of sine wave #####
        player_recorder.play_analog_signal(output_channels=[ANALOG_OUT_CHANNEL],
        type = PLAY_SIGNAL,
        amplitude = PLAY_AMPLITUDE,
        frequency = PLAY_FREQUENCY,
        offset= PLAY_OFFSET)

        ##### start a Continuous recording on ANALOG_IN_CHANNEL #####
        player_recorder.record_analog_signal(input_channels = [ANALOG_IN_CHANNEL],                                     
        range= 2 * PLAY_AMPLITUDE,
        offset= PLAY_OFFSET,
        sampling_frequency= SAMPLE_FREQUENCY)
    
        # collect recordded data acquired by the scope
        samples = player_recorder.fill_recorded_samples(ANALOG_IN_CHANNEL, SAMPLES_COUNT)
  ```

### Multiprocessing workers
To support running workflows in parallel to the main process, example multiprocessing workers are implemented. Python built in multiporcessing
module is used to create process clasess. Examples are available as part of the plugin tests [here](./testing/test_pytest_analog_plugin.py)

# Contribute
Contributions to pytest-analog are welcome to extend the functions list / add wrappers for additonal test equipment

Please reach out to me via E-mail: ammar.khallouf@tum.de to discuss your ideas