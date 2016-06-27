#!/usr/bin/env python
# -*- coding: utf-8 -*-


import config_tool
import json
import tempfile
import unittest


class TestConifgTool(unittest.TestCase):

    def test_misc(self):
        d = {'foo': {'bar': {'baz': 'quux'}}}

        assert config_tool.deep_get(['foo', 'bar', 'baz'], d) == 'quux'
        assert config_tool.deep_get(['foo', 'bar', 'wat'], d) is None
        assert config_tool.deep_get(['wat'], d) is None

        assert config_tool.check_gpg_public_key_fingerprint('0CEC936888A60171461174C5C0A2586F09D77C82')
        assert not config_tool.check_gpg_public_key_fingerprint('0cEC936888A60171461174C5C0A2586F09D77C82')
        assert not config_tool.check_gpg_public_key_fingerprint('0CEC936888A60171461174C5C0A2586F09D77C82 ')

        assert config_tool.check_ip_address_valid('1.2.3.4')
        assert not config_tool.check_ip_address_valid('1.2.3.400')
        assert not config_tool.check_ip_address_valid('1.2.3')

    def test_validate_config(self):
        conf = {
            'app': {
                'ip_address': '1.2.3.4',
                'hostname': 'app',
                'secure_drop': {
                    'header_image': '',
                    'gpg_public_key': '-----BEGIN PGP PUBLIC KEY BLOCK-----\nblahblahblah\n-----END PGP PUBLIC KEY BLOCK-----',
                    'gpg_public_key_fingerprint': '0CEC936888A60171461174C5C0A2586F09D77C82',
                }
            },
            'mon': {
                'ip_address': '1.2.3.5',
                'hostname': 'mon',
                'ossec': {
                    'gpg_public_key': '-----BEGIN PGP PUBLIC KEY BLOCK-----\nblahblahblah\n-----END PGP PUBLIC KEY BLOCK-----',
                    'gpg_public_key_fingerprint': '0CEC936888A60171461174C5C0A2586F09D77C82',
                    'email_address': 'foo@bar.baz',
                    'smtp': {
                        'relay': 'foo.bar',
                        'port': 502,
                        'sasl': {
                            'username': 'steve',
                            'password': 'urkel',
                            'domain': 'nerd-stuff',
                        }
                    }
                }
            },
            'provisioning': {
                'ssh_users': [
                    'snowden',
                    'ellsberg',
                ],
                'dns_servers': [
                    '8.8.8.8',
                    '8.8.4.4',
                ]
            }
        }

        output_file = tempfile.NamedTemporaryFile()
        input_file = tempfile.NamedTemporaryFile()

        with open(input_file.name, 'w') as f:
            f.write(json.dumps(conf))

        args = config_tool.get_arg_parser().parse_args([
            '-o', output_file.name,
            'load-conf', '-i', input_file.name,
        ])

        config_tool.load_conf(args)

    def test_validate_bad_config(self):
        conf = {'foo': 'bar'}

        output_file = tempfile.NamedTemporaryFile()
        input_file = tempfile.NamedTemporaryFile()

        with open(input_file.name, 'w') as f:
            f.write(json.dumps(conf))

        args = config_tool.get_arg_parser().parse_args([
            '-o', output_file.name,
            'load-conf', '-i', input_file.name,
        ])

        self.assertRaises(config_tool.ConfigToolException, lambda: config_tool.load_conf(args))
