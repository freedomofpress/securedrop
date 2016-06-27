#!/usr/bin/env python

import argparse
import logging
import re
import sys
import yaml

from os import path
from yaml.scanner import ScannerError


"""
A CLI tool to help admins configure their SecureDrop instances. Uses argparse, so run this file from
your terminal with --help to get instructions on how to use this.
"""


def init_logger():
    l = logging.getLogger(__file__)
    l.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    l.addHandler(ch)
    return l

log = init_logger()


class ConfigToolException(Exception):

    def __init__(self, msg=None):
        super(ConfigToolException, self).__init__(msg)


def check_ip_address_valid(ip):  # "good enough"
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    if bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups())):
        log.debug("'{ip}' was a valid ipv4 address".format(ip=ip))
        return True
    else:
        log.error("'{ip}' was not a valid ipv4 address".format(ip=ip))
        return False


def check_ssh_users(users):
    def check_user(user):
        regex = r'^[a-z][-a-z0-9]*$'
        if isinstance(user, str) and re.match(regex, user):
            log.debug("'{user}' was a valid Unix user name".format(user=user))
            return True
        else:
            log.debug("'{user}' was not valid Unix user name. Regex: {regex}".format(user=user, regex=regex))
            return False

    if isinstance(users, str):
        return check_user(users)
    elif isinstance(users, list):
        return all(map(check_user, users))
    else:
        log.error('SSH users need to be a string or list of strings')
        return False


def check_dns_servers(servers):
    if isinstance(servers, str):
        return check_ip_address_valid(servers)
    elif isinstance(servers, list):
        return all(map(check_ip_address_valid, servers))
    else:
        log.error('DNS servers need to be a string or list of strings')
        return False


def check_gpg_public_key(key_str):
    key_lines = key_str.splitlines()
    return len(key_lines) >= 2 and \
        key_lines[0] == '-----BEGIN PGP PUBLIC KEY BLOCK-----' in key_str and \
        (key_lines[-1] == '-----END PGP PUBLIC KEY BLOCK-----' or
         key_lines[-2] == '-----END PGP PUBLIC KEY BLOCK-----')


def check_gpg_public_key_fingerprint(fpr):
    return bool(re.match(r'^[0-9A-F]{40}$', fpr))


def check_email_address(addr):
    return '@' in addr


"""
This object represents what a valid config should look like and contains test functions to validate
the data in configs we generate.
"""
MASTER_CONFIG = {
    'app': {
        'ip_address': check_ip_address_valid,
        'hostname': lambda x: True,  # no hostname validation
        'secure_drop': {
            'header_image': lambda x: True if not x else path.exists(x),
            'gpg_public_key': check_gpg_public_key,
            'gpg_public_key_fingerprint': check_gpg_public_key_fingerprint,
        }
    },
    'mon': {
        'ip_address': check_ip_address_valid,
        'hostname': lambda x: True,  # no hostname validation
        'ossec': {
            'gpg_public_key': check_gpg_public_key,
            'gpg_public_key_fingerprint': check_gpg_public_key_fingerprint,
            'email_address': check_email_address,
            'smtp': {
                'relay': lambda x: isinstance(x, str) and bool(x),
                'port': lambda x: isinstance(x, int) and 0 < x < 65536,
                'sasl': {
                    'username': lambda x: isinstance(x, str) and bool(x),
                    'password': lambda x: isinstance(x, str) and bool(x),
                    'domain': lambda x: isinstance(x, str) and bool(x),
                }

            }
        }
    },
    'provisioning': {
        'ssh_users': check_ssh_users,
        'dns_servers': check_dns_servers
    },
}


def load_file(path):
    """
    Loads a config as YAML from a given path
    :param path: Path to the file to load
    :return: A dict if successful, raises an Exception otherwise
    """

    log.debug("Loading file from path '{path}'".format(path=path))
    f = None

    try:
        f = open(path, 'r')
        yml = yaml.safe_load(f)

        log.info("Successfully loaded file from path '{path}'".format(path=path))

        return yml
    except IOError as e:
        log.error("Cannot open file '{path}'".format(path=path))
        raise e
    except ScannerError as e:
        log.error("Failed to parse YAML for file '{path}'".format(path=path))
        raise e
    finally:
        if f is not None:
            f.close()


def finalize(path, conf):
    """
    Validates then writes the master config to a given path

    :param path: Path to write master config file
    :param conf: Config to write
    :return: None if successful, raises an Exception otherwise
    """

    log.debug('Validating master config file')

    if recurse_through_dict([], conf, is_success=True):
        log.debug('Successfully validated master config')
    else:
        log.error('Failed to validate master config file.')
        raise ConfigToolException()

    log.debug("Writing master config to path '{path}'".format(path=path))
    f = None

    try:
        f = open(path, 'w')
        f.write(yaml.safe_dump(conf))
    except IOError as e:
        log.error("Failed to write master config to path '{path}'".format(path=path))
        raise e
    finally:
        if f is not None:
            f.close()


def deep_get(breadcrumbs, d):
    """
    Helper function to extract deeply nested values from dicts
    :param breadcrumbs: A list of keys
    :param d: the dict to extract values from
    :return: the value at the desired key or None
    """

    for k in breadcrumbs:
        if d is not None:
            d = d.get(k)
    return d


def recurse_through_dict(breadcrumbs, conf, is_success):
    """
    Recursively walk through a dict and validate the keys against MASTER_CONFIG
    :param breadcrumbs: a list of keys traversed so far to reach the current dict (when starting, should be [])
    :param conf: the dict representing the config we want to test
    :param is_success: Whether or not the traversal so far has been successful (when starting, should be True)
    :return: True if the given key validated, False otherwise
    """

    # check keys at current step
    cur_dict_conf = deep_get(breadcrumbs, conf)
    cur_dict_master = deep_get(breadcrumbs, MASTER_CONFIG)

    if cur_dict_conf is None:
        is_success = False
    else:
        if cur_dict_master is not None:
            conf_diff_master = set(cur_dict_conf.keys()) - set(cur_dict_master.keys())

            if conf_diff_master:
                for k in conf_diff_master:
                    log.warn("Unnecessary key in master config: {bc}".format(bc=breadcrumbs + [k]))
                    del cur_dict_conf[k]

    # do the next step of the walk
    for key, v in cur_dict_master.items():
        if isinstance(v, dict):
            if cur_dict_conf is not None:
                is_success = recurse_through_dict(breadcrumbs + [key], conf, is_success)
        else:
            config_value = deep_get(breadcrumbs + [key], conf)

            if config_value is not None:
                v_res = v(config_value)

                if v_res is True:
                    log.info("Successful validation for key {bc}".format(bc=breadcrumbs + [key]))
                else:
                    log.error("Failed validation for key {bc}".format(bc=breadcrumbs + [key]))

                is_success = v_res and is_success
            else:
                log.error("Missing value in master config: {bc}".format(bc=breadcrumbs + [key]))
                is_success = False

    return is_success


def make_conf(args):
    conf = {}
    finalize(args.output_file, conf)


def load_conf(args):
    conf = {}

    for f in args.input_files:
        yml = load_file(f)
        conf.update(yml)

    finalize(args.output_file, conf)


def get_arg_parser():
    parser = argparse.ArgumentParser(prog=path.basename(__file__),
                                     description='A tool to help SecureDrop admins configure their installations')

    parser.add_argument('-o', '--output-file',
                        help='Path for the output for the master config file',
                        dest='output_file',
                        type=str,
                        default='/home/amnesia/Persistent/securedrop-master-config.yml')
    parser.add_argument('-v', '--verbose',
                        help='Enable verbose output (additive, repeat this arg for more verbose output)',
                        dest='verbosity',
                        action='count')

    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'subcommand'

    load_conf_subparser = subparsers.add_parser('load-conf',
                                                help='Load and validate and old master config files')
    load_conf_subparser.add_argument('-i', '--input-file',
                                     help="Path to the file to load (additive, repeat this arg for multiple files,"
                                          "configs are merged with a 'last config wins' strategy)",
                                     dest='input_files',
                                     type=str,
                                     action='append',
                                     required=True)
    load_conf_subparser.set_defaults(func=load_conf)

    return parser


if __name__ == '__main__':  # pragma: no cover
    try:
        args = get_arg_parser().parse_args()

        if args.verbosity == 0:
            log.setLevel(logging.WARN)
        elif args.verbosity == 1:
            log.setLevel(logging.INFO)
        elif args.verbosity >= 2:
            log.setLevel(logging.DEBUG)

        if hasattr(args, 'output_file'):
            if path.exists(args.output_file):
                log.error('Output file already exists. Cowardly refusing to overwrite.')
                raise ConfigToolException()

        args.func(args)
        log.info("Success")
        exit(0)
    except KeyboardInterrupt:
        log.error('Interrupt. Aborting.')
        exit(1)
    except ConfigToolException:
        log.error('Failure. Config could not be validated.')
        exit(1)
else:
    # enambe debug for tests
    log.setLevel(logging.DEBUG)
