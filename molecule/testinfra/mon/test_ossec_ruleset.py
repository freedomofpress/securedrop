import pytest
import re

import testutils

sdvars = testutils.securedrop_test_vars
testinfra_hosts = [sdvars.monitor_hostname]
alert_level_regex = re.compile(r"Level: '(\d+)'")
rule_id_regex = re.compile(r"Rule id: '(\d+)'")


@pytest.mark.parametrize('log_event',
                         sdvars.log_events_without_ossec_alerts)
def test_ossec_false_positives_suppressed(host, log_event):
    with host.sudo():
        c = host.run('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                     log_event["alert"]))
        assert "Alert to be generated" not in c.stderr


@pytest.mark.parametrize('log_event',
                         sdvars.log_events_with_ossec_alerts)
def test_ossec_expected_alerts_are_present(host, log_event):
    with host.sudo():
        c = host.run('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                     log_event["alert"]))
        assert "Alert to be generated" in c.stderr
        alert_level = alert_level_regex.findall(c.stderr)[0]
        assert alert_level == log_event["level"]
        rule_id = rule_id_regex.findall(c.stderr)[0]
        assert rule_id == log_event["rule_id"]
