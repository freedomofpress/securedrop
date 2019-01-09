#!/usr/bin/env python

from __future__ import print_function

import fcntl
import json
import os
import sys

from argparse import ArgumentParser
from base64 import b64encode
from contextlib import contextmanager
from os import path

LOCK_FILE = '/var/lib/securedrop/securedrop-config-migrate.lock'
CONFIG_DIR = '/etc/securedrop'


@contextmanager
def acquire_lock():
    lock = open(LOCK_FILE, 'w')
    try:
        # an exclusive, non-blocking file lock
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, IOError):
        print('Failed to acquire lock.')
        sys.exit(1)
    else:
        yield
    finally:
        # unlock it (to make testing easier)
        fcntl.flock(lock, fcntl.LOCK_UN)


def main():
    # Acquire an exclusive lock because clobbering the config file would be
    # very bad
    args = arg_parser().parse_args()
    with acquire_lock():
        migrate_and_populate_configs(args.journalist_key_fpr,
                                     args.default_locale,
                                     args.supported_locales)


def import_config():
    '''Helper function to make mocking in tests easier.'''
    import config  # noqa
    return config


def migrate_and_populate_configs(journalist_key_fpr,
                                 default_locale,
                                 supported_locales,
                                 config_dir=CONFIG_DIR):
    source_config_file = path.join(config_dir, 'source-config.json')
    journalist_config_file = path.join(config_dir, 'journalist-config.json')

    # Read the destination configs in case they have been created with partial
    # values
    journalist_config = try_read_config(journalist_config_file)
    source_config = try_read_config(source_config_file)

    # Attempt to import `config.py` (legacy configuration)
    try:
        config = import_config()
        print('Python config imported.')
    except ImportError:
        # If the module does not exist (newer releases), we set the config to
        # `None` and then catch all the `AttributeError`s
        config = None
        print('Python config unable to be imported.')

    # Next collect the attributes using the following priority:
    #   1. CLI args
    #   2. `config.py`
    #   3. `journalist-config.json`
    #   4. `source-config.json`
    #   5. newly generated values

    try:
        id_pepper = config.SCRYPT_ID_PEPPER
        if not id_pepper:
            raise ValueError
    except (AttributeError, ValueError):
        id_pepper = (journalist_config.get('scrypt_id_pepper', None) or
                     source_config.get('scrypt_id_pepper', None) or
                     random_b64(32))

    try:
        gpg_pepper = config.SCRYPT_GPG_PEPPER
        if not gpg_pepper:
            raise ValueError
    except (AttributeError, ValueError):
        gpg_pepper = (journalist_config.get('scrypt_gpg_pepper', None) or
                      source_config.get('scrypt_gpg_pepper', None) or
                      random_b64(32))

    if not default_locale:
        try:
            default_locale = config.DEFAULT_LOCALE
        except AttributeError:
            default_locale = None
    default_locale = (
        default_locale or
        journalist_config.get('i18n', {}).get('default_locale', None) or
        source_config.get('i18n', {}).get('default_locale', None))

    if not supported_locales:
        try:
            supported_locales = config.SUPPORTED_LOCALES
        except AttributeError:
            supported_locales = None
    supported_locales = (
        supported_locales or
        journalist_config.get('i18n', {}).get('default_locale', None) or
        source_config.get('i18n', {}).get('default_locale', None))

    if default_locale and supported_locales:
        i18n = {}
        if default_locale:
            i18n['default_locale'] = default_locale
        if supported_locales:
            i18n['supported_locales'] = supported_locales
    else:
        i18n = None

    try:
        scrypt_params = config.SCRYPT_PARAMS
    except AttributeError:
        scrypt_params = (
            journalist_config.get('scrypt_params', None) or
            source_config.get('scrypt_params', None) or
            None  # adding none to prevent empty `dict` case
        )

    if not journalist_key_fpr:
        try:
            journalist_key_fpr = config.JOURNALIST_KEY
        except AttributeError:
            journalist_key_fpr = None

    try:
        source_key = config.SourceInterfaceFlaskConfig.SECRET_KEY
    except AttributeError:
        source_key = source_config.get('secret_key', None)
    if not source_key:
        source_key = random_b64(32)

    try:
        journalist_key = config.JournalistInterfaceFlaskConfig.SECRET_KEY
    except AttributeError:
        journalist_key = journalist_config.get('secret_key', None)
    if not journalist_key:
        journalist_key = random_b64(32)

    try:
        custom_header_image = config.CUSTOM_HEADER_IMAGE
    except AttributeError:
        custom_header_image = None
    if not custom_header_image:
        custom_header_image = (
            journalist_config.get('custom_header_image', None) or
            source_config.get('custom_header_image', None)
        )

    # Then we assemble them into a configs.
    # We allow a partial configs to be assembled in case of a partial
    # configuration of SecureDrop. Ansible will fill in the rest.

    journalist_config['journalist_key'] = journalist_key_fpr
    source_config['journalist_key'] = journalist_key_fpr

    journalist_config['scrypt_id_pepper'] = id_pepper
    source_config['scrypt_id_pepper'] = id_pepper

    journalist_config['scrypt_gpg_pepper'] = gpg_pepper
    source_config['scrypt_gpg_pepper'] = gpg_pepper

    if i18n:
        journalist_config['i18n'] = i18n
        source_config['i18n'] = i18n

    if scrypt_params:
        journalist_config['scrypt_params'] = scrypt_params
        source_config['scrypt_params'] = scrypt_params

    journalist_config['secret_key'] = journalist_key
    source_config['secret_key'] = source_key

    if custom_header_image is not None:
        journalist_config['custom_header_image'] = custom_header_image
        source_config['custom_header_image'] = custom_header_image

    safe_write_file(journalist_config, journalist_config_file)
    safe_write_file(source_config, source_config_file)


def safe_write_file(data, dest_file):
    temp_file = dest_file + '.tmp'

    if not path.exists(temp_file):
        # ensure file exists
        open(temp_file, 'w').close()
        # set safe permissions on it before we write secret values
        os.chmod(temp_file, 0o640)

    # Use a temp file to not clobber original in the event of an IO error
    with open(temp_file, 'w') as f:
        f.write(json.dumps(data, indent=2, sort_keys=True))

    os.rename(temp_file, dest_file)


def try_read_config(config_path):
    try:
        with open(config_path) as f:
            out = json.loads(f.read())
            print('Config file read: {}'.format(config_path))
            return out
    except IOError as e:
        if e.errno == 2:  # file not found
            print('Config file did not exist: {}'.format(config_path))
            return {}
        raise
    except ValueError:
        # if we can't parse, we assume this is a partial write
        print('Config file unparseable: {}'.format(config_path))
        return {}


def random_b64(byte_count):
    with open('/dev/urandom') as f:
        return b64encode(f.read(byte_count))


def comma_separated_list(arg):
    return [x.strip() for x in arg.split(',') if x.strip()]


def arg_parser():
    parser = ArgumentParser(
        path.basename(__file__),
        description='Helper for migrating config from Python to JSON')
    parser.add_argument('--journalist-key-fpr',
                        help='The PGP fingerprint of the journalist key')
    parser.add_argument('--default-locale',
                        help='The default locale',
                        default=None)
    parser.add_argument('--supported-locales', type=comma_separated_list,
                        default=None,
                        help='Comma separated list of locales')
    return parser


if __name__ == '__main__':
    main()
