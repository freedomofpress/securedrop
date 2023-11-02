from unittest.mock import patch

from startup import validate_journalist_key

from redwood import RedwoodError


def test_validate_journalist_key(config, journalist_app, capsys):
    # The test key passes validation
    assert validate_journalist_key(journalist_app) is True
    # Reading the key file fails
    with patch(
        "encryption.EncryptionManager.get_journalist_public_key", side_effect=RuntimeError("err")
    ):
        assert validate_journalist_key(journalist_app) is False
    assert capsys.readouterr().err == "ERROR: Unable to read journalist public key: err\n"
    # Key fails validation
    with patch("redwood.is_valid_public_key", side_effect=RedwoodError("err")):
        assert validate_journalist_key(journalist_app) is False
    assert capsys.readouterr().err == "ERROR: Journalist public key is not valid: err\n"
