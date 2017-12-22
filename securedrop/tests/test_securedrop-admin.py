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
import imp
from os.path import abspath, dirname, join, realpath, basename
import mock
from prompt_toolkit.validation import ValidationError
import pytest
import string
import subprocess
import textwrap
import yaml

here = abspath(join(dirname(realpath(__file__))))
securedrop_admin = imp.load_source('sa', here + '/../securedrop-admin')


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

    def test_run_command(self):
        for output_line in securedrop_admin.run_command(
                ['/bin/echo', 'something']):
            assert output_line.strip() == 'something'

        lines = []
        with pytest.raises(subprocess.CalledProcessError):
            for output_line in securedrop_admin.run_command(
                    ['sh', '-c',
                     'echo in stdout ; echo in stderr >&2 ; false']):
                lines.append(output_line.strip())
        assert lines[0] == 'in stdout'
        assert lines[1] == 'in stderr'

    def test_install_pip_dependencies_up_to_date(self, caplog):
        args = argparse.Namespace()
        securedrop_admin.install_pip_dependencies(args, ['/bin/echo'])
        assert 'securedrop-admin are up-to-date' in caplog.text

    def test_install_pip_dependencies_upgraded(self, caplog):
        args = argparse.Namespace()
        securedrop_admin.install_pip_dependencies(
            args, ['/bin/echo', 'Successfully installed'])
        assert 'securedrop-admin upgraded' in caplog.text

    def test_install_pip_dependencies_fail(self, caplog):
        args = argparse.Namespace()
        with pytest.raises(subprocess.CalledProcessError):
            securedrop_admin.install_pip_dependencies(
                args, ['/bin/sh', '-c',
                       'echo in stdout ; echo in stderr >&2 ; false'])
        assert 'Failed to install' in caplog.text
        assert 'in stdout' in caplog.text
        assert 'in stderr' in caplog.text


class TestSiteConfig(object):

    def test_exists(self):
        args = argparse.Namespace(site_config='DOES_NOT_EXIST',
                                  ansible_path='.',
                                  app_path='.')
        assert not securedrop_admin.SiteConfig(args).exists()
        args = argparse.Namespace(site_config=__file__,
                                  ansible_path='.',
                                  app_path='.')
        assert securedrop_admin.SiteConfig(args).exists()

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
        with mock.patch('sa.SiteConfig.ValidateDNS.is_tails',
                        return_value=True):
            with mock.patch('subprocess.check_output',
                            return_value='has address') as check_output:
                assert validator.lookup_fqdn('gnu.org', '8.8.8.8')
                assert check_output.call_args[0][0].startswith('torify')
                assert check_output.call_args[0][0].endswith('8.8.8.8')

        with mock.patch('sa.SiteConfig.ValidateDNS.is_tails',
                        return_value=False):
            with mock.patch('subprocess.check_output',
                            return_value='failed') as check_output:
                assert validator.lookup_fqdn('gnu.org') is False
                assert not check_output.call_args[0][0].startswith('torify')
                assert 'failed' in caplog.text()

        with mock.patch('sa.SiteConfig.ValidateDNS.is_tails',
                        return_value=False):
            with mock.patch('subprocess.check_output',
                            side_effect=subprocess.CalledProcessError(
                                1, 'cmd', 'BANG')):
                assert validator.lookup_fqdn('gnu.org') is False
                assert 'BANG' in caplog.text()

    def test_validate_dns_server(self, caplog):
        validator = securedrop_admin.SiteConfig.ValidateDNSServer()
        with mock.patch('sa.SiteConfig.ValidateDNS.lookup_fqdn',
                        return_value=True):
            assert validator.validate(Document('8.8.8.8'))
        with mock.patch('sa.SiteConfig.ValidateDNS.lookup_fqdn',
                        return_value=False):
            with pytest.raises(ValidationError):
                validator.validate(Document('8.8.8.8'))

    def test_lookup_fqdn(self, caplog):
        validator = securedrop_admin.SiteConfig.ValidateFQDN()
        with mock.patch('sa.SiteConfig.ValidateDNS.lookup_fqdn',
                        return_value=True):
            assert validator.validate(Document('gnu.org'))
        with mock.patch('sa.SiteConfig.ValidateDNS.lookup_fqdn',
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
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)
        assert "ABC" == site_config.sanitize_fingerprint("    A bc")

    def test_validate_int(self):
        validator = securedrop_admin.SiteConfig.ValidateInt()
        with pytest.raises(ValidationError):
            validator.validate(Document("123X"))
        assert validator.validate(Document("192"))

    def test_save(self, tmpdir):
        site_config_path = join(str(tmpdir), 'site_config')
        args = argparse.Namespace(site_config=site_config_path,
                                  ansible_path='.',
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)
        site_config.config = {'var1': u'val1', 'var2': u'val2'}
        site_config.save()
        expected = textwrap.dedent("""\
        var1: val1
        var2: val2
        """)
        assert expected == open(site_config_path).read()

    @mock.patch('sa.SiteConfig.validated_input',
                side_effect=lambda p, d, v, t: d)
    @mock.patch('sa.SiteConfig.save')
    def test_update_config(self, mock_save, mock_validate_input):
        args = argparse.Namespace(site_config='tests/files/site-specific',
                                  ansible_path='tests/files',
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)

        assert site_config.load_and_update_config()
        mock_save.assert_called_once()
        mock_validate_input.assert_called()

    def test_load_and_update_config(self):
        args = argparse.Namespace(site_config='tests/files/site-specific',
                                  ansible_path='tests/files',
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)
        with mock.patch('sa.SiteConfig.update_config'):
            site_config.load_and_update_config()
            assert site_config.config is not None

        args = argparse.Namespace(site_config='UNKNOWN',
                                  ansible_path='tests/files',
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)
        with mock.patch('sa.SiteConfig.update_config'):
            site_config.load_and_update_config()
            assert site_config.config is None

    def test_validated_input(self):
        args = argparse.Namespace(site_config='UNKNOWN',
                                  ansible_path='tests/files',
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)
        value = 'VALUE'
        with mock.patch('prompt_toolkit.prompt', return_value=value):
            assert value == site_config.validated_input(
                '', value, lambda: True, None)
            assert value.lower() == site_config.validated_input(
                '', value, lambda: True, string.lower)

    def test_load(self, caplog):
        args = argparse.Namespace(site_config='tests/files/site-specific',
                                  ansible_path='tests/files',
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)
        assert 'app_hostname' in site_config.load()

        args = argparse.Namespace(site_config='UNKNOWN',
                                  ansible_path='tests/files',
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)
        with pytest.raises(IOError) as e:
            site_config.load()
        assert 'No such file' in e.value.strerror
        assert 'Config file missing' in caplog.text()

        args = argparse.Namespace(site_config='tests/files/corrupted',
                                  ansible_path='tests/files',
                                  app_path='.')
        site_config = securedrop_admin.SiteConfig(args)
        with pytest.raises(yaml.YAMLError) as e:
            site_config.load()
        assert 'issue processing' in caplog.text()
