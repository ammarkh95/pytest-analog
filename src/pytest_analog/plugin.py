"""Hook specifications for pytest plugins which are invoked by pytest itself and by builtin plugins"""

from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser):
    # Analog Discovery Options
    ############################
    parser.addini(
        "analog_discovery_config_number",
        type="string",
        default="0",
        help="desired configuration image number to use for the analog discovery (see WaveForms reference manual)",
    )

    parser.addini(
        "analog_discovery_supplies_positive_voltage",
        type="string",
        default=None,
        help="desired positive suuply voltage (V+) for the analog discovery 2,3 range: [0, 5] V",
    )

    parser.addini(
        "analog_discovery_supplies_negative_voltage",
        type="string",
        default=None,
        help="desired negative suuply voltage (V-) for the analog discovery 2,3 range: [-5, 0] V",
    )

    # ADALM1K Options
    ############################
    parser.addini(
        "adalm1k_ch_a_voltage",
        type="string",
        default=None,
        help="desired DC voltage for channel A of ADALM1K: [0, 5] V",
    )

    parser.addini(
        "adalm1k_ch_b_voltage",
        type="string",
        default=None,
        help="desired DC voltage for channel B of ADALM1K: [0, 5] V",
    )

    parser.addini(
        "adalm1k_ch_a_current",
        type="string",
        default=None,
        help="desired DC current for channel A of ADALM1K: [-200, 200] mA",
    )

    parser.addini(
        "adalm1k_ch_b_current",
        type="string",
        default=None,
        help="desired DC current for channel B of ADALM1K: [-200, 200] mA",
    )
