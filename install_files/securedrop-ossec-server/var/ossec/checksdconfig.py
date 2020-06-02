#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import sys


IPTABLES_RULES_UNCONFIGURED = {
    "all": ["-P INPUT ACCEPT", "-P FORWARD ACCEPT", "-P OUTPUT ACCEPT"]
}


IPTABLES_RULES_DEFAULT_DROP = {
    "policies": [
        "-P INPUT DROP",
        "-P FORWARD DROP",
        "-P OUTPUT DROP",
    ],
    "input": [
        '-A INPUT -m comment --comment "Drop and log all other incoming traffic" -j LOGNDROP',
    ],
    "output": [
        '-A OUTPUT -m comment --comment "Drop all other outgoing traffic" -j DROP',
    ],
    "logndrop": [
        (
            "-A LOGNDROP -p tcp -m limit --limit 5/min -j LOG --log-tcp-options --log-ip-options "
            "--log-uid"
        ),
        "-A LOGNDROP -p udp -m limit --limit 5/min -j LOG --log-ip-options --log-uid",
        "-A LOGNDROP -p icmp -m limit --limit 5/min -j LOG --log-ip-options --log-uid",
        "-A LOGNDROP -j DROP",
    ]
}


def list_iptables_rules():
    result = subprocess.run(
        ["iptables", "-S"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    rules = result.stdout.decode("utf-8").splitlines()
    policies = [r for r in rules if r.startswith("-P")]
    input_rules = [r for r in rules if r.startswith("-A INPUT")]
    output_rules = [r for r in rules if r.startswith("-A OUTPUT")]
    logndrop_rules = [r for r in rules if r.startswith("-A LOGNDROP")]
    return {
        "all": rules,
        "policies": policies,
        "input": input_rules,
        "output": output_rules,
        "logndrop": logndrop_rules,
    }


def check_iptables_are_default(rules):
    if rules["all"] == IPTABLES_RULES_UNCONFIGURED:
        raise ValueError("The iptables rules have not been configured.")


def check_iptables_default_drop(rules):
    for chain, chain_rules in IPTABLES_RULES_DEFAULT_DROP.items():
        for i, rule in enumerate(reversed(chain_rules), 1):
            try:
                if rules[chain][-i] != rule:
                    raise ValueError("The iptables default drop rules are incorrect.")
            except (KeyError, IndexError):
                raise ValueError("The iptables default drop rules are incorrect.")


def check_iptables_rules():
    rules = list_iptables_rules()
    check_iptables_are_default(rules)
    check_iptables_default_drop(rules)


def check_system_configuration(args):
    print("Checking system configuration...")
    try:
        check_iptables_rules()
    except ValueError as e:
        print("System configuration error:", e)
        sys.exit(1)
    print("System configuration checks were successful.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SecureDrop server configuration check')
    args = parser.parse_args()
    check_system_configuration(args)
