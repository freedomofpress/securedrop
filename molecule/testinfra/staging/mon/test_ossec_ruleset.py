import pytest
import re

testinfra_hosts = ["mon-staging"]
alert_level_regex = re.compile(r"Level: '(\d+)'")
rule_id_regex = re.compile(r"Rule id: '(\d+)'")
sdvars = pytest.securedrop_test_vars


@pytest.mark.parametrize('log_event',
                         sdvars.log_events_without_ossec_alerts)
def test_ossec_false_positives_suppressed(Command, Sudo, log_event):
    with Sudo():
        c = Command('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                log_event["alert"]))
        assert "Alert to be generated" not in c.stderr


@pytest.mark.parametrize('log_event',
                         sdvars.log_events_with_ossec_alerts)
def test_ossec_expected_alerts_are_present(Command, Sudo, log_event):
    with Sudo():
        c = Command('echo "{}" | /var/ossec/bin/ossec-logtest'.format(
                log_event["alert"]))
        assert "Alert to be generated" in c.stderr
        alert_level = alert_level_regex.findall(c.stderr)[0]
        assert alert_level == log_event["level"]
        rule_id = rule_id_regex.findall(c.stderr)[0]
        assert rule_id == log_event["rule_id"]
