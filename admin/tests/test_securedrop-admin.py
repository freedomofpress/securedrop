# -*- coding: utf-8 -*-
#
# SecureDrop whistleblower submission system
# Copyright (C) 2017 Loic Dachary <loic@dachary.org>
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
from os.path import dirname, join, basename
import mock
from prompt_toolkit.validation import ValidationError
import pytest
import string
import subprocess
import textwrap
import yaml

import securedrop_admin


class Document(object):
    def __init__(self, text):
        self.text = text


class TestSecureDropAdmin(object):

    def test_verbose(self, capsys):
        securedrop_admin.setup_logger(verbose=True)
        securedrop_admin.sdlog.debug('VISIBLE')
        out, err = capsys.readouterr()
        assert 'VISIBLE' in out

    def test_not_verbose(self, capsys):
        securedrop_admin.setup_logger(verbose=False)
        securedrop_admin.sdlog.debug('HIDDEN')
        securedrop_admin.sdlog.info('VISIBLE')
        out, err = capsys.readouterr()
        assert 'HIDDEN' not in out
        assert 'VISIBLE' in out


class TestSiteConfig(object):

    def test_exists(self):
        args = argparse.Namespace(site_config='DOES_NOT_EXIST',
                                  ansible_path='.',
                                  app_path=dirname(__file__))
        assert not securedrop_admin.SiteConfig(args).exists()
        args = argparse.Namespace(site_config=__file__,
                                  ansible_path='.',
                                  app_path=dirname(__file__))
        assert securedrop_admin.SiteConfig(args).exists()

    def test_validate_not_empty(self):
        validator = securedrop_admin.SiteConfig.ValidateNotEmpty()

        assert validator.validate(Document('something'))
        with pytest.raises(ValidationError):
            validator.validate(Document(''))

    def test_validate_ossec_username(self):
        validator = securedrop_admin.SiteConfig.ValidateOSSECUsername()

        assert validator.validate(Document('username'))
        with pytest.raises(ValidationError):
            validator.validate(Document('bad@user'))
        with pytest.raises(ValidationError):
            validator.validate(Document('test'))

    def test_validate_ossec_password(self):
        validator = securedrop_admin.SiteConfig.ValidateOSSECPassword()

        assert validator.validate(Document('goodpassword'))
        with pytest.raises(ValidationError):
            validator.validate(Document('password123'))
        with pytest.raises(ValidationError):
            validator.validate(Document(''))
        with pytest.raises(ValidationError):
            validator.validate(Document('short'))

    def test_validate_ossec_email(self):
        validator = securedrop_admin.SiteConfig.ValidateOSSECEmail()

        assert validator.validate(Document('good@mail.com'))
        with pytest.raises(ValidationError):
            validator.validate(Document('badmail'))
        with pytest.raises(ValidationError):
            validator.validate(Document(''))
        with pytest.raises(ValidationError) as e:
            validator.validate(Document('ossec@ossec.test'))
        assert 'something other than ossec@ossec.test' in e.value.message

    def test_is_tails(self):
        validator = securedrop_admin.SiteConfig.ValidateDNS()
        with mock.patch('subprocess.check_output', return_value='Tails'):
            assert validator.is_tails()
        with mock.patch('subprocess.check_output', return_value='Debian'):
            assert validator.is_tails() is False
        with mock.patch('subprocess.check_output',
                        side_effect=subprocess.CalledProcessError(
                            1, 'cmd', 'BANG')):
            assert validator.is_tails() is False

    def test_lookup_dns(self, caplog):
        validator = securedrop_admin.SiteConfig.ValidateDNS()
        with mock.patch('securedrop_admin.SiteConfig.ValidateDNS.is_tails',
                        return_value=True):
            with mock.patch('subprocess.check_output',
                            return_value='has address') as check_output:
                assert validator.lookup_fqdn('gnu.org', '8.8.8.8')
                assert check_output.call_args[0][0].startswith('torify')
                assert check_output.call_args[0][0].endswith('8.8.8.8')

        with mock.patch('securedrop_admin.SiteConfig.ValidateDNS.is_tails',
                        return_value=False):
            with mock.patch('subprocess.check_output',
                            return_value='failed') as check_output:
                assert validator.lookup_fqdn('gnu.org') is False
                assert not check_output.call_args[0][0].startswith('torify')
                assert 'failed' in caplog.text

        with mock.patch('securedrop_admin.SiteConfig.ValidateDNS.is_tails',
                        return_value=False):
            with mock.patch('subprocess.check_output',
                            side_effect=subprocess.CalledProcessError(
                                1, 'cmd', 'BANG')):
                assert validator.lookup_fqdn('gnu.org') is False
                assert 'BANG' in caplog.text

    def test_validate_dns_server(self, caplog):
        validator = securedrop_admin.SiteConfig.ValidateDNSServer()
        with mock.patch('securedrop_admin.SiteConfig.ValidateDNS.lookup_fqdn',
                        return_value=True):
            assert validator.validate(Document('8.8.8.8'))
        with mock.patch('securedrop_admin.SiteConfig.ValidateDNS.lookup_fqdn',
                        return_value=False):
            with pytest.raises(ValidationError):
                validator.validate(Document('8.8.8.8'))

    def test_lookup_fqdn(self, caplog):
        validator = securedrop_admin.SiteConfig.ValidateFQDN()
        with mock.patch('securedrop_admin.SiteConfig.ValidateDNS.lookup_fqdn',
                        return_value=True):
            assert validator.validate(Document('gnu.org'))
        with mock.patch('securedrop_admin.SiteConfig.ValidateDNS.lookup_fqdn',
                        return_value=False):
            with pytest.raises(ValidationError):
                assert validator.validate(Document('gnu.org'))

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
        assert validator.validate(Document(
            "012345678901234567890123456789ABCDEFABCD"))
        assert validator.validate(Document(
            "01234 5678901234567890123456789ABCDE   FABCD"))

        with pytest.raises(ValidationError) as e:
            validator.validate(Document(
                "65A1B5FF195B56353CC63DFFCC40EF1228271441"))
        assert 'TEST journalist' in e.value.message

        with pytest.raises(ValidationError) as e:
            validator.validate(Document(
                "600BC6D5142C68F35DDBCEA87B597104EDDDC102"))
        assert 'TEST admin' in e.value.message

        with pytest.raises(ValidationError) as e:
            validator.validate(Document(
                "0000"))
        assert '40 hexadecimal' in e.value.message

        with pytest.raises(ValidationError) as e:
            validator.validate(Document(
                "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"))
        assert '40 hexadecimal' in e.value.message

    def test_sanitize_fingerprint(self):
        args = argparse.Namespace(site_config='DOES_NOT_EXIST',
                                  ansible_path='.',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        assert "ABC" == site_config.sanitize_fingerprint("    A bc")

    def test_validate_int(self):
        validator = securedrop_admin.SiteConfig.ValidateInt()
        with pytest.raises(ValidationError):
            validator.validate(Document("123X"))
        assert validator.validate(Document("192"))

    def test_locales(self):
        locales = securedrop_admin.SiteConfig.Locales(dirname(__file__))
        translations = locales.get_translations()
        assert 'en_US' in translations
        assert 'fr_FR' in translations

    def test_validate_locales(self):
        validator = securedrop_admin.SiteConfig.ValidateLocales(
            dirname(__file__))
        assert validator.validate(Document('en_US  fr_FR '))
        with pytest.raises(ValidationError) as e:
            validator.validate(Document('BAD'))
        assert 'BAD' in e.value.message

    def test_save(self, tmpdir):
        site_config_path = join(str(tmpdir), 'site_config')
        args = argparse.Namespace(site_config=site_config_path,
                                  ansible_path='.',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        site_config.config = {'var1': u'val1', 'var2': u'val2'}
        site_config.save()
        expected = textwrap.dedent("""\
        var1: val1
        var2: val2
        """)
        assert expected == open(site_config_path).read()

    def test_validate_gpg_key(self, caplog):
        args = argparse.Namespace(site_config='INVALID',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        site_config.config = {
            'securedrop_app_gpg_public_key':
            'test_journalist_key.pub',

            'securedrop_app_gpg_fingerprint':
            '65A1B5FF195B56353CC63DFFCC40EF1228271441',

            'ossec_alert_gpg_public_key':
            'test_journalist_key.pub',

            'ossec_gpg_fpr':
            '65A1B5FF195B56353CC63DFFCC40EF1228271441',
        }
        assert site_config.validate_gpg_keys()
        site_config.config['ossec_gpg_fpr'] = 'FAIL'
        with pytest.raises(securedrop_admin.FingerprintException) as e:
            site_config.validate_gpg_keys()
        assert 'FAIL does not match' in e.value.message

    @mock.patch('securedrop_admin.SiteConfig.validated_input',
                side_effect=lambda p, d, v, t: d)
    @mock.patch('securedrop_admin.SiteConfig.save')
    def test_update_config(self, mock_save, mock_validate_input):
        args = argparse.Namespace(site_config='tests/files/site-specific',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)

        assert site_config.load_and_update_config()
        assert 'user_defined_variable' in site_config.config
        mock_save.assert_called_once()
        mock_validate_input.assert_called()

    def test_load_and_update_config(self):
        args = argparse.Namespace(site_config='tests/files/site-specific',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        with mock.patch('securedrop_admin.SiteConfig.update_config'):
            site_config.load_and_update_config()
            assert site_config.config is not None

        args = argparse.Namespace(
            site_config='tests/files/site-specific-missing-entries',
            ansible_path='tests/files',
            app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        with mock.patch('securedrop_admin.SiteConfig.update_config'):
            site_config.load_and_update_config()
            assert site_config.config is not None

        args = argparse.Namespace(site_config='UNKNOWN',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        with mock.patch('securedrop_admin.SiteConfig.update_config'):
            site_config.load_and_update_config()
            assert site_config.config is None

    def get_desc(self, site_config, var):
        for desc in site_config.desc:
            if desc[0] == var:
                return desc

    def verify_desc_consistency(self, site_config, desc):
        (var, default, etype, prompt, validator, transform) = desc
        # verify the default passes validation
        assert site_config.user_prompt_config_one(desc, None) == default
        assert type(default) == etype
        with pytest.raises(ValidationError):
            site_config.user_prompt_config_one(desc, '')

    verify_prompt_ssh_users = verify_desc_consistency
    verify_prompt_app_ip = verify_desc_consistency
    verify_prompt_monitor_ip = verify_desc_consistency
    verify_prompt_app_hostname = verify_desc_consistency
    verify_prompt_monitor_hostname = verify_desc_consistency
    verify_prompt_dns_server = verify_desc_consistency

    def verify_prompt_securedrop_app_https_on_source_interface(
            self, site_config, desc):
        self.verify_desc_consistency(site_config, desc)
        (var, default, etype, prompt, validator, transform) = desc
        assert site_config.user_prompt_config_one(desc, True) is True
        assert site_config.user_prompt_config_one(desc, False) is False
        assert site_config.user_prompt_config_one(desc, 'YES') is True
        assert site_config.user_prompt_config_one(desc, 'NO') is False

    verify_prompt_securedrop_app_gpg_public_key = verify_desc_consistency

    def verify_prompt_not_empty(self, site_config, desc):
        with pytest.raises(ValidationError):
            site_config.user_prompt_config_one(desc, '')

    def verify_prompt_fingerprint(self, site_config, desc):
        self.verify_prompt_not_empty(site_config, desc)
        fpr = "0123456 789012 34567890123456789ABCDEFABCD"
        clean_fpr = site_config.sanitize_fingerprint(fpr)
        assert site_config.user_prompt_config_one(desc, fpr) == clean_fpr

    def verify_desc_consistency_allow_empty(self, site_config, desc):
        (var, default, etype, prompt, validator, transform) = desc
        # verify the default passes validation
        assert site_config.user_prompt_config_one(desc, None) == default
        assert type(default) == etype

    verify_prompt_securedrop_app_gpg_fingerprint = verify_prompt_fingerprint
    verify_prompt_ossec_alert_gpg_public_key = verify_desc_consistency
    verify_prompt_ossec_gpg_fpr = verify_prompt_fingerprint
    verify_prompt_ossec_alert_email = verify_prompt_not_empty
    verify_prompt_smtp_relay = verify_prompt_not_empty
    verify_prompt_smtp_relay_port = verify_desc_consistency
    verify_prompt_sasl_domain = verify_desc_consistency_allow_empty
    verify_prompt_sasl_username = verify_prompt_not_empty
    verify_prompt_sasl_password = verify_prompt_not_empty

    def verify_prompt_securedrop_supported_locales(self, site_config, desc):
        (var, default, etype, prompt, validator, transform) = desc
        # verify the default passes validation
        assert site_config.user_prompt_config_one(desc, None) == default
        assert type(default) == etype
        assert site_config.user_prompt_config_one(
            desc, 'fr_FR en_US') == ['fr_FR', 'en_US']
        assert site_config.user_prompt_config_one(
            desc, ['fr_FR', 'en_US']) == ['fr_FR', 'en_US']
        assert site_config.user_prompt_config_one(desc, '') == []
        with pytest.raises(ValidationError):
            site_config.user_prompt_config_one(desc, 'wrong')

    def test_user_prompt_config_one(self):
        args = argparse.Namespace(site_config='UNKNOWN',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)

        def auto_prompt(prompt, default, **kwargs):
            if 'validator' in kwargs:
                assert kwargs['validator'].validate(Document(default))
            return default

        with mock.patch('prompt_toolkit.prompt', side_effect=auto_prompt):
            for desc in site_config.desc:
                (var, default, etype, prompt, validator, transform) = desc
                method = 'verify_prompt_' + var
                print("checking " + method)
                getattr(self, method)(site_config, desc)

    def test_validated_input(self):
        args = argparse.Namespace(site_config='UNKNOWN',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)

        def auto_prompt(prompt, default, **kwargs):
            return default

        with mock.patch('prompt_toolkit.prompt', side_effect=auto_prompt):
            value = 'VALUE'
            assert value == site_config.validated_input(
                '', value, lambda: True, None)
            assert value.lower() == site_config.validated_input(
                '', value, lambda: True, string.lower)
            assert 'yes' == site_config.validated_input(
                '', True, lambda: True, None)
            assert 'no' == site_config.validated_input(
                '', False, lambda: True, None)
            assert '1234' == site_config.validated_input(
                '', 1234, lambda: True, None)
            assert "a b" == site_config.validated_input(
                '', ['a', 'b'], lambda: True, None)
            assert "{}" == site_config.validated_input(
                '', {}, lambda: True, None)

    def test_load(self, caplog):
        args = argparse.Namespace(site_config='tests/files/site-specific',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        assert 'app_hostname' in site_config.load()

        args = argparse.Namespace(site_config='UNKNOWN',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        with pytest.raises(IOError) as e:
            site_config.load()
        assert 'No such file' in e.value.strerror
        assert 'Config file missing' in caplog.text

        args = argparse.Namespace(site_config='tests/files/corrupted',
                                  ansible_path='tests/files',
                                  app_path=dirname(__file__))
        site_config = securedrop_admin.SiteConfig(args)
        with pytest.raises(yaml.YAMLError) as e:
            site_config.load()
        assert 'issue processing' in caplog.text
