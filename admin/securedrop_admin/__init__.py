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

import argparse
import functools
import ipaddress
import logging
import os
import io
import re
import subprocess
import sys
import json
import base64
from typing import Any
from typing import Optional
from typing import TypeVar
from typing import Union

import prompt_toolkit
from prompt_toolkit.document import Document
from prompt_toolkit.validation import Validator, ValidationError
import yaml
from pkg_resources import parse_version
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import x25519

from typing import cast

from typing import List

from typing import Set

from typing import Dict

from typing import Tuple

from typing import Callable

from typing import Type

sdlog = logging.getLogger(__name__)

# We list two (2) pubkeys as authorized to sign SecureDrop release artifacts,
# to provide a transition window during key rotation. On or around v2.0.0,
# we can remove the older of the two keys and only trust the newer going forward.
RELEASE_KEYS = [
    '22245C81E3BAEB4138B36061310F561200F4AD77',
    '2359E6538C0613E652955E6C188EDD3B7B22E6A3',
]
DEFAULT_KEYSERVER = 'hkps://keys.openpgp.org'
SUPPORT_ONION_URL = 'http://sup6h5iyiyenvjkfxbgrjynm5wsgijjoatvnvdgyyi7je3xqm4kh6uqd.onion'
SUPPORT_URL = 'https://support.freedom.press'
EXIT_SUCCESS = 0
EXIT_SUBPROCESS_ERROR = 1
EXIT_INTERRUPT = 2

MAX_NAMESERVERS = 3
LIST_SPLIT_RE = re.compile(r"\s*,\s*|\s+")


class FingerprintException(Exception):
    pass


class JournalistAlertEmailException(Exception):
    pass


# The type of each entry within SiteConfig.desc
_T = TypeVar('_T', bound=Union[int, str, bool])

# The function type used for the @update_check_required decorator; see
# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
_FuncT = TypeVar('_FuncT', bound=Callable[..., Any])

# Configuration description tuples drive the CLI user experience and the
# validation logic of the  securedrop-admin tool. A tuple is in the following
# format.
#
# (var, default, type, prompt, validator, transform, condition):
#
# var         configuration variable name (will be stored in `site-specific`)
# default     default value (can be a callable)
# type        configuration variable type
# prompt      text prompt presented to the user
# validator   input validator based on `prompt_toolkit`'s Validator class
# transform   transformation function to run on input
# condition   condition under which this prompt is shown, receives the
#             in-progress configuration object as input. Used for "if this
#             then that" branching of prompts.
#
# The mypy type description of the format follows.
_DescEntryType = Tuple[str, _T, Type[_T], str, Optional[Validator], Optional[Callable], Callable]


class SiteConfig:

    class ValidateNotEmpty(Validator):
        def validate(self, document: Document) -> bool:
            if document.text != '':
                return True
            raise ValidationError(
                message="Must not be an empty string")

    class ValidateTime(Validator):
        def validate(self, document: Document) -> bool:
            if document.text.isdigit() and int(document.text) in range(0, 24):
                return True
            raise ValidationError(
                message="Must be an integer between 0 and 23")

    class ValidateUser(Validator):
        def validate(self, document: Document) -> bool:
            text = document.text
            if text != '' and text != 'root' and text != 'amnesia':
                return True
            raise ValidationError(
                message="Must not be root, amnesia or an empty string")

    class ValidateIP(Validator):
        def validate(self, document: Document) -> bool:
            try:
                ipaddress.ip_address(document.text)
                return True
            except ValueError as e:
                raise ValidationError(message=str(e))

    class ValidateNameservers(Validator):
        def validate(self, document: Document) -> bool:
            candidates = LIST_SPLIT_RE.split(document.text)
            if len(candidates) > MAX_NAMESERVERS:
                raise ValidationError(message="Specify no more than three nameservers.")
            try:
                all(map(ipaddress.ip_address, candidates))
            except ValueError:
                raise ValidationError(
                    message=(
                        "DNS server(s) should be a space/comma-separated list "
                        "of up to {} IP addresses"
                    ).format(MAX_NAMESERVERS)
                )
            return True

    @staticmethod
    def split_list(text: str) -> List[str]:
        """
        Splits a string containing a list of values separated by commas or whitespace.
        """
        return LIST_SPLIT_RE.split(text)

    class ValidatePath(Validator):
        def __init__(self, basedir: str) -> None:
            self.basedir = basedir
            super(SiteConfig.ValidatePath, self).__init__()

        def validate(self, document: Document) -> bool:
            if document.text == '':
                raise ValidationError(
                    message='an existing file name is required')
            path = os.path.join(self.basedir, document.text)
            if os.path.exists(path):
                return True
            raise ValidationError(
                message=path + ' file does not exist')

    class ValidateOptionalPath(ValidatePath):
        def validate(self, document: Document) -> bool:
            if document.text == '':
                return True
            return super(SiteConfig.ValidateOptionalPath, self).validate(
                document)

    class ValidateYesNo(Validator):
        def validate(self, document: Document) -> bool:
            text = document.text.lower()
            if text == 'yes' or text == 'no':
                return True
            raise ValidationError(message="Must be either yes or no")

    class ValidateFingerprint(Validator):
        def validate(self, document: Document) -> bool:
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
        def validate(self, document: Document) -> bool:
            if document.text == '':
                return True
            return super(SiteConfig.ValidateOptionalFingerprint,
                         self).validate(document)

    class ValidateInt(Validator):
        def validate(self, document: Document) -> bool:
            if re.match(r'\d+$', document.text):
                return True
            raise ValidationError(message="Must be an integer")

    class Locales(object):
        def __init__(self, appdir: str) -> None:
            self.translation_dir = os.path.realpath(
                os.path.join(appdir, 'translations'))

        def get_translations(self) -> Set[str]:
            translations = set(['en_US'])
            for dirname in os.listdir(self.translation_dir):
                if dirname != 'messages.pot':
                    translations.add(dirname)
            return translations

    class ValidateLocales(Validator):
        def __init__(self, basedir: str) -> None:
            self.basedir = basedir
            super(SiteConfig.ValidateLocales, self).__init__()

        def validate(self, document: Document) -> bool:
            desired = document.text.split()
            existing = SiteConfig.Locales(self.basedir).get_translations()
            missing = set(desired) - set(existing)
            if not missing:
                return True
            raise ValidationError(
                message="The following locales do not exist " + " ".join(
                    missing))

    class ValidateOSSECUsername(Validator):
        def validate(self, document: Document) -> bool:
            text = document.text
            if text and '@' not in text and 'test' != text:
                return True
            raise ValidationError(
                message="The SASL username should not include the domain name")

    class ValidateOSSECPassword(Validator):
        def validate(self, document: Document) -> bool:
            text = document.text
            if len(text) >= 8 and 'password123' != text:
                return True
            raise ValidationError(
                message="Password for OSSEC email account must be strong")

    class ValidateEmail(Validator):
        def validate(self, document: Document) -> bool:
            text = document.text
            if text == '':
                raise ValidationError(
                    message=("Must not be empty"))
            if '@' not in text:
                raise ValidationError(
                    message=("Must contain a @"))
            return True

    class ValidateOSSECEmail(ValidateEmail):
        def validate(self, document: Document) -> bool:
            super(SiteConfig.ValidateOSSECEmail, self).validate(document)
            text = document.text
            if 'ossec@ossec.test' != text:
                return True
            raise ValidationError(
                message=("Must be set to something other than "
                         "ossec@ossec.test"))

    class ValidateOptionalEmail(ValidateEmail):
        def validate(self, document: Document) -> bool:
            if document.text == '':
                return True
            return super(SiteConfig.ValidateOptionalEmail, self).validate(
                document)

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        self.config = {}  # type: Dict
        # Hold runtime configuration before save, to support
        # referencing other responses during validation
        self._config_in_progress = {}  # type: Dict
        translations = SiteConfig.Locales(
            self.args.app_path).get_translations()
        translations_as_str = " ".join(translations)

        self.desc = [
            ('ssh_users', 'sd', str,
             'Username for SSH access to the servers',
             SiteConfig.ValidateUser(),
             None,
             lambda config: True),
            ('daily_reboot_time', 4, int,
             'Daily reboot time of the server (24-hour clock)',
             SiteConfig.ValidateTime(),
             int,
             lambda config: True),
            ('app_ip', '10.20.2.2', str,
             'Local IPv4 address for the Application Server',
             SiteConfig.ValidateIP(),
             None,
             lambda config: True),
            ('monitor_ip', '10.20.3.2', str,
             'Local IPv4 address for the Monitor Server',
             SiteConfig.ValidateIP(),
             None,
             lambda config: True),
            ('app_hostname', 'app', str,
             'Hostname for Application Server',
             SiteConfig.ValidateNotEmpty(),
             None,
             lambda config: True),
            ('monitor_hostname', 'mon', str,
             'Hostname for Monitor Server',
             SiteConfig.ValidateNotEmpty(),
             None,
             lambda config: True),
            ('dns_server', ['8.8.8.8', '8.8.4.4'], list,
             'DNS server(s)',
             SiteConfig.ValidateNameservers(),
             SiteConfig.split_list,
             lambda config: True),
            ('securedrop_app_gpg_public_key', 'SecureDrop.asc', str,
             'Local filepath to public key for ' +
             'SecureDrop Application GPG public key',
             SiteConfig.ValidatePath(self.args.ansible_path),
             None,
             lambda config: True),
            ('securedrop_app_https_on_source_interface', False, bool,
             'Whether HTTPS should be enabled on ' +
             'Source Interface (requires EV cert)',
             SiteConfig.ValidateYesNo(),
             lambda x: x.lower() == 'yes',
             lambda config: True),
            ('securedrop_app_https_certificate_cert_src', '', str,
             'Local filepath to HTTPS certificate',
             SiteConfig.ValidateOptionalPath(self.args.ansible_path),
             None,
             lambda config: config.get(
                'securedrop_app_https_on_source_interface')),
            ('securedrop_app_https_certificate_key_src', '', str,
             'Local filepath to HTTPS certificate key',
             SiteConfig.ValidateOptionalPath(self.args.ansible_path),
             None,
             lambda config: config.get(
                'securedrop_app_https_on_source_interface')),
            ('securedrop_app_https_certificate_chain_src', '', str,
             'Local filepath to HTTPS certificate chain file',
             SiteConfig.ValidateOptionalPath(self.args.ansible_path),
             None,
             lambda config: config.get(
                'securedrop_app_https_on_source_interface')),
            ('securedrop_app_gpg_fingerprint', '', str,
             'Full fingerprint for the SecureDrop Application GPG Key',
             SiteConfig.ValidateFingerprint(),
             self.sanitize_fingerprint,
             lambda config: True),
            ('ossec_alert_gpg_public_key', 'ossec.pub', str,
             'Local filepath to OSSEC alerts GPG public key',
             SiteConfig.ValidatePath(self.args.ansible_path),
             None,
             lambda config: True),
            ('ossec_gpg_fpr', '', str,
             'Full fingerprint for the OSSEC alerts GPG public key',
             SiteConfig.ValidateFingerprint(),
             self.sanitize_fingerprint,
             lambda config: True),
            ('ossec_alert_email', '', str,
             'Admin email address for receiving OSSEC alerts',
             SiteConfig.ValidateOSSECEmail(),
             None,
             lambda config: True),
            ('journalist_alert_gpg_public_key', '', str,
             'Local filepath to journalist alerts GPG public key (optional)',
             SiteConfig.ValidateOptionalPath(self.args.ansible_path),
             None,
             lambda config: True),
            ('journalist_gpg_fpr', '', str,
             'Full fingerprint for the journalist alerts ' +
             'GPG public key (optional)',
             SiteConfig.ValidateOptionalFingerprint(),
             self.sanitize_fingerprint,
             lambda config: config.get('journalist_alert_gpg_public_key')),
            ('journalist_alert_email', '', str,
             'Email address for receiving journalist alerts (optional)',
             SiteConfig.ValidateOptionalEmail(),
             None,
             lambda config: config.get('journalist_alert_gpg_public_key')),
            ('smtp_relay', "smtp.gmail.com", str,
             'SMTP relay for sending OSSEC alerts',
             SiteConfig.ValidateNotEmpty(),
             None,
             lambda config: True),
            ('smtp_relay_port', 587, int,
             'SMTP port for sending OSSEC alerts',
             SiteConfig.ValidateInt(),
             int,
             lambda config: True),
            ('sasl_domain', "gmail.com", str,
             'SASL domain for sending OSSEC alerts',
             None,
             None,
             lambda config: True),
            ('sasl_username', '', str,
             'SASL username for sending OSSEC alerts',
             SiteConfig.ValidateOSSECUsername(),
             None,
             lambda config: True),
            ('sasl_password', '', str,
             'SASL password for sending OSSEC alerts',
             SiteConfig.ValidateOSSECPassword(),
             None,
             lambda config: True),
            ('enable_ssh_over_tor', True, bool,
             'Enable SSH over Tor (recommended, disables SSH over LAN). ' +
             'If you respond no, SSH will be available over LAN only',
             SiteConfig.ValidateYesNo(),
             lambda x: x.lower() == 'yes',
             lambda config: True),
            ('securedrop_supported_locales', [], list,
             'Space separated list of additional locales to support '
             '(' + translations_as_str + ')',
             SiteConfig.ValidateLocales(self.args.app_path),
             str.split,
             lambda config: True),
        ]  # type: List[_DescEntryType]

    def load_and_update_config(self, validate: bool = True, prompt: bool = True) -> bool:
        if self.exists():
            self.config = self.load(validate)
        elif not prompt:
            sdlog.error('Please run "securedrop-admin sdconfig" first.')
            sys.exit(1)

        return self.update_config(prompt)

    def update_config(self, prompt: bool = True) -> bool:
        if prompt:
            self.config.update(self.user_prompt_config())
        self.save()
        self.validate_gpg_keys()
        self.validate_journalist_alert_email()
        return True

    def user_prompt_config(self) -> Dict[str, Any]:
        self._config_in_progress = {}
        for desc in self.desc:
            (var, default, type, prompt, validator, transform,
                condition) = desc
            if not condition(self._config_in_progress):
                self._config_in_progress[var] = ''
                continue
            self._config_in_progress[var] = self.user_prompt_config_one(desc,
                                                                        self.config.get(var))  # noqa: E501
        return self._config_in_progress

    def user_prompt_config_one(
        self, desc: _DescEntryType, from_config: Optional[Any]
    ) -> Any:
        (var, default, type, prompt, validator, transform, condition) = desc
        if from_config is not None:
            default = from_config
        prompt += ': '

        # The following is for the dynamic check of the user input
        # for the previous question, as we are calling the default value
        # function dynamically, we can get the right value based on the
        # previous user input.
        if callable(default):
            default = default()
        return self.validated_input(prompt, default, validator, transform)

    def validated_input(
        self, prompt: str, default: Any, validator: Validator, transform: Optional[Callable]
    ) -> Any:
        if type(default) is bool:
            default = default and 'yes' or 'no'
        if type(default) is int:
            default = str(default)
        if isinstance(default, list):
            default = " ".join(default)
        if type(default) is not str:
            default = str(default)
        value = prompt_toolkit.prompt(prompt,
                                      default=default,
                                      validator=validator)
        if transform:
            return transform(value)
        else:
            return value

    def sanitize_fingerprint(self, value: str) -> str:
        return value.upper().replace(' ', '')

    def validate_gpg_keys(self) -> bool:
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

    def validate_journalist_alert_email(self) -> bool:
        if (self.config['journalist_alert_gpg_public_key'] == '' and
                self.config['journalist_gpg_fpr'] == ''):
            return True

        class Document:
            def __init__(self, text: str) -> None:
                self.text = text

        try:
            SiteConfig.ValidateEmail().validate(Document(
                self.config['journalist_alert_email']))
        except ValidationError as e:
            raise JournalistAlertEmailException(
                "journalist alerts email: " + e.message)
        return True

    def exists(self) -> bool:
        return os.path.exists(self.args.site_config)

    def save(self) -> None:
        with io.open(self.args.site_config, 'w') as site_config_file:
            yaml.safe_dump(self.config,
                           site_config_file,
                           default_flow_style=False)

    def clean_config(self, config: Dict) -> Dict:
        """
        Cleans a loaded config without prompting.

        For every variable defined in self.desc, validate its value in
        the supplied configuration dictionary, run the value through
        its defined transformer, and add the result to a clean version
        of the configuration.

        If no configuration variable triggers a ValidationError, the
        clean configuration will be returned.
        """
        clean_config = {}
        clean_config.update(config)
        for desc in self.desc:
            var, default, vartype, prompt, validator, transform, condition = desc
            if var in clean_config:
                value = clean_config[var]
                if isinstance(value, list):
                    text = " ".join(str(v) for v in value)
                elif isinstance(value, bool):
                    text = "yes" if value else "no"
                else:
                    text = str(value)

                if validator is not None:
                    try:
                        validator.validate(Document(text))
                    except ValidationError as e:
                        sdlog.error(e)
                        sdlog.error(
                            'Error loading configuration. '
                            'Please run "securedrop-admin sdconfig" again.'
                        )
                        raise
                clean_config[var] = transform(text) if transform else text
                if var not in self._config_in_progress:
                    self._config_in_progress[var] = clean_config[var]
        return clean_config

    def load(self, validate: bool = True) -> Dict:
        """
        Loads the site configuration file.

        If validate is True, then each configuration variable that has
        an entry in self.desc is validated and transformed according
        to current specifications.
        """
        try:
            with io.open(self.args.site_config) as site_config_file:
                c = yaml.safe_load(site_config_file)
                return self.clean_config(c) if validate else c
        except IOError:
            sdlog.error("Config file missing, re-run with sdconfig")
            raise
        except yaml.YAMLError:
            sdlog.error("There was an issue processing {}".format(
                self.args.site_config))
            raise


def setup_logger(verbose: bool = False) -> None:
    """ Configure logging handler """
    # Set default level on parent
    sdlog.setLevel(logging.DEBUG)
    level = logging.DEBUG if verbose else logging.INFO

    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    stdout.setLevel(level)
    sdlog.addHandler(stdout)


def update_check_required(cmd_name: str) -> Callable[[_FuncT], _FuncT]:
    """
    This decorator can be added to any subcommand that is part of securedrop-admin
    via `@update_check_required("name_of_subcommand")`. It forces a check for
    updates, and aborts if the locally installed code is out of date. It should
    be generally added to all subcommands that make modifications on the
    server or on the Admin Workstation.

    The user can override this check by specifying the --force argument before
    any subcommand.
    """
    def decorator_update_check(func: _FuncT) -> _FuncT:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cli_args = args[0]
            if cli_args.force:
                sdlog.info("Skipping update check because --force argument was provided.")
                return func(*args, **kwargs)

            update_status, latest_tag = check_for_updates(cli_args)
            if update_status is True:

                # Useful for troubleshooting
                branch_status = get_git_branch(cli_args)

                sdlog.error("You are not running the most recent signed SecureDrop release "
                            "on this workstation.")
                sdlog.error("Latest available version: {}".format(latest_tag))

                if branch_status is not None:
                    sdlog.error("Current branch status: {}".format(branch_status))
                else:
                    sdlog.error("Problem determining current branch status.")

                sdlog.error("Running outdated or mismatched code can cause significant "
                            "technical issues.")
                sdlog.error("To display more information about your repository state, run:\n\n\t"
                            "git status\n")
                sdlog.error("If you are certain you want to proceed, run:\n\n\t"
                            "./securedrop-admin --force {}\n".format(cmd_name))
                sdlog.error("To apply the latest updates, run:\n\n\t"
                            "./securedrop-admin update\n")
                sdlog.error("If this fails, see the latest upgrade guide on "
                            "https://docs.securedrop.org/ for instructions.")
                sys.exit(1)
            return func(*args, **kwargs)
        return cast(_FuncT, wrapper)
    return decorator_update_check


@update_check_required("sdconfig")
def sdconfig(args: argparse.Namespace) -> int:
    """Configure SD site settings"""
    SiteConfig(args).load_and_update_config(validate=False)
    return 0


def generate_new_v3_keys() -> Tuple[str, str]:
    """This function generate new keys for Tor v3 onion
    services and returns them as as tuple.

    :returns: Tuple(public_key, private_key)
    """

    private_key = x25519.X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw	,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption())
    public_key = private_key.public_key()
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw)

    # Base32 encode and remove base32 padding characters (`=`)
    public = base64.b32encode(public_bytes).replace(b'=', b'').decode("utf-8")
    private = base64.b32encode(private_bytes).replace(b'=', b'').decode("utf-8")
    return public, private


def find_or_generate_new_torv3_keys(args: argparse.Namespace) -> int:
    """
    This method will either read v3 Tor onion service keys if found or generate
    a new public/private keypair.
    """
    secret_key_path = os.path.join(args.ansible_path,
                                   "tor_v3_keys.json")
    if os.path.exists(secret_key_path):
        print('Tor v3 onion service keys already exist in: {}'.format(
            secret_key_path))
        return 0
    # No old keys, generate and store them first
    app_journalist_public_key, \
        app_journalist_private_key = generate_new_v3_keys()
    # For app SSH service
    app_ssh_public_key, app_ssh_private_key = generate_new_v3_keys()
    # For mon SSH service
    mon_ssh_public_key, mon_ssh_private_key = generate_new_v3_keys()
    tor_v3_service_info = {
            "app_journalist_public_key": app_journalist_public_key,
            "app_journalist_private_key": app_journalist_private_key,
            "app_ssh_public_key": app_ssh_public_key,
            "app_ssh_private_key": app_ssh_private_key,
            "mon_ssh_public_key": mon_ssh_public_key,
            "mon_ssh_private_key": mon_ssh_private_key,
    }
    with open(secret_key_path, 'w') as fobj:
        json.dump(tor_v3_service_info, fobj, indent=4)
    print('Tor v3 onion service keys generated and stored in: {}'.format(
        secret_key_path))
    return 0


@update_check_required("install")
def install_securedrop(args: argparse.Namespace) -> int:
    """Install/Update SecureDrop"""

    SiteConfig(args).load_and_update_config(prompt=False)

    sdlog.info("Now installing SecureDrop on remote servers.")
    sdlog.info("You will be prompted for the sudo password on the "
               "servers.")
    sdlog.info("The sudo password is only necessary during initial "
               "installation.")
    return subprocess.check_call(
        [os.path.join(args.ansible_path, 'securedrop-prod.yml'), '--ask-become-pass'],
        cwd=args.ansible_path
    )


def verify_install(args: argparse.Namespace) -> int:
    """Run configuration tests against SecureDrop servers"""

    sdlog.info("Running configuration tests: ")
    testinfra_cmd = ["./devops/scripts/run_prod_testinfra"]
    return subprocess.check_call(testinfra_cmd,
                                 cwd=os.getcwd())


@update_check_required("backup")
def backup_securedrop(args: argparse.Namespace) -> int:
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


@update_check_required("restore")
def restore_securedrop(args: argparse.Namespace) -> int:
    """Perform restore of the SecureDrop Application Server.
    Requires a tarball of submissions and server config, created via
    the `backup` action."""
    sdlog.info("Restoring the SecureDrop Application Server from backup")
    # Canonicalize filepath to backup tarball, so Ansible sees only the
    # basename. The files must live in args.ansible_path,
    # but the securedrop-admin
    # script will be invoked from the repo root, so preceding dirs are likely.
    restore_file_basename = os.path.basename(args.restore_file)

    # Would like readable output if there's a problem
    os.environ["ANSIBLE_STDOUT_CALLBACK"] = "debug"

    ansible_cmd = [
        'ansible-playbook',
        os.path.join(args.ansible_path, 'securedrop-restore.yml'),
        '-e',
    ]

    ansible_cmd_extras = [
        "restore_file='{}'".format(restore_file_basename),
    ]

    if args.restore_skip_tor:
        ansible_cmd_extras.append("restore_skip_tor='True'")

    if args.restore_manual_transfer:
        ansible_cmd_extras.append("restore_manual_transfer='True'")

    ansible_cmd.append(' '.join(ansible_cmd_extras))
    return subprocess.check_call(ansible_cmd, cwd=args.ansible_path)


@update_check_required("tailsconfig")
def run_tails_config(args: argparse.Namespace) -> int:
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


def check_for_updates_wrapper(args: argparse.Namespace) -> int:
    check_for_updates(args)
    # Because the command worked properly exit with 0.
    return 0


def check_for_updates(args: argparse.Namespace) -> Tuple[bool, str]:
    """Check for SecureDrop updates"""
    sdlog.info("Checking for SecureDrop updates...")

    # Determine what tag we are likely to be on. Caveat: git describe
    # may produce very surprising results, because it will locate the most recent
    # _reachable_ tag. However, in our current branching model, it can be
    # relied on to determine if we're on the latest tag or not.
    current_tag = subprocess.check_output(['git', 'describe'],
                                          cwd=args.root).decode('utf-8').rstrip('\n')  # noqa: E501

    # Fetch all branches
    git_fetch_cmd = ['git', 'fetch', '--all']
    subprocess.check_call(git_fetch_cmd, cwd=args.root)

    # Get latest tag
    git_all_tags = ["git", "tag"]
    all_tags = subprocess.check_output(git_all_tags,
                                       cwd=args.root).decode('utf-8').rstrip('\n').split('\n')  # noqa: E501

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


def get_git_branch(args: argparse.Namespace) -> Optional[str]:
    """
    Returns the starred line of `git branch` output.
    """
    git_branch_raw = subprocess.check_output(['git', 'branch'],
                                             cwd=args.root).decode('utf-8')
    match = re.search(r"\* (.*)\n", git_branch_raw)
    if match is not None and len(match.groups()) > 0:
        return match.group(1)
    else:
        return None


def get_release_key_from_keyserver(
    args: argparse.Namespace, keyserver: Optional[str] = None, timeout: int = 45
) -> None:
    gpg_recv = ['timeout', str(timeout), 'gpg', '--batch', '--no-tty',
                '--recv-key']
    for release_key in RELEASE_KEYS:
        # We construct the gpg --recv-key command based on optional keyserver arg.
        if keyserver:
            get_key_cmd = gpg_recv + ['--keyserver', keyserver] + [release_key]
        else:
            get_key_cmd = gpg_recv + [release_key]

        subprocess.check_call(get_key_cmd, cwd=args.root)


def update(args: argparse.Namespace) -> int:
    """Verify, and apply latest SecureDrop workstation update"""
    sdlog.info("Applying SecureDrop updates...")

    update_status, latest_tag = check_for_updates(args)

    if not update_status:
        # Exit if we're up to date
        return 0

    sdlog.info("Verifying signature on latest update...")

    # Retrieve key from openpgp.org keyserver
    get_release_key_from_keyserver(args,
                                   keyserver=DEFAULT_KEYSERVER)

    git_verify_tag_cmd = ['git', 'tag', '-v', latest_tag]
    try:
        sig_result = subprocess.check_output(git_verify_tag_cmd,
                                             stderr=subprocess.STDOUT,
                                             cwd=args.root).decode('utf-8')

        good_sig_text = ['Good signature from "SecureDrop Release Signing ' +
                         'Key"',
                         'Good signature from "SecureDrop Release Signing ' +
                         'Key <securedrop-release-key@freedom.press>"',
                         'Good signature from "SecureDrop Release Signing ' +
                         'Key <securedrop-release-key-2021@freedom.press>"']
        bad_sig_text = 'BAD signature'
        gpg_lines = sig_result.split('\n')

        # Check if any strings in good_sig_text match against gpg_lines[]
        good_sig_matches = [s for s in gpg_lines if
                            any(xs in s for xs in good_sig_text)]

        # To ensure that an adversary cannot name a malicious key good_sig_text
        # we check that bad_sig_text does not appear, that the release key
        # appears on the second line of the output, and that there is a single
        # match from good_sig_text[]
        if (RELEASE_KEYS[0] in gpg_lines[1] or RELEASE_KEYS[1] in gpg_lines[1]) and \
                len(good_sig_matches) == 1 and \
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
            except subprocess.CalledProcessError as e:
                if 'not a valid ref' in e.output.decode('utf-8'):
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


@update_check_required("logs")
def get_logs(args: argparse.Namespace) -> int:
    """Get logs for forensics and debugging purposes"""
    sdlog.info("Gathering logs for forensics and debugging")
    ansible_cmd = [
        'ansible-playbook',
        os.path.join(args.ansible_path, 'securedrop-logs.yml'),
    ]
    subprocess.check_call(ansible_cmd, cwd=args.ansible_path)
    sdlog.info("Please send the encrypted logs to securedrop@freedom.press or "
               "upload them to the SecureDrop support portal: " + SUPPORT_URL)
    return 0


def set_default_paths(args: argparse.Namespace) -> argparse.Namespace:
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


@update_check_required("reset_admin_access")
def reset_admin_access(args: argparse.Namespace) -> int:
    """Resets SSH access to the SecureDrop servers, locking it to
    this Admin Workstation."""
    sdlog.info("Resetting SSH access to the SecureDrop servers")
    ansible_cmd = [
        'ansible-playbook',
        os.path.join(args.ansible_path, 'securedrop-reset-ssh-key.yml'),
    ]
    return subprocess.check_call(ansible_cmd, cwd=args.ansible_path)


def parse_argv(argv: List[str]) -> argparse.Namespace:
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
    parser.add_argument('--force', action='store_true', required=False,
                        help="force command execution without update check")
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

    parse_generate_tor_keys = subparsers.add_parser(
        'generate_v3_keys',
        help=find_or_generate_new_torv3_keys.__doc__)
    parse_generate_tor_keys.set_defaults(func=find_or_generate_new_torv3_keys)

    parse_backup = subparsers.add_parser('backup',
                                         help=backup_securedrop.__doc__)
    parse_backup.set_defaults(func=backup_securedrop)

    parse_restore = subparsers.add_parser('restore',
                                          help=restore_securedrop.__doc__)
    parse_restore.set_defaults(func=restore_securedrop)
    parse_restore.add_argument("restore_file")
    parse_restore.add_argument("--preserve-tor-config", default=False,
                               action='store_true',
                               dest='restore_skip_tor',
                               help="Preserve the server's current Tor config")

    parse_restore.add_argument("--no-transfer", default=False,
                               action='store_true',
                               dest='restore_manual_transfer',
                               help="Restore using a backup file already present on the server")

    parse_update = subparsers.add_parser('update', help=update.__doc__)
    parse_update.set_defaults(func=update)

    parse_check_updates = subparsers.add_parser('check_for_updates',
                                                help=check_for_updates.__doc__)
    parse_check_updates.set_defaults(func=check_for_updates_wrapper)

    parse_logs = subparsers.add_parser('logs',
                                       help=get_logs.__doc__)
    parse_logs.set_defaults(func=get_logs)

    parse_reset_ssh = subparsers.add_parser('reset_admin_access',
                                            help=reset_admin_access.__doc__)
    parse_reset_ssh.set_defaults(func=reset_admin_access)

    parse_verify = subparsers.add_parser('verify',
                                         help=verify_install.__doc__)
    parse_verify.set_defaults(func=verify_install)

    args = parser.parse_args(argv)
    if getattr(args, 'func', None) is None:
        print('Please specify an operation.\n')
        parser.print_help()
        sys.exit(1)
    return set_default_paths(args)


def main(argv: List[str]) -> None:
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
