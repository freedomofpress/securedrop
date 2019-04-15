# -*- encoding:utf-8 -*-
from __future__ import absolute_import, division, print_function, \
        unicode_literals

import sys

import ansible

try:
    # Version 2.0+
    from ansible.plugins.callback import CallbackBase
except ImportError:
    CallbackBase = object


def print_red_bold(text):
    print('\x1b[31;1m' + text + '\x1b[0m')


class CallbackModule(CallbackBase):
    def __init__(self):
        # Can't use `on_X` because this isn't forwards compatible
        # with Ansible 2.0+
        required_version = '2.6.14'  # Keep synchronized with requirements files
        if not ansible.__version__.startswith(required_version):
            print_red_bold(
                "SecureDrop restriction: only Ansible {version}.*"
                "is supported."
                .format(version=required_version)
            )
            sys.exit(1)
