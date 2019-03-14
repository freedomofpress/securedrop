# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2013-2018 Freedom of the Press Foundation & al
# Copyright (C) 2018 Loic Dachary <loic@dachary.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
SecureDrop Admin Toolkit.

For use by administrators to install, maintain, and manage their SD
instances.
"""

from __future__ import print_function
import argparse
import logging
import os
import io
import re
import string
import subprocess
import sys
import types
import prompt_toolkit
from prompt_toolkit.validation import Validator, ValidationError
import yaml
from pkg_resources import parse_version

sdlog = logging.getLogger(__name__)
RELEASE_KEY = '22245C81E3BAEB4138B36061310F561200F4AD77'
EXIT_SUCCESS = 0
EXIT_SUBPROCESS_ERROR = 1
EXIT_INTERRUPT = 2


class FingerprintException(Exception):
    pass


class JournalistAlertEmailException(Exception):
    pass


class SiteConfig(object):

    class ValidateNotEmpty(Validator):
        def validate(self, document):
            if document.text != '':
                return True
            raise ValidationError(
                message="Must not be an empty string")

    class ValidateTime(Validator):
        def validate(self, document):
            if document.text.isdigit() and int(document.text) in range(0, 24):
                return True
            raise ValidationError(
                message="Must be an integer between 0 and 23")

    class ValidateUser(Validator):
        def validate(self, document):
            text = document.text
            if text != '' and text != 'root' and text != 'amnesia':
                return True
            raise ValidationError(
                message="Must not be root, amnesia or an empty string")

    class ValidateIP(Validator):
        def validate(self, document):
            if re.match('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}$',
                        document.text):
                return True
            raise ValidationError(
                message="An IP address must be something like 10.240.20.83")

    class ValidateDNS(Validator):
        def validate(self):
            raise Exception()  # pragma: no cover

        def is_tails(self):
            try:
                id = subprocess.check_output('lsb_release --id --short',
                                             shell=True).strip()
            except subprocess.CalledProcessError:
                id = None
            return id == 'Tails'

        def lookup_fqdn(self, fqdn, dns=None):
            cmd = 'host -W=10 -T -4 ' + fqdn
            if self.is_tails():
                cmd = 'torify ' + cmd
            cmd += ' ' + (dns and dns or '8.8.8.8')
            try:
                result = subprocess.check_output(cmd.split(' '),
                                                 stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                result = e.output
            sdlog.debug(cmd + ' => ' + result)
            return 'has address' in result

    class ValidateDNSServer(ValidateDNS):
        def validate(self, document):
            if self.lookup_fqdn('gnu.org', document.text):
                return True
            raise ValidationError(
                message='Unable to resolve gnu.org using this DNS')

    class ValidateFQDN(ValidateDNS):
        def validate(self, document):
            if self.lookup_fqdn(document.text):
                return True
            raise ValidationError(
                message='Unable to resolve ' + document.text)

    class ValidatePath(Validator):
        def __init__(self, basedir):
            self.basedir = basedir
            super(SiteConfig.ValidatePath, self).__init__()

        def validate(self, document):
            if document.text == '':
                raise ValidationError(
                    message='an existing file name is required')
            path = os.path.join(self.basedir, document.text)
            if os.path.exists(path):
                return True
            raise ValidationError(
                message=path + ' file does not exist')

    class ValidateOptionalPath(ValidatePath):
        def validate(self, document):
            if document.text == '':
                return True
            return super(SiteConfig.ValidateOptionalPath, self).validate(
                document)

    class ValidateYesNo(Validator):
        def validate(self, document):
            text = document.text.lower()
            if text == 'yes' or text == 'no':
                return True
            raise ValidationError(message="Must be either yes or no")

    class ValidateFingerprint(Validator):
        def validate(self, document):
            text = document.text.replace(' ', '')
            if text == '65A1B5FF195B56353CC63DFFCC40EF1228271441':
                raise ValidationError(
                    message='This is the TEST journalist fingerprint')
            if text == '600BC6D5142C68F35DDBCEA87B597104EDDDC102':
                raise ValidationError(
                    message='This is the TEST admin fingerprint')
            if not re.match('[a-fA-F0-9]{40}$', text):
                raise ValidationError(
                    message='fingerprints must be 40 hexadecimal characters')
            return True

    class ValidateOptionalFingerprint(ValidateFingerprint):
        def validate(self, document):
            if document.text == '':
                return True
            return super(SiteConfig.ValidateOptionalFingerprint,
                         self).validate(document)

    class ValidateInt(Validator):
        def validate(self, document):
            if re.match('\d+$', document.text):
                return True
            raise ValidationError(message="Must be an integer")

    class Locales(object):
        def __init__(self, appdir):
            self.translation_dir = os.path.realpath(
                os.path.join(appdir, 'translations'))

        def get_translations(self):
            translations = set(['en_US'])
            for dirname in os.listdir(self.translation_dir):
                if dirname != 'messages.pot':
                    translations.add(dirname)
            return translations

    class ValidateLocales(Validator):
        def __init__(self, basedir):
            self.basedir = basedir
            super(SiteConfig.ValidateLocales, self).__init__()

        def validate(self, document):
            desired = document.text.split()
            existing = SiteConfig.Locales(self.basedir).get_translations()
            missing = set(desired) - set(existing)
            if not missing:
                return True
            raise ValidationError(
                message="The following locales do not exist " + " ".join(
                    missing))

    class ValidateOSSECUsername(Validator):
        def validate(self, document):
            text = document.text
            if text and '@' not in text and 'test' != text:
                return True
            raise ValidationError(
                message="The SASL username should not include the domain name")

    class ValidateOSSECPassword(Validator):
        def validate(self, document):
            text = document.text
            if len(text) >= 8 and 'password123' != text:
                return True
            raise ValidationError(
                message="Password for OSSEC email account must be strong")

    class ValidateEmail(Validator):
        def validate(self, document):
            text = document.text
            if text == '':
                raise ValidationError(
                    message=("Must not be empty"))
            if '@' not in text:
                raise ValidationError(
                    message=("Must contain a @"))
            return True

    class ValidateOSSECEmail(ValidateEmail):
        def validate(self, document):
            super(SiteConfig.ValidateOSSECEmail, self).validate(document)
            text = document.text
            if 'ossec@ossec.test' != text:
                return True
            raise ValidationError(
                message=("Must be set to something other than "
                         "ossec@ossec.test"))

    class ValidateOptionalEmail(ValidateEmail):
        def validate(self, document):
            if document.text == '':
                return True
            return super(SiteConfig.ValidateOptionalEmail, self).validate(
                document)

    def __init__(self, args):
        self.args = args
        self.config = {}
        translations = SiteConfig.Locales(
            self.args.app_path).get_translations()
        translations = " ".join(translations)
        self.desc = [
            ['ssh_users', 'sd', str,
             u'Username for SSH access to the servers',
             SiteConfig.ValidateUser(),
             None,
             lambda config: True],
            ['daily_reboot_time', 4, int,
             u'Daily reboot time of the server (24-hour clock)',
             SiteConfig.ValidateTime(),
             int,
             lambda config: True],
            ['app_ip', '10.20.2.2', str,
             u'Local IPv4 address for the Application Server',
             SiteConfig.ValidateIP(),
             None,
             lambda config: True],
            ['monitor_ip', '10.20.3.2', str,
             u'Local IPv4 address for the Monitor Server',
             SiteConfig.ValidateIP(),
             None,
             lambda config: True],
            ['app_hostname', 'app', str,
             u'Hostname for Application Server',
             SiteConfig.ValidateNotEmpty(),
             None,
             lambda config: True],
            ['monitor_hostname', 'mon', str,
             u'Hostname for Monitor Server',
             SiteConfig.ValidateNotEmpty(),
             None,
             lambda config: True],
            ['dns_server', '8.8.8.8', str,
             u'DNS server specified during installation',
             SiteConfig.ValidateNotEmpty(),
             None,
             lambda config: True],
            ['securedrop_app_gpg_public_key', 'SecureDrop.asc', str,
             u'Local filepath to public key for '
             'SecureDrop Application GPG public key',
             SiteConfig.ValidatePath(self.args.ansible_path),
             None,
             lambda config: True],
            ['securedrop_app_https_on_source_interface', False, bool,
             u'Whether HTTPS should be enabled on '
             'Source Interface (requires EV cert)',
             SiteConfig.ValidateYesNo(),
             lambda x: x.lower() == 'yes',
             lambda config: True],
            ['securedrop_app_https_certificate_cert_src', '', str,
             u'Local filepath to HTTPS certificate',
             SiteConfig.ValidateOptionalPath(self.args.ansible_path),
             None,
             lambda config: config.get(
                'securedrop_app_https_on_source_interface')],
            ['securedrop_app_https_certificate_key_src', '', str,
             u'Local filepath to HTTPS certificate key',
             SiteConfig.ValidateOptionalPath(self.args.ansible_path),
             None,
             lambda config: config.get(
                'securedrop_app_https_on_source_interface')],
            ['securedrop_app_https_certificate_chain_src', '', str,
             u'Local filepath to HTTPS certificate chain file',
             SiteConfig.ValidateOptionalPath(self.args.ansible_path),
             None,
             lambda config: config.get(
                'securedrop_app_https_on_source_interface')],
            ['securedrop_app_gpg_fingerprint', '', str,
             u'Full fingerprint for the SecureDrop Application GPG Key',
             SiteConfig.ValidateFingerprint(),
             self.sanitize_fingerprint,
             lambda config: True],
            ['ossec_alert_gpg_public_key', 'ossec.pub', str,
             u'Local filepath to OSSEC alerts GPG public key',
             SiteConfig.ValidatePath(self.args.ansible_path),
             None,
             lambda config: True],
            ['ossec_gpg_fpr', '', str,
             u'Full fingerprint for the OSSEC alerts GPG public key',
             SiteConfig.ValidateFingerprint(),
             self.sanitize_fingerprint,
             lambda config: True],
            ['ossec_alert_email', '', str,
             u'Admin email address for receiving OSSEC alerts',
             SiteConfig.ValidateOSSECEmail(),
             None,
             lambda config: True],
            ['journalist_alert_gpg_public_key', '', str,
             u'Local filepath to journalist alerts GPG public key (optional)',
             SiteConfig.ValidateOptionalPath(self.args.ansible_path),
             None,
             lambda config: True],
            ['journalist_gpg_fpr', '', str,
             u'Full fingerprint for the journalist alerts '
             u'GPG public key (optional)',
             SiteConfig.ValidateOptionalFingerprint(),
             self.sanitize_fingerprint,
             lambda config: config.get('journalist_alert_gpg_public_key')],
            ['journalist_alert_email', '', str,
             u'Email address for receiving journalist alerts (optional)',
             SiteConfig.ValidateOptionalEmail(),
             None,
             lambda config: config.get('journalist_alert_gpg_public_key')],
            ['smtp_relay', "smtp.gmail.com", str,
             u'SMTP relay for sending OSSEC alerts',
             SiteConfig.ValidateNotEmpty(),
             None,
             lambda config: True],
            ['smtp_relay_port', 587, int,
             u'SMTP port for sending OSSEC alerts',
             SiteConfig.ValidateInt(),
             int,
             lambda config: True],
            ['sasl_domain', "gmail.com", str,
             u'SASL domain for sending OSSEC alerts',
             None,
             None,
             lambda config: True],
            ['sasl_username', '', str,
             u'SASL username for sending OSSEC alerts',
             SiteConfig.ValidateOSSECUsername(),
             None,
             lambda config: True],
            ['sasl_password', '', str,
             u'SASL password for sending OSSEC alerts',
             SiteConfig.ValidateOSSECPassword(),
             None,
             lambda config: True],
            ['enable_ssh_over_tor', True, bool,
             u'Enable SSH over Tor (recommended, disables SSH over LAN). '
             u'If you respond no, SSH will be available over LAN only',
             SiteConfig.ValidateYesNo(),
             lambda x: x.lower() == 'yes',
             lambda config: True],
            ['securedrop_supported_locales', [], types.ListType,
             u'Space separated list of additional locales to support '
             '(' + translations + ')',
             SiteConfig.ValidateLocales(self.args.app_path),
             string.split,
             lambda config: True],
        ]

    def load_and_update_config(self):
        if self.exists():
            self.config = self.load()

        return self.update_config()

    def update_config(self):
        self.config.update(self.user_prompt_config())
        self.save()
        self.validate_gpg_keys()
        self.validate_journalist_alert_email()
        return True

    def user_prompt_config(self):
        config = {}
        for desc in self.desc:
            (var, default, type, prompt, validator, transform,
                condition) = desc
            if not condition(config):
                config[var] = ''
                continue
            config[var] = self.user_prompt_config_one(desc,
                                                      self.config.get(var))
        return config

    def user_prompt_config_one(self, desc, from_config):
        (var, default, type, prompt, validator, transform, condition) = desc
        if from_config is not None:
            default = from_config
        prompt += ': '
        return self.validated_input(prompt, default, validator, transform)

    def validated_input(self, prompt, default, validator, transform):
        if type(default) is bool:
            default = default and 'yes' or 'no'
        if type(default) is int:
            default = str(default)
        if isinstance(default, types.ListType):
            default = " ".join(default)
        if type(default) is not str:
            default = str(default)
        kwargs = {}
        if validator:
            kwargs['validator'] = validator
        value = prompt_toolkit.prompt(prompt,
                                      default=unicode(default, 'utf-8'),
                                      **kwargs)
        if transform:
            return transform(value)
        else:
            return value

    def sanitize_fingerprint(self, value):
        return value.upper().replace(' ', '')

    def validate_gpg_keys(self):
        keys = (('securedrop_app_gpg_public_key',
                 'securedrop_app_gpg_fingerprint'),

                ('ossec_alert_gpg_public_key',
                 'ossec_gpg_fpr'),

                ('journalist_alert_gpg_public_key',
                 'journalist_gpg_fpr'))
        validate = os.path.join(
            os.path.dirname(__file__), '..', 'bin',
            'validate-gpg-key.sh')
        for (public_key, fingerprint) in keys:
            if (self.config[public_key] == '' and
                    self.config[fingerprint] == ''):
                continue
            public_key = os.path.join(self.args.ansible_path,
                                      self.config[public_key])
            fingerprint = self.config[fingerprint]
            try:
                sdlog.debug(subprocess.check_output(
                    [validate, public_key, fingerprint],
                    stderr=subprocess.STDOUT))
            except subprocess.CalledProcessError as e:
                sdlog.debug(e.output)
                raise FingerprintException(
                    "fingerprint {} ".format(fingerprint) +
                    "does not match " +
                    "the public key {}".format(public_key))
        return True

    def validate_journalist_alert_email(self):
        if (self.config['journalist_alert_gpg_public_key'] == '' and
                self.config['journalist_gpg_fpr'] == ''):
            return True

        class Document(object):
            def __init__(self, text):
                self.text = text

        try:
            SiteConfig.ValidateEmail().validate(Document(
                self.config['journalist_alert_email']))
        except ValidationError as e:
            raise JournalistAlertEmailException(
                "journalist alerts email: " + e.message)
        return True

    def exists(self):
        return os.path.exists(self.args.site_config)

    def save(self):
        with io.open(self.args.site_config, 'w') as site_config_file:
            yaml.safe_dump(self.config,
                           site_config_file,
                           default_flow_style=False)

    def load(self):
        try:
            with io.open(self.args.site_config) as site_config_file:
                return yaml.safe_load(site_config_file)
        except IOError:
            sdlog.error("Config file missing, re-run with sdconfig")
            raise
        except yaml.YAMLError:
            sdlog.error("There was an issue processing {}".format(
                self.args.site_config))
            raise


def setup_logger(verbose=False):
    """ Configure logging handler """
    # Set default level on parent
    sdlog.setLevel(logging.DEBUG)
    level = logging.DEBUG if verbose else logging.INFO

    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    stdout.setLevel(level)
    sdlog.addHandler(stdout)


def sdconfig(args):
    """Configure SD site settings"""
    SiteConfig(args).load_and_update_config()
    return 0


def install_securedrop(args):
    """Install/Update SecureDrop"""
    SiteConfig(args).load()

    sdlog.info("Now installing SecureDrop on remote servers.")
    sdlog.info("You will be prompted for the sudo password on the "
               "servers.")
    sdlog.info("The sudo password is only necessary during initial "
               "installation.")
    return subprocess.check_call([os.path.join(args.ansible_path,
                                 'securedrop-prod.yml'), '--ask-become-pass'],
                                 cwd=args.ansible_path)


def backup_securedrop(args):
    """Perform backup of the SecureDrop Application Server.
    Creates a tarball of submissions and server config, and fetches
    back to the Admin Workstation. Future `restore` actions can be performed
    with the backup tarball."""
    sdlog.info("Backing up the SecureDrop Application Server")
    ansible_cmd = [
        'ansible-playbook',
        os.path.join(args.ansible_path, 'securedrop-backup.yml'),
    ]
    return subprocess.check_call(ansible_cmd, cwd=args.ansible_path)


def restore_securedrop(args):
    """Perform restore of the SecureDrop Application Server.
    Requires a tarball of submissions and server config, created via
    the `backup` action."""
    sdlog.info("Restoring the SecureDrop Application Server from backup")
    # Canonicalize filepath to backup tarball, so Ansible sees only the
    # basename. The files must live in args.ansible_path,
    # but the securedrop-admin
    # script will be invoked from the repo root, so preceding dirs are likely.
    restore_file_basename = os.path.basename(args.restore_file)
    ansible_cmd = [
        'ansible-playbook',
        os.path.join(args.ansible_path, 'securedrop-restore.yml'),
        '-e',
        "restore_file='{}'".format(restore_file_basename),
    ]
    return subprocess.check_call(ansible_cmd, cwd=args.ansible_path)


def run_tails_config(args):
    """Configure Tails environment post SD install"""
    sdlog.info("Configuring Tails workstation environment")
    sdlog.info(("You'll be prompted for the temporary Tails admin password,"
                " which was set on Tails login screen"))
    ansible_cmd = [
        os.path.join(args.ansible_path, 'securedrop-tails.yml'),
        "--ask-become-pass",
        # Passing an empty inventory file to override the automatic dynamic
        # inventory script, which fails if no site vars are configured.
        '-i', '/dev/null',
    ]
    return subprocess.check_call(ansible_cmd,
                                 cwd=args.ansible_path)


def check_for_updates_wrapper(args):
    res, tag = check_for_updates(args)
    # Because the command worked properly exit with 0.
    return 0


def check_for_updates(args):
    """Check for SecureDrop updates"""
    sdlog.info("Checking for SecureDrop updates...")

    # Determine what branch we are on
    current_tag = subprocess.check_output(['git', 'describe'],
                                          cwd=args.root).rstrip('\n')

    # Fetch all branches
    git_fetch_cmd = ['git', 'fetch', '--all']
    subprocess.check_call(git_fetch_cmd, cwd=args.root)

    # Get latest tag
    git_all_tags = ["git", "tag"]
    all_tags = subprocess.check_output(git_all_tags,
                                       cwd=args.root).rstrip('\n').split('\n')

    # Do not check out any release candidate tags
    all_prod_tags = [x for x in all_tags if 'rc' not in x]

    # We want the tags to be sorted based on semver
    all_prod_tags.sort(key=parse_version)

    latest_tag = all_prod_tags[-1]

    if current_tag != latest_tag:
        sdlog.info("Update needed")
        return True, latest_tag
    sdlog.info("All updates applied")
    return False, latest_tag


def get_release_key_from_keyserver(args, keyserver=None, timeout=45):
    gpg_recv = ['timeout', str(timeout), 'gpg', '--batch', '--no-tty',
            '--recv-key']
    release_key = [RELEASE_KEY]

    # We construct the gpg --recv-key command based on optional keyserver arg.
    if keyserver:
        get_key_cmd = gpg_recv + ['--keyserver', keyserver] + release_key
    else:
        get_key_cmd = gpg_recv + release_key

    subprocess.check_call(get_key_cmd, cwd=args.root)


def update(args):
    """Verify, and apply latest SecureDrop workstation update"""
    sdlog.info("Applying SecureDrop updates...")

    update_status, latest_tag = check_for_updates(args)

    if not update_status:
        # Exit if we're up to date
        return 0

    sdlog.info("Verifying signature on latest update...")

    try:
        # First try to get the release key using Tails default keyserver
        get_release_key_from_keyserver(args)
    except subprocess.CalledProcessError:
        # Now try to get the key from a secondary keyserver.
        secondary_keyserver = 'hkps://hkps.pool.sks-keyservers.net'
        get_release_key_from_keyserver(args,
                                       keyserver=secondary_keyserver)

    git_verify_tag_cmd = ['git', 'tag', '-v', latest_tag]
    try:
        sig_result = subprocess.check_output(git_verify_tag_cmd,
                                             stderr=subprocess.STDOUT,
                                             cwd=args.root)

        good_sig_text = 'Good signature from "SecureDrop Release Signing Key"'
        bad_sig_text = 'BAD signature'
        # To ensure that an adversary cannot name a malicious key good_sig_text
        # we check that bad_sig_text does not appear and that the release key
        # appears on the second line of the output.
        gpg_lines = sig_result.split('\n')
        if RELEASE_KEY in gpg_lines[1] and \
                sig_result.count(good_sig_text) == 1 and \
                bad_sig_text not in sig_result:
            # Finally, we check that there is no branch of the same name
            # prior to reporting success.
            cmd = ['git', 'show-ref', '--heads', '--verify',
                   'refs/heads/{}'.format(latest_tag)]
            try:
                # We expect this to produce a non-zero exit code, which
                # will produce a subprocess.CalledProcessError
                subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                        cwd=args.root)
                sdlog.info("Signature verification failed.")
                return 1
            except subprocess.CalledProcessError, e:
                if 'not a valid ref' in e.output:
                    # Then there is no duplicate branch.
                    sdlog.info("Signature verification successful.")
                else:  # If any other exception occurs, we bail.
                    sdlog.info("Signature verification failed.")
                    return 1
        else:  # If anything else happens, fail and exit 1
            sdlog.info("Signature verification failed.")
            return 1

    except subprocess.CalledProcessError:
        # If there is no signature, or if the signature does not verify,
        # then git tag -v exits subprocess.check_output will exit 1
        # and subprocess.check_output will throw a CalledProcessError
        sdlog.info("Signature verification failed.")
        return 1

    # Only if the proper signature verifies do we check out the latest
    git_checkout_cmd = ['git', 'checkout', latest_tag]
    subprocess.check_call(git_checkout_cmd, cwd=args.root)

    sdlog.info("Updated to SecureDrop {}.".format(latest_tag))
    return 0


def get_logs(args):
    """Get logs for forensics and debugging purposes"""
    sdlog.info("Gathering logs for forensics and debugging")
    ansible_cmd = [
        'ansible-playbook',
        os.path.join(args.ansible_path, 'securedrop-logs.yml'),
    ]
    subprocess.check_call(ansible_cmd, cwd=args.ansible_path)
    sdlog.info("Encrypt logs and send to securedrop@freedom.press or upload "
               "to the SecureDrop support portal.")
    return 0


def set_default_paths(args):
    if not args.ansible_path:
        args.ansible_path = args.root + "/install_files/ansible-base"
    args.ansible_path = os.path.realpath(args.ansible_path)
    if not args.site_config:
        args.site_config = args.ansible_path + "/group_vars/all/site-specific"
    args.site_config = os.path.realpath(args.site_config)
    if not args.app_path:
        args.app_path = args.root + "/securedrop"
    args.app_path = os.path.realpath(args.app_path)
    return args


def parse_argv(argv):
    class ArgParseFormatterCombo(argparse.ArgumentDefaultsHelpFormatter,
                                 argparse.RawTextHelpFormatter):
        """Needed to combine formatting classes for help output"""
        pass

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=ArgParseFormatterCombo)
    parser.add_argument('-v', action='store_true', default=False,
                        help="Increase verbosity on output")
    parser.add_argument('-d', action='store_true', default=False,
                        help="Developer mode. Not to be used in production.")
    parser.add_argument('--root', required=True,
                        help="path to the root of the SecureDrop repository")
    parser.add_argument('--site-config',
                        help="path to the YAML site configuration file")
    parser.add_argument('--ansible-path',
                        help="path to the Ansible root")
    parser.add_argument('--app-path',
                        help="path to the SecureDrop application root")
    subparsers = parser.add_subparsers()

    parse_sdconfig = subparsers.add_parser('sdconfig', help=sdconfig.__doc__)
    parse_sdconfig.set_defaults(func=sdconfig)

    parse_install = subparsers.add_parser('install',
                                          help=install_securedrop.__doc__)
    parse_install.set_defaults(func=install_securedrop)

    parse_tailsconfig = subparsers.add_parser('tailsconfig',
                                              help=run_tails_config.__doc__)
    parse_tailsconfig.set_defaults(func=run_tails_config)

    parse_backup = subparsers.add_parser('backup',
                                         help=backup_securedrop.__doc__)
    parse_backup.set_defaults(func=backup_securedrop)

    parse_restore = subparsers.add_parser('restore',
                                          help=restore_securedrop.__doc__)
    parse_restore.set_defaults(func=restore_securedrop)
    parse_restore.add_argument("restore_file")

    parse_update = subparsers.add_parser('update', help=update.__doc__)
    parse_update.set_defaults(func=update)

    parse_check_updates = subparsers.add_parser('check_for_updates',
                                                help=check_for_updates.__doc__)
    parse_check_updates.set_defaults(func=check_for_updates_wrapper)

    parse_logs = subparsers.add_parser('logs',
                                       help=get_logs.__doc__)
    parse_logs.set_defaults(func=get_logs)

    return set_default_paths(parser.parse_args(argv))


def main(argv):
    args = parse_argv(argv)
    setup_logger(args.v)
    if args.v:
        return_code = args.func(args)
        if return_code != 0:
            sys.exit(EXIT_SUBPROCESS_ERROR)
    else:
        try:
            return_code = args.func(args)
        except KeyboardInterrupt:
            print('Process was interrupted.')
            sys.exit(EXIT_INTERRUPT)
        except subprocess.CalledProcessError as e:
            print('ERROR (run with -v for more): {msg}'.format(msg=e),
                  file=sys.stderr)
            sys.exit(EXIT_SUBPROCESS_ERROR)
        except Exception as e:
            raise SystemExit(
                'ERROR (run with -v for more): {msg}'.format(msg=e))
    if return_code == 0:
        sys.exit(EXIT_SUCCESS)
    else:
        sys.exit(EXIT_SUBPROCESS_ERROR)


if __name__ == "__main__":
    main(sys.argv[1:])
