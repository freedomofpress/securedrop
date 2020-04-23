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
        # The acceptable version range needs to be synchronized with
        # requirements files.
        viable_start = [2, 9, 7]
        viable_end = [2, 10, 0]
        ansible_version = [int(v) for v in ansible.__version__.split('.')]
        if not (viable_start <= ansible_version < viable_end):
            print_red_bold(
                "SecureDrop restriction: Ansible version must be at least {viable_start} "
                "and less than {viable_end}."
                .format(
                    viable_start='.'.join(str(v) for v in viable_start),
                    viable_end='.'.join(str(v) for v in viable_end),
                )
            )
            sys.exit(1)
