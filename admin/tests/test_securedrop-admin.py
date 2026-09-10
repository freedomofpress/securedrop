#
# SecureDrop whistleblower submission system
# Copyright (C) 2017- Freedom of the Press Foundation and SecureDrop
# contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import argparse
import json
import os
import shutil
import subprocess
import textwrap
from os.path import basename, dirname, exists, join
from pathlib import Path
from unittest import mock

import pytest
import securedrop_admin
import yaml
from flaky import flaky
from prompt_toolkit.validation import ValidationError

CONFIG_DIR = f"{str(Path.home())}/.config/securedrop-admin"
SITE_CONFIG_PATH = join(CONFIG_DIR, "site-specific")


class Document:
    def __init__(self, text):
        self.text = text


@flaky
class TestSecureDropAdmin:
    def test_verbose(self, capsys):
        securedrop_admin.setup_logger(verbose=True)
        securedrop_admin.sdlog.debug("VISIBLE")
        out, err = capsys.readouterr()
        assert "VISIBLE" in out

    def test_not_verbose(self, capsys):
        securedrop_admin.setup_logger(verbose=False)
        securedrop_admin.sdlog.debug("HIDDEN")
        securedrop_admin.sdlog.info("VISIBLE")
        out, err = capsys.readouterr()
        assert "HIDDEN" not in out
        assert "VISIBLE" in out

    def test_openssh_detection(self):
        with mock.patch("securedrop_admin.openssh_version", side_effect=[9]):
            assert securedrop_admin.ansible_command() == [
                "/usr/share/securedrop-admin/venv/bin/ansible-playbook",
                "--scp-extra-args='-O'",
            ]
        with mock.patch("securedrop_admin.openssh_version", side_effect=[8]):
            assert securedrop_admin.ansible_command() == [
                "/usr/share/securedrop-admin/venv/bin/ansible-playbook"
            ]

    def test_check_for_updates_success(self, caplog):
        """
        When check_for_updates is called
          And the Ansible playbook succeeds
        Then it should log "All updates applied"
          And return 0
        """
        args = argparse.Namespace()

        with mock.patch("securedrop_admin.ansible_command", return_value=["ansible-playbook"]):
            with mock.patch("subprocess.check_call") as mocked_check_call:
                update_status = securedrop_admin.check_for_updates(args)
                assert mocked_check_call.called
                assert "All updates applied" in caplog.text
                assert update_status == 0

    def test_check_for_updates_failure(self, caplog):
        """
        When check_for_updates is called
          And the Ansible playbook fails
        Then it should log "Update check failed"
          And return 1
        """
        args = argparse.Namespace()

        with mock.patch("securedrop_admin.ansible_command", return_value=["ansible-playbook"]):
            with mock.patch(
                "subprocess.check_call",
                side_effect=subprocess.CalledProcessError(1, "ansible-playbook"),
            ):
                update_status = securedrop_admin.check_for_updates(args)
                assert "Update check failed" in caplog.text
                assert update_status == 1

    def test_exit_codes(self):
        """Ensure that securedrop-admin returns the correct
        exit codes for success or failure."""
        with mock.patch("securedrop_admin.install_securedrop", return_value=0):
            with pytest.raises(SystemExit) as e:
                securedrop_admin.main(["install"])
            assert e.value.code == securedrop_admin.EXIT_SUCCESS

        with mock.patch(
            "securedrop_admin.install_securedrop",
            side_effect=subprocess.CalledProcessError(1, "TestError"),
        ):
            with pytest.raises(SystemExit) as e:
                securedrop_admin.main(["install"])
            assert e.value.code == securedrop_admin.EXIT_SUBPROCESS_ERROR

        with mock.patch("securedrop_admin.install_securedrop", side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as e:
                securedrop_admin.main(["install"])
            assert e.value.code == securedrop_admin.EXIT_INTERRUPT


class TestSiteConfig:
    def setup_method(self, method):
        # Make sure config dir exists and is empty
        shutil.rmtree(CONFIG_DIR, ignore_errors=True)
        os.makedirs(CONFIG_DIR, exist_ok=True)

    def teardown_method(self, method):
        # Delete config dir when we're done
        shutil.rmtree(CONFIG_DIR, ignore_errors=True)

    def test_exists(self):
        assert not securedrop_admin.SiteConfig().exists()

        with open(SITE_CONFIG_PATH, "w") as f:
            f.write("fake-config")

        assert securedrop_admin.SiteConfig().exists()

    def test_validate_not_empty(self):
        validator = securedrop_admin.SiteConfig.ValidateNotEmpty()

        assert validator.validate(Document("something"))
        with pytest.raises(ValidationError):
            validator.validate(Document(""))

    def test_validate_time(self):
        validator = securedrop_admin.SiteConfig.ValidateTime()

        assert validator.validate(Document("4"))
        with pytest.raises(ValidationError):
            validator.validate(Document(""))
        with pytest.raises(ValidationError):
            validator.validate(Document("four"))
        with pytest.raises(ValidationError):
            validator.validate(Document("4.30"))
        with pytest.raises(ValidationError):
            validator.validate(Document("25"))
        with pytest.raises(ValidationError):
            validator.validate(Document("-4"))

    def test_validate_ossec_username(self):
        validator = securedrop_admin.SiteConfig.ValidateOSSECUsername()

        assert validator.validate(Document("username"))
        with pytest.raises(ValidationError):
            validator.validate(Document("bad@user"))
        with pytest.raises(ValidationError):
            validator.validate(Document("test"))

    def test_validate_ossec_password(self):
        validator = securedrop_admin.SiteConfig.ValidateOSSECPassword()

        assert validator.validate(Document("goodpassword"))
        with pytest.raises(ValidationError):
            validator.validate(Document("password123"))
        with pytest.raises(ValidationError):
            validator.validate(Document(""))
        with pytest.raises(ValidationError):
            validator.validate(Document("short"))

    def test_validate_email(self):
        validator = securedrop_admin.SiteConfig.ValidateEmail()

        assert validator.validate(Document("good@mail.com"))
        with pytest.raises(ValidationError):
            validator.validate(Document("badmail"))
        with pytest.raises(ValidationError):
            validator.validate(Document(""))

    def test_validate_ossec_email(self):
        validator = securedrop_admin.SiteConfig.ValidateOSSECEmail()

        assert validator.validate(Document("good@mail.com"))
        with pytest.raises(ValidationError) as e:
            validator.validate(Document("ossec@ossec.test"))
        assert "something other than ossec@ossec.test" in str(e)

    def test_validate_optional_email(self):
        validator = securedrop_admin.SiteConfig.ValidateOptionalEmail()

        assert validator.validate(Document("good@mail.com"))
        assert validator.validate(Document(""))

    def test_validate_user(self):
        validator = securedrop_admin.SiteConfig.ValidateUser()
        with pytest.raises(ValidationError):
            validator.validate(Document("amnesia"))
        with pytest.raises(ValidationError):
            validator.validate(Document("root"))
        with pytest.raises(ValidationError):
            validator.validate(Document(""))
        assert validator.validate(Document("gooduser"))

    def test_validate_ip(self):
        validator = securedrop_admin.SiteConfig.ValidateIP()
        with pytest.raises(ValidationError):
            validator.validate(Document("599.20"))
        assert validator.validate(Document("192.168.1.1"))

    def test_validate_path(self):
        mydir = dirname(__file__)
        myfile = basename(__file__)
        validator = securedrop_admin.SiteConfig.ValidatePath(mydir)
        assert validator.validate(Document(myfile))
        with pytest.raises(ValidationError):
            validator.validate(Document("NONEXIST"))
        with pytest.raises(ValidationError):
            validator.validate(Document(""))

    def test_validate_optional_path(self):
        mydir = dirname(__file__)
        myfile = basename(__file__)
        validator = securedrop_admin.SiteConfig.ValidateOptionalPath(mydir)
        assert validator.validate(Document(myfile))
        assert validator.validate(Document(""))

    def test_validate_yes_no(self):
        validator = securedrop_admin.SiteConfig.ValidateYesNo()
        with pytest.raises(ValidationError):
            validator.validate(Document("something"))
        assert validator.validate(Document("yes"))
        assert validator.validate(Document("YES"))
        assert validator.validate(Document("no"))
        assert validator.validate(Document("NO"))

    def test_validate_fingerprint(self):
        validator = securedrop_admin.SiteConfig.ValidateFingerprint()
        assert validator.validate(Document("012345678901234567890123456789ABCDEFABCD"))
        assert validator.validate(Document("01234 5678901234567890123456789ABCDE   FABCD"))

        with pytest.raises(ValidationError) as e:
            validator.validate(Document("65A1B5FF195B56353CC63DFFCC40EF1228271441"))
        assert "TEST journalist" in str(e)

        with pytest.raises(ValidationError) as e:
            validator.validate(Document("600BC6D5142C68F35DDBCEA87B597104EDDDC102"))
        assert "TEST admin" in str(e)

        with pytest.raises(ValidationError) as e:
            validator.validate(Document("0000"))
        assert "40 hexadecimal" in str(e)

        with pytest.raises(ValidationError) as e:
            validator.validate(Document("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"))
        assert "40 hexadecimal" in str(e)

    def test_validate_optional_fingerprint(self):
        validator = securedrop_admin.SiteConfig.ValidateOptionalFingerprint()
        assert validator.validate(Document("012345678901234567890123456789ABCDEFABCD"))
        assert validator.validate(Document(""))

    def test_sanitize_fingerprint(self):
        site_config = securedrop_admin.SiteConfig()
        assert site_config.sanitize_fingerprint("    A bc\n") == "ABC"

    def test_validate_int(self):
        validator = securedrop_admin.SiteConfig.ValidateInt()
        with pytest.raises(ValidationError):
            validator.validate(Document("123X"))
        assert validator.validate(Document("192"))

    def test_locales(self):
        locales = securedrop_admin.SiteConfig.Locales()
        translations = locales.get_translations()
        assert "en_US" in translations
        assert "fr_FR" in translations

    def test_validate_locales(self):
        validator = securedrop_admin.SiteConfig.ValidateLocales({"en_US", "fr_FR"})
        assert validator.validate(Document("en_US  fr_FR "))
        with pytest.raises(ValidationError) as e:
            validator.validate(Document("BAD"))
        assert "BAD" in str(e)

    def test_save(self):
        site_config = securedrop_admin.SiteConfig()
        site_config.config = {"var1": "val1", "var2": "val2"}
        site_config.save()
        expected = textwrap.dedent(
            """\
        var1: val1
        var2: val2
        """
        )
        assert expected == open(SITE_CONFIG_PATH).read()

    def test_validate_gpg_key(self):
        for file in ["test_journalist_key.pub", "weak_test_key_should_fail_sqlinter.asc"]:
            shutil.copy(join("tests", "files", file), CONFIG_DIR)
        good_config = {
            "securedrop_app_gpg_public_key": "test_journalist_key.pub",
            "securedrop_app_gpg_fingerprint": "65A1B5FF195B56353CC63DFFCC40EF1228271441",
            "ossec_alert_gpg_public_key": "test_journalist_key.pub",
            "ossec_gpg_fpr": "65A1B5FF195B56353CC63DFFCC40EF1228271441",
            "journalist_alert_gpg_public_key": "test_journalist_key.pub",
            "journalist_gpg_fpr": "65A1B5FF195B56353CC63DFFCC40EF1228271441",
        }
        site_config = securedrop_admin.SiteConfig()
        site_config.config = good_config
        assert site_config.validate_gpg_keys()

        for key in ("securedrop_app_gpg_fingerprint", "ossec_gpg_fpr", "journalist_gpg_fpr"):
            bad_config = good_config.copy()
            bad_config[key] = "FAIL"
            site_config.config = bad_config
            with pytest.raises(securedrop_admin.FingerprintException) as e:
                site_config.validate_gpg_keys()
            assert "FAIL does not match" in str(e)

        # Test a key with matching fingerprint but that fails sq-keyring-linter
        invalid_config = {
            # Correct key fingerprint but weak 1024-bit RSA key with SHA-1 self signature
            "securedrop_app_gpg_public_key": "weak_test_key_should_fail_sqlinter.asc",
            "securedrop_app_gpg_fingerprint": "40F1C17B7E7826DAB40B14AE7786B000E6D0A76E",
            "ossec_alert_gpg_public_key": "test_journalist_key.pub",
            "ossec_gpg_fpr": "65A1B5FF195B56353CC63DFFCC40EF1228271441",
            "journalist_alert_gpg_public_key": "test_journalist_key.pub",
            "journalist_gpg_fpr": "65A1B5FF195B56353CC63DFFCC40EF1228271441",
        }
        site_config.config = invalid_config
        with pytest.raises(securedrop_admin.FingerprintException) as e:
            site_config.validate_gpg_keys()
        assert "failed sq key validation check" in str(e)

    def test_journalist_alert_email(self):
        shutil.copy(join("tests", "files", "test_journalist_key.pub"), CONFIG_DIR)
        site_config = securedrop_admin.SiteConfig()
        site_config.config = {
            "journalist_alert_gpg_public_key": "",
            "journalist_gpg_fpr": "",
        }
        assert site_config.validate_journalist_alert_email()
        site_config.config = {
            "journalist_alert_gpg_public_key": "test_journalist_key.pub",
            "journalist_gpg_fpr": "65A1B5FF195B56353CC63DFFCC40EF1228271441",
        }
        site_config.config["journalist_alert_email"] = ""
        with pytest.raises(securedrop_admin.JournalistAlertEmailException) as e:
            site_config.validate_journalist_alert_email()
        assert "not be empty" in str(e)

        site_config.config["journalist_alert_email"] = "bademail"
        with pytest.raises(securedrop_admin.JournalistAlertEmailException) as e:
            site_config.validate_journalist_alert_email()
        assert "Must contain a @" in str(e)

        site_config.config["journalist_alert_email"] = "good@email.com"
        assert site_config.validate_journalist_alert_email()

    @mock.patch("securedrop_admin.SiteConfig.validated_input", side_effect=lambda p, d, v, t: d)
    @mock.patch("securedrop_admin.SiteConfig.save")
    def test_update_config(self, mock_save, mock_validate_input):
        for file in ["site-specific", "key.asc"]:
            shutil.copy(join("tests", "files", file), CONFIG_DIR)
        site_config = securedrop_admin.SiteConfig()

        assert site_config.load_and_update_config()
        assert "user_defined_variable" in site_config.config
        mock_save.assert_called_once()
        mock_validate_input.assert_called()

    @mock.patch("securedrop_admin.SiteConfig.validated_input", side_effect=lambda p, d, v, t: d)
    @mock.patch("securedrop_admin.SiteConfig.validate_gpg_keys")
    def test_update_config_no_site_specific(self, validate_gpg_keys, mock_validate_input):
        site_config = securedrop_admin.SiteConfig()
        assert site_config.load_and_update_config()
        mock_validate_input.assert_called()
        validate_gpg_keys.assert_called_once()
        assert exists(SITE_CONFIG_PATH)

    def test_load_and_update_config(self):
        for file in ["site-specific", "key.asc"]:
            shutil.copy(join("tests", "files", file), CONFIG_DIR)
        site_config = securedrop_admin.SiteConfig()
        with mock.patch("securedrop_admin.SiteConfig.update_config"):
            site_config.load_and_update_config()
            assert site_config.config != {}

        shutil.copy(join("tests", "files", "site-specific-missing-entries"), SITE_CONFIG_PATH)
        site_config = securedrop_admin.SiteConfig()
        with mock.patch("securedrop_admin.SiteConfig.update_config"):
            site_config.load_and_update_config()
            assert site_config.config != {}

        os.remove(SITE_CONFIG_PATH)
        site_config = securedrop_admin.SiteConfig()
        with mock.patch("securedrop_admin.SiteConfig.update_config"):
            site_config.load_and_update_config()
            assert site_config.config == {}

    def get_desc(self, site_config, var):
        for desc in site_config.desc:
            if desc[0] == var:
                return desc

    def verify_desc_consistency_optional(self, site_config, desc):
        (var, default, etype, prompt, validator, transform, condition) = desc
        # verify the default passes validation
        if callable(default):
            default = default()
        assert site_config.user_prompt_config_one(desc, None) == default
        assert type(default) is etype

    def verify_desc_consistency(self, site_config, desc):
        self.verify_desc_consistency_optional(site_config, desc)

    def verify_prompt_boolean(self, site_config, desc):
        self.verify_desc_consistency(site_config, desc)
        (var, default, etype, prompt, validator, transform, condition) = desc
        assert site_config.user_prompt_config_one(desc, True) is True
        assert site_config.user_prompt_config_one(desc, False) is False
        assert site_config.user_prompt_config_one(desc, "YES") is True
        assert site_config.user_prompt_config_one(desc, "NO") is False

    def test_desc_conditional(self):
        """Ensure that conditional prompts behave correctly.

        Prompts which depend on another question should only be
        asked if the prior question was answered appropriately."""
        for file in ["site-specific", "key.asc"]:
            shutil.copy(join("tests", "files", file), CONFIG_DIR)

        questions = [
            (
                "first_question",
                False,
                bool,
                "Test Question 1",
                None,
                lambda x: x.lower() == "yes",
                lambda config: True,
            ),
            (
                "dependent_question",
                "default_value",
                str,
                "Test Question 2",
                None,
                None,
                lambda config: config.get("first_question", False),
            ),
        ]
        site_config = securedrop_admin.SiteConfig()
        site_config.desc = questions

        def auto_prompt(prompt, default, **kwargs):
            return default

        with mock.patch("prompt_toolkit.prompt", side_effect=auto_prompt):
            config = site_config.user_prompt_config()
            assert config["dependent_question"] != "default_value"

            edited_first_question = list(site_config.desc[0])
            edited_first_question[1] = True
            site_config.desc[0] = tuple(edited_first_question)

            config = site_config.user_prompt_config()
            assert config["dependent_question"] == "default_value"

    verify_prompt_ssh_users = verify_desc_consistency
    verify_prompt_app_ip = verify_desc_consistency
    verify_prompt_monitor_ip = verify_desc_consistency
    verify_prompt_app_hostname = verify_desc_consistency
    verify_prompt_monitor_hostname = verify_desc_consistency
    verify_prompt_dns_server = verify_desc_consistency

    verify_prompt_securedrop_app_pow_on_source_interface = verify_prompt_boolean
    verify_prompt_securedrop_app_https_on_source_interface = verify_prompt_boolean
    verify_prompt_enable_ssh_over_tor = verify_prompt_boolean

    verify_prompt_securedrop_app_gpg_public_key = verify_desc_consistency

    def verify_prompt_not_empty(self, site_config, desc):
        with pytest.raises(ValidationError):
            site_config.user_prompt_config_one(desc, "")

    def verify_prompt_fingerprint_optional(self, site_config, desc):
        fpr = "0123456 789012 34567890123456789ABCDEFABCD"
        clean_fpr = site_config.sanitize_fingerprint(fpr)
        assert site_config.user_prompt_config_one(desc, fpr) == clean_fpr

    def verify_desc_consistency_allow_empty(self, site_config, desc):
        (var, default, etype, prompt, validator, transform, condition) = desc
        # verify the default passes validation
        assert site_config.user_prompt_config_one(desc, None) == default
        assert type(default) is etype

    def verify_prompt_fingerprint(self, site_config, desc):
        self.verify_prompt_not_empty(site_config, desc)
        self.verify_prompt_fingerprint_optional(site_config, desc)

    verify_prompt_securedrop_app_gpg_fingerprint = verify_prompt_fingerprint
    verify_prompt_ossec_alert_gpg_public_key = verify_desc_consistency
    verify_prompt_ossec_gpg_fpr = verify_prompt_fingerprint
    verify_prompt_ossec_alert_email = verify_prompt_not_empty
    verify_prompt_journalist_alert_gpg_public_key = verify_desc_consistency_optional
    verify_prompt_journalist_gpg_fpr = verify_prompt_fingerprint_optional
    verify_prompt_journalist_alert_email = verify_desc_consistency_optional
    verify_prompt_securedrop_app_https_certificate_chain_src = verify_desc_consistency_optional
    verify_prompt_securedrop_app_https_certificate_key_src = verify_desc_consistency_optional
    verify_prompt_securedrop_app_https_certificate_cert_src = verify_desc_consistency_optional
    verify_prompt_smtp_relay = verify_prompt_not_empty
    verify_prompt_smtp_relay_port = verify_desc_consistency
    verify_prompt_daily_reboot_time = verify_desc_consistency
    verify_prompt_sasl_domain = verify_desc_consistency_allow_empty
    verify_prompt_sasl_username = verify_prompt_not_empty
    verify_prompt_sasl_password = verify_prompt_not_empty

    def verify_prompt_securedrop_supported_locales(self, site_config, desc):
        (var, default, etype, prompt, validator, transform, condition) = desc
        # verify the default passes validation
        assert site_config.user_prompt_config_one(desc, None) == default
        assert type(default) is etype
        assert site_config.user_prompt_config_one(desc, "fr_FR en_US") == ["fr_FR", "en_US"]
        assert site_config.user_prompt_config_one(desc, ["fr_FR", "en_US"]) == ["fr_FR", "en_US"]
        assert site_config.user_prompt_config_one(desc, "") == []
        with pytest.raises(ValidationError):
            site_config.user_prompt_config_one(desc, "wrong")

    def test_user_prompt_config_one(self):
        for file in ["SecureDrop.asc", "ossec.pub"]:
            shutil.copy(join("tests", "files", file), CONFIG_DIR)
        site_config = securedrop_admin.SiteConfig()

        def auto_prompt(prompt, default, **kwargs):
            if "validator" in kwargs and kwargs["validator"]:
                assert kwargs["validator"].validate(Document(default))
            return default

        with mock.patch("prompt_toolkit.prompt", side_effect=auto_prompt):
            for desc in site_config.desc:
                (var, default, etype, prompt, validator, transform, condition) = desc
                method = "verify_prompt_" + var
                print("checking " + method)
                getattr(self, method)(site_config, desc)

    def test_validated_input(self):
        site_config = securedrop_admin.SiteConfig()

        def auto_prompt(prompt, default, **kwargs):
            return default

        with mock.patch("prompt_toolkit.prompt", side_effect=auto_prompt):
            value = "VALUE"
            assert value == site_config.validated_input("", value, lambda: True, None)
            assert value.lower() == site_config.validated_input("", value, lambda: True, str.lower)
            assert site_config.validated_input("", True, lambda: True, None) == "yes"
            assert site_config.validated_input("", False, lambda: True, None) == "no"
            assert site_config.validated_input("", 1234, lambda: True, None) == "1234"
            assert site_config.validated_input("", ["a", "b"], lambda: True, None) == "a b"
            assert site_config.validated_input("", {}, lambda: True, None) == "{}"

    def test_load(self, caplog):
        for file in ["site-specific", "key.asc"]:
            shutil.copy(join("tests", "files", file), CONFIG_DIR)
        site_config = securedrop_admin.SiteConfig()
        assert "app_hostname" in site_config.load()

        shutil.rmtree(CONFIG_DIR, ignore_errors=True)
        os.makedirs(CONFIG_DIR, exist_ok=True)
        site_config = securedrop_admin.SiteConfig()
        with pytest.raises(IOError) as e:
            site_config.load()
        assert "No such file" in e.value.strerror
        assert "Config file missing" in caplog.text

        shutil.copy(join("tests", "files", "corrupted"), SITE_CONFIG_PATH)
        site_config = securedrop_admin.SiteConfig()
        with pytest.raises(yaml.YAMLError) as e:
            site_config.load()
        assert "issue processing" in caplog.text


def test_generate_new_v3_keys():
    public, private = securedrop_admin.generate_new_v3_keys()

    for key in [public, private]:
        # base32 padding characters should be removed
        assert "=" not in key
        assert len(key) == 52


def test_find_or_generate_new_torv3_keys_first_run(capsys):
    os.makedirs(CONFIG_DIR, exist_ok=True)

    args = argparse.Namespace()
    return_code = securedrop_admin.find_or_generate_new_torv3_keys(args)

    out, err = capsys.readouterr()
    assert "Tor v3 onion service keys generated" in out
    assert return_code == 0

    secret_key_path = join(CONFIG_DIR, "tor_v3_keys.json")

    with open(secret_key_path) as f:
        v3_onion_service_keys = json.load(f)

    expected_keys = [
        "app_journalist_public_key",
        "app_journalist_private_key",
        "app_ssh_public_key",
        "app_ssh_private_key",
        "mon_ssh_public_key",
        "mon_ssh_private_key",
    ]
    for key in expected_keys:
        assert key in v3_onion_service_keys


def test_find_or_generate_new_torv3_keys_subsequent_run(capsys):
    os.makedirs(CONFIG_DIR, exist_ok=True)

    args = argparse.Namespace()
    secret_key_path = join(CONFIG_DIR, "tor_v3_keys.json")
    old_keys = {"foo": "bar"}
    with open(secret_key_path, "w") as f:
        json.dump(old_keys, f)

    return_code = securedrop_admin.find_or_generate_new_torv3_keys(args)

    out, err = capsys.readouterr()
    assert "Tor v3 onion service keys already exist" in out
    assert return_code == 0

    with open(secret_key_path) as f:
        v3_onion_service_keys = json.load(f)

    assert v3_onion_service_keys == old_keys


class TestExportJournalistConfig:
    JOURNALIST_ONION = "sdolvtfhatvsysc6l34d65ymdwxcujausv7k5jk4cy5ttzhjoi6fzvyd.onion"
    JOURNALIST_KEY = "5U4JPYSZ34N2ZDSOUAL2YLEX2NPI5BLL2Y66QJW24KLSH7R3FEPQ"
    FINGERPRINT = "1234567890ABCDEF1234567890ABCDEF12345678"

    def setup_method(self, method):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(SITE_CONFIG_PATH, "w") as f:
            yaml.safe_dump({"securedrop_app_gpg_fingerprint": self.FINGERPRINT}, f)
        self.write_auth_file(
            f"{self.JOURNALIST_ONION[: -len('.onion')]}:descriptor:x25519:{self.JOURNALIST_KEY}"
        )

    def teardown_method(self, method):
        for path in (SITE_CONFIG_PATH, join(CONFIG_DIR, "app-journalist.auth_private")):
            if exists(path):
                os.remove(path)

    def write_auth_file(self, contents):
        with open(join(CONFIG_DIR, "app-journalist.auth_private"), "w") as f:
            f.write(contents + "\n")

    def args(self):
        return argparse.Namespace()

    def test_export_to_stdout(self, capsys):
        return_code = securedrop_admin.export_journalist_config(self.args())

        assert return_code == 0
        out, err = capsys.readouterr()
        assert json.loads(out) == {
            "submission_key_fpr": self.FINGERPRINT,
            "hidserv": {"hostname": self.JOURNALIST_ONION, "key": self.JOURNALIST_KEY},
            "environment": "prod",
            "vmsizes": {"sd_app": 10, "sd_log": 5},
        }

    def test_export_missing_fingerprint(self):
        with open(SITE_CONFIG_PATH, "w") as f:
            yaml.safe_dump({"app_hostname": "app"}, f)

        with pytest.raises(ValueError, match="Submission Key fingerprint is not set"):
            securedrop_admin.export_journalist_config(self.args())

    def test_export_missing_auth_file(self):
        os.remove(join(CONFIG_DIR, "app-journalist.auth_private"))

        with pytest.raises(ValueError, match="onion service file is missing"):
            securedrop_admin.export_journalist_config(self.args())

    def test_export_unparseable_auth_file(self):
        self.write_auth_file("not-an-onion-service")

        with pytest.raises(ValueError, match="Could not parse the onion service file"):
            securedrop_admin.export_journalist_config(self.args())

    def test_export_invalid_onion_address(self):
        self.write_auth_file(f"notanonion:descriptor:x25519:{self.JOURNALIST_KEY}")

        with pytest.raises(ValueError, match="Invalid onion address"):
            securedrop_admin.export_journalist_config(self.args())

    def test_export_invalid_key(self):
        self.write_auth_file(f"{self.JOURNALIST_ONION[: -len('.onion')]}:descriptor:x25519:nope")

        with pytest.raises(ValueError, match="Invalid onion service key"):
            securedrop_admin.export_journalist_config(self.args())
