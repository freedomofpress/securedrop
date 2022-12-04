from pathlib import Path

from sdconfig import _parse_config_from_file


def test_parse_2014_config():
    # Given a config file from 2014
    config_module_from_2014 = "tests.config_from_2014"

    # When trying to parse it, it succeeds
    assert _parse_config_from_file(config_module_from_2014)


def test_parse_current_config():
    # Given a config file that is current; copy the example file to a proper Python module
    current_sample_config = Path(__file__).absolute().parent.parent / "config.py.example"
    current_config_module = "config_current"
    current_config_file = Path(__file__).absolute().parent / f"{current_config_module}.py"
    try:
        current_config_file.write_text(current_sample_config.read_text())

        # When trying to parse it, it succeeds
        assert _parse_config_from_file(f"tests.{current_config_module}")

    finally:
        current_config_file.unlink(missing_ok=True)
