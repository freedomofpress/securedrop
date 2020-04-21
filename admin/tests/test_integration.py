from flaky import flaky
import os
import io
import pexpect
import pytest
import re
import requests
import subprocess
import tempfile

SD_DIR = ''
CURRENT_DIR = os.path.dirname(__file__)
ANSIBLE_BASE = ''
# Regex to strip ANSI escape chars
# https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
ANSI_ESCAPE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')


OUTPUT1 = '''app_hostname: app
app_ip: 10.20.2.2
daily_reboot_time: 5
dns_server: 8.8.8.8
enable_ssh_over_tor: true
journalist_alert_email: ''
journalist_alert_gpg_public_key: ''
journalist_gpg_fpr: ''
monitor_hostname: mon
monitor_ip: 10.20.3.2
ossec_alert_email: test@gmail.com
ossec_alert_gpg_public_key: sd_admin_test.pub
ossec_gpg_fpr: 1F544B31C845D698EB31F2FF364F1162D32E7E58
sasl_domain: gmail.com
sasl_password: testpassword
sasl_username: testuser
securedrop_app_gpg_fingerprint: 1F544B31C845D698EB31F2FF364F1162D32E7E58
securedrop_app_gpg_public_key: sd_admin_test.pub
securedrop_app_https_certificate_cert_src: ''
securedrop_app_https_certificate_chain_src: ''
securedrop_app_https_certificate_key_src: ''
securedrop_app_https_on_source_interface: false
securedrop_supported_locales:
- de_DE
- es_ES
smtp_relay: smtp.gmail.com
smtp_relay_port: 587
ssh_users: sd
v2_onion_services: false
v3_onion_services: true
'''

WHEN_BOTH_TRUE = '''app_hostname: app
app_ip: 10.20.2.2
daily_reboot_time: 5
dns_server: 8.8.8.8
enable_ssh_over_tor: true
journalist_alert_email: ''
journalist_alert_gpg_public_key: ''
journalist_gpg_fpr: ''
monitor_hostname: mon
monitor_ip: 10.20.3.2
ossec_alert_email: test@gmail.com
ossec_alert_gpg_public_key: sd_admin_test.pub
ossec_gpg_fpr: 1F544B31C845D698EB31F2FF364F1162D32E7E58
sasl_domain: gmail.com
sasl_password: testpassword
sasl_username: testuser
securedrop_app_gpg_fingerprint: 1F544B31C845D698EB31F2FF364F1162D32E7E58
securedrop_app_gpg_public_key: sd_admin_test.pub
securedrop_app_https_certificate_cert_src: ''
securedrop_app_https_certificate_chain_src: ''
securedrop_app_https_certificate_key_src: ''
securedrop_app_https_on_source_interface: false
securedrop_supported_locales:
- de_DE
- es_ES
smtp_relay: smtp.gmail.com
smtp_relay_port: 587
ssh_users: sd
v2_onion_services: true
v3_onion_services: true
'''

WHEN_ONLY_V2 = '''app_hostname: app
app_ip: 10.20.2.2
daily_reboot_time: 5
dns_server: 8.8.8.8
enable_ssh_over_tor: true
journalist_alert_email: ''
journalist_alert_gpg_public_key: ''
journalist_gpg_fpr: ''
monitor_hostname: mon
monitor_ip: 10.20.3.2
ossec_alert_email: test@gmail.com
ossec_alert_gpg_public_key: sd_admin_test.pub
ossec_gpg_fpr: 1F544B31C845D698EB31F2FF364F1162D32E7E58
sasl_domain: gmail.com
sasl_password: testpassword
sasl_username: testuser
securedrop_app_gpg_fingerprint: 1F544B31C845D698EB31F2FF364F1162D32E7E58
securedrop_app_gpg_public_key: sd_admin_test.pub
securedrop_app_https_certificate_cert_src: ''
securedrop_app_https_certificate_chain_src: ''
securedrop_app_https_certificate_key_src: ''
securedrop_app_https_on_source_interface: false
securedrop_supported_locales:
- de_DE
- es_ES
smtp_relay: smtp.gmail.com
smtp_relay_port: 587
ssh_users: sd
v2_onion_services: true
v3_onion_services: false
'''

JOURNALIST_ALERT_OUTPUT = '''app_hostname: app
app_ip: 10.20.2.2
daily_reboot_time: 5
dns_server: 8.8.8.8
enable_ssh_over_tor: true
journalist_alert_email: test@gmail.com
journalist_alert_gpg_public_key: sd_admin_test.pub
journalist_gpg_fpr: 1F544B31C845D698EB31F2FF364F1162D32E7E58
monitor_hostname: mon
monitor_ip: 10.20.3.2
ossec_alert_email: test@gmail.com
ossec_alert_gpg_public_key: sd_admin_test.pub
ossec_gpg_fpr: 1F544B31C845D698EB31F2FF364F1162D32E7E58
sasl_domain: gmail.com
sasl_password: testpassword
sasl_username: testuser
securedrop_app_gpg_fingerprint: 1F544B31C845D698EB31F2FF364F1162D32E7E58
securedrop_app_gpg_public_key: sd_admin_test.pub
securedrop_app_https_certificate_cert_src: ''
securedrop_app_https_certificate_chain_src: ''
securedrop_app_https_certificate_key_src: ''
securedrop_app_https_on_source_interface: false
securedrop_supported_locales:
- de_DE
- es_ES
smtp_relay: smtp.gmail.com
smtp_relay_port: 587
ssh_users: sd
v2_onion_services: false
v3_onion_services: true
'''

HTTPS_OUTPUT = '''app_hostname: app
app_ip: 10.20.2.2
daily_reboot_time: 5
dns_server: 8.8.8.8
enable_ssh_over_tor: true
journalist_alert_email: test@gmail.com
journalist_alert_gpg_public_key: sd_admin_test.pub
journalist_gpg_fpr: 1F544B31C845D698EB31F2FF364F1162D32E7E58
monitor_hostname: mon
monitor_ip: 10.20.3.2
ossec_alert_email: test@gmail.com
ossec_alert_gpg_public_key: sd_admin_test.pub
ossec_gpg_fpr: 1F544B31C845D698EB31F2FF364F1162D32E7E58
sasl_domain: gmail.com
sasl_password: testpassword
sasl_username: testuser
securedrop_app_gpg_fingerprint: 1F544B31C845D698EB31F2FF364F1162D32E7E58
securedrop_app_gpg_public_key: sd_admin_test.pub
securedrop_app_https_certificate_cert_src: sd.crt
securedrop_app_https_certificate_chain_src: ca.crt
securedrop_app_https_certificate_key_src: key.asc
securedrop_app_https_on_source_interface: true
securedrop_supported_locales:
- de_DE
- es_ES
smtp_relay: smtp.gmail.com
smtp_relay_port: 587
ssh_users: sd
v2_onion_services: false
v3_onion_services: true
'''


def setup_function(function):
    global SD_DIR
    SD_DIR = tempfile.mkdtemp()
    ANSIBLE_BASE = '{0}/install_files/ansible-base'.format(SD_DIR)
    cmd = 'mkdir -p {0}/group_vars/all'.format(ANSIBLE_BASE).split()
    subprocess.check_call(cmd)
    for name in ['sd_admin_test.pub', 'ca.crt', 'sd.crt', 'key.asc']:
        subprocess.check_call('cp -r {0}/files/{1} {2}'.format(CURRENT_DIR,
                              name, ANSIBLE_BASE).split())
    for name in ['de_DE', 'es_ES', 'fr_FR', 'pt_BR']:
        dircmd = 'mkdir -p {0}/securedrop/translations/{1}'.format(
            SD_DIR, name)
        subprocess.check_call(dircmd.split())


def teardown_function(function):
    subprocess.check_call('rm -rf {0}'.format(SD_DIR).split())


def verify_username_prompt(child):
    child.expect(b"Username for SSH access to the servers:")


def verify_reboot_prompt(child):
    child.expect(
        rb"Daily reboot time of the server \(24\-hour clock\):", timeout=2)
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == '4'  # noqa: E501


def verify_ipv4_appserver_prompt(child):
    child.expect(rb'Local IPv4 address for the Application Server\:', timeout=2)  # noqa: E501
    # Expected default
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == '10.20.2.2'  # noqa: E501


def verify_ipv4_monserver_prompt(child):
    child.expect(rb'Local IPv4 address for the Monitor Server\:', timeout=2)
    # Expected default
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == '10.20.3.2'  # noqa: E501


def verify_hostname_app_prompt(child):
    child.expect(rb'Hostname for Application Server\:', timeout=2)
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == 'app'  # noqa: E501


def verify_hostname_mon_prompt(child):
    child.expect(rb'Hostname for Monitor Server\:', timeout=2)
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == 'mon'  # noqa: E501


def verify_dns_prompt(child):
    child.expect(rb'DNS server specified during installation\:', timeout=2)
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == '8.8.8.8'  # noqa: E501


def verify_app_gpg_key_prompt(child):
    child.expect(rb'Local filepath to public key for SecureDrop Application GPG public key\:', timeout=2)  # noqa: E501


def verify_https_prompt(child):
    child.expect(rb'Whether HTTPS should be enabled on Source Interface \(requires EV cert\)\:', timeout=2)  # noqa: E501


def verify_https_cert_prompt(child):
    child.expect(rb'Local filepath to HTTPS certificate\:', timeout=2)


def verify_https_cert_key_prompt(child):
    child.expect(rb'Local filepath to HTTPS certificate key\:', timeout=2)


def verify_https_cert_chain_file_prompt(child):
    child.expect(rb'Local filepath to HTTPS certificate chain file\:', timeout=2)  # noqa: E501


def verify_app_gpg_fingerprint_prompt(child):
    child.expect(rb'Full fingerprint for the SecureDrop Application GPG Key\:', timeout=2)  # noqa: E501


def verify_ossec_gpg_key_prompt(child):
    child.expect(rb'Local filepath to OSSEC alerts GPG public key\:', timeout=2)  # noqa: E501


def verify_ossec_gpg_fingerprint_prompt(child):
    child.expect(rb'Full fingerprint for the OSSEC alerts GPG public key\:', timeout=2)  # noqa: E501


def verify_admin_email_prompt(child):
    child.expect(rb'Admin email address for receiving OSSEC alerts\:', timeout=2)  # noqa: E501


def verify_journalist_gpg_key_prompt(child):
    child.expect(rb'Local filepath to journalist alerts GPG public key \(optional\)\:', timeout=2)  # noqa: E501


def verify_journalist_fingerprint_prompt(child):
    child.expect(rb'Full fingerprint for the journalist alerts GPG public key \(optional\)\:', timeout=2)  # noqa: E501


def verify_journalist_email_prompt(child):
    child.expect(rb'Email address for receiving journalist alerts \(optional\)\:', timeout=2)  # noqa: E501


def verify_smtp_relay_prompt(child):
    child.expect(rb'SMTP relay for sending OSSEC alerts\:', timeout=2)
    # Expected default
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == 'smtp.gmail.com'  # noqa: E501


def verify_smtp_port_prompt(child):
    child.expect(rb'SMTP port for sending OSSEC alerts\:', timeout=2)
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == '587'  # noqa: E501


def verify_sasl_domain_prompt(child):
    child.expect(rb'SASL domain for sending OSSEC alerts\:', timeout=2)
    # Expected default
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == 'gmail.com'  # noqa: E501


def verify_sasl_username_prompt(child):
    child.expect(rb'SASL username for sending OSSEC alerts\:', timeout=2)


def verify_sasl_password_prompt(child):
    child.expect(rb'SASL password for sending OSSEC alerts\:', timeout=2)


def verify_ssh_over_lan_prompt(child):
    child.expect(rb'will be available over LAN only\:', timeout=2)
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == 'yes'  # noqa: E501


def verify_locales_prompt(child):
    child.expect(rb'Space separated list of additional locales to support')  # noqa: E501


def verify_v2_onion_for_first_time(child):
    child.expect(rb' installed before 1.0.0\)\?\:', timeout=2)  # noqa: E501
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == 'no'  # noqa: E501


def verify_v3_onion_for_first_time(child):
    child.expect(rb'Do you want to enable v3 onion services \(recommended\)\?\:', timeout=2)  # noqa: E501
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == 'yes'  # noqa: E501


def verify_v3_onion_when_v2_is_enabled(child):
    child.expect(rb'Do you want to enable v3 onion services \(recommended\)\?\:', timeout=2)  # noqa: E501
    assert ANSI_ESCAPE.sub('', child.buffer.decode("utf-8")).strip() == 'yes'  # noqa: E501


def test_sdconfig_on_first_run():
    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    child = pexpect.spawn('python {0} --root {1} sdconfig'.format(cmd, SD_DIR))
    verify_username_prompt(child)
    child.sendline('')
    verify_reboot_prompt(child)
    child.sendline('\b5')  # backspace and put 5
    verify_ipv4_appserver_prompt(child)
    child.sendline('')
    verify_ipv4_monserver_prompt(child)
    child.sendline('')
    verify_hostname_app_prompt(child)
    child.sendline('')
    verify_hostname_mon_prompt(child)
    child.sendline('')
    verify_dns_prompt(child)
    child.sendline('')
    verify_app_gpg_key_prompt(child)
    child.sendline('\b' * 14 + 'sd_admin_test.pub')
    verify_https_prompt(child)
    # Default answer is no
    child.sendline('')
    verify_app_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_ossec_gpg_key_prompt(child)
    child.sendline('\b' * 9 + 'sd_admin_test.pub')
    verify_ossec_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_admin_email_prompt(child)
    child.sendline('test@gmail.com')
    verify_journalist_gpg_key_prompt(child)
    child.sendline('')
    verify_smtp_relay_prompt(child)
    child.sendline('')
    verify_smtp_port_prompt(child)
    child.sendline('')
    verify_sasl_domain_prompt(child)
    child.sendline('')
    verify_sasl_username_prompt(child)
    child.sendline('testuser')
    verify_sasl_password_prompt(child)
    child.sendline('testpassword')
    verify_ssh_over_lan_prompt(child)
    child.sendline('')
    verify_locales_prompt(child)
    child.sendline('de_DE es_ES')
    verify_v2_onion_for_first_time(child)
    child.sendline('\b' * 3 + 'no')
    verify_v3_onion_for_first_time(child)
    child.sendline('\b' * 4 + 'yes')

    child.expect(pexpect.EOF, timeout=10)  # Wait for validation to occur
    child.close()
    assert child.exitstatus == 0
    assert child.signalstatus is None

    with open(os.path.join(SD_DIR, 'install_files/ansible-base/group_vars/all/site-specific')) as fobj:    # noqa: E501
        data = fobj.read()
    assert data == OUTPUT1


def test_sdconfig_both_v2_v3_true():
    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    child = pexpect.spawn('python {0} --root {1} sdconfig'.format(cmd, SD_DIR))
    verify_username_prompt(child)
    child.sendline('')
    verify_reboot_prompt(child)
    child.sendline('\b5')  # backspace and put 5
    verify_ipv4_appserver_prompt(child)
    child.sendline('')
    verify_ipv4_monserver_prompt(child)
    child.sendline('')
    verify_hostname_app_prompt(child)
    child.sendline('')
    verify_hostname_mon_prompt(child)
    child.sendline('')
    verify_dns_prompt(child)
    child.sendline('')
    verify_app_gpg_key_prompt(child)
    child.sendline('\b' * 14 + 'sd_admin_test.pub')
    verify_https_prompt(child)
    # Default answer is no
    child.sendline('')
    verify_app_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_ossec_gpg_key_prompt(child)
    child.sendline('\b' * 9 + 'sd_admin_test.pub')
    verify_ossec_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_admin_email_prompt(child)
    child.sendline('test@gmail.com')
    verify_journalist_gpg_key_prompt(child)
    child.sendline('')
    verify_smtp_relay_prompt(child)
    child.sendline('')
    verify_smtp_port_prompt(child)
    child.sendline('')
    verify_sasl_domain_prompt(child)
    child.sendline('')
    verify_sasl_username_prompt(child)
    child.sendline('testuser')
    verify_sasl_password_prompt(child)
    child.sendline('testpassword')
    verify_ssh_over_lan_prompt(child)
    child.sendline('')
    verify_locales_prompt(child)
    child.sendline('de_DE es_ES')
    verify_v2_onion_for_first_time(child)
    child.sendline('\b' * 3 + 'yes')
    verify_v3_onion_when_v2_is_enabled(child)
    child.sendline('\b' * 3 + 'yes')

    child.expect(pexpect.EOF, timeout=10)  # Wait for validation to occur
    child.close()
    assert child.exitstatus == 0
    assert child.signalstatus is None

    with open(os.path.join(SD_DIR, 'install_files/ansible-base/group_vars/all/site-specific')) as fobj:    # noqa: E501
        data = fobj.read()
    assert data == WHEN_BOTH_TRUE


def test_sdconfig_only_v2_true():
    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    child = pexpect.spawn('python {0} --root {1} sdconfig'.format(cmd, SD_DIR))
    verify_username_prompt(child)
    child.sendline('')
    verify_reboot_prompt(child)
    child.sendline('\b5')  # backspace and put 5
    verify_ipv4_appserver_prompt(child)
    child.sendline('')
    verify_ipv4_monserver_prompt(child)
    child.sendline('')
    verify_hostname_app_prompt(child)
    child.sendline('')
    verify_hostname_mon_prompt(child)
    child.sendline('')
    verify_dns_prompt(child)
    child.sendline('')
    verify_app_gpg_key_prompt(child)
    child.sendline('\b' * 14 + 'sd_admin_test.pub')
    verify_https_prompt(child)
    # Default answer is no
    child.sendline('')
    verify_app_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_ossec_gpg_key_prompt(child)
    child.sendline('\b' * 9 + 'sd_admin_test.pub')
    verify_ossec_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_admin_email_prompt(child)
    child.sendline('test@gmail.com')
    verify_journalist_gpg_key_prompt(child)
    child.sendline('')
    verify_smtp_relay_prompt(child)
    child.sendline('')
    verify_smtp_port_prompt(child)
    child.sendline('')
    verify_sasl_domain_prompt(child)
    child.sendline('')
    verify_sasl_username_prompt(child)
    child.sendline('testuser')
    verify_sasl_password_prompt(child)
    child.sendline('testpassword')
    verify_ssh_over_lan_prompt(child)
    child.sendline('')
    verify_locales_prompt(child)
    child.sendline('de_DE es_ES')
    verify_v2_onion_for_first_time(child)
    child.sendline('\b' * 3 + 'yes')
    verify_v3_onion_when_v2_is_enabled(child)
    child.sendline('\b' * 3 + 'no')

    child.expect(pexpect.EOF, timeout=10)  # Wait for validation to occur
    child.close()
    assert child.exitstatus == 0
    assert child.signalstatus is None

    with open(os.path.join(SD_DIR, 'install_files/ansible-base/group_vars/all/site-specific')) as fobj:    # noqa: E501
        data = fobj.read()
    assert data == WHEN_ONLY_V2


def test_sdconfig_enable_journalist_alerts():
    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    child = pexpect.spawn('python {0} --root {1} sdconfig'.format(cmd, SD_DIR))
    verify_username_prompt(child)
    child.sendline('')
    verify_reboot_prompt(child)
    child.sendline('\b5')  # backspace and put 5
    verify_ipv4_appserver_prompt(child)
    child.sendline('')
    verify_ipv4_monserver_prompt(child)
    child.sendline('')
    verify_hostname_app_prompt(child)
    child.sendline('')
    verify_hostname_mon_prompt(child)
    child.sendline('')
    verify_dns_prompt(child)
    child.sendline('')
    verify_app_gpg_key_prompt(child)
    child.sendline('\b' * 14 + 'sd_admin_test.pub')
    verify_https_prompt(child)
    # Default answer is no
    child.sendline('')
    verify_app_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_ossec_gpg_key_prompt(child)
    child.sendline('\b' * 9 + 'sd_admin_test.pub')
    verify_ossec_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_admin_email_prompt(child)
    child.sendline('test@gmail.com')
    # We will provide a key for this question
    verify_journalist_gpg_key_prompt(child)
    child.sendline('sd_admin_test.pub')
    verify_journalist_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_journalist_email_prompt(child)
    child.sendline('test@gmail.com')
    verify_smtp_relay_prompt(child)
    child.sendline('')
    verify_smtp_port_prompt(child)
    child.sendline('')
    verify_sasl_domain_prompt(child)
    child.sendline('')
    verify_sasl_username_prompt(child)
    child.sendline('testuser')
    verify_sasl_password_prompt(child)
    child.sendline('testpassword')
    verify_ssh_over_lan_prompt(child)
    child.sendline('')
    verify_locales_prompt(child)
    child.sendline('de_DE es_ES')
    verify_v2_onion_for_first_time(child)
    child.sendline('\b' * 3 + 'no')
    verify_v3_onion_for_first_time(child)
    child.sendline('\b' * 4 + 'yes')

    child.expect(pexpect.EOF, timeout=10)  # Wait for validation to occur
    child.close()
    assert child.exitstatus == 0
    assert child.signalstatus is None

    with open(os.path.join(SD_DIR, 'install_files/ansible-base/group_vars/all/site-specific')) as fobj:    # noqa: E501
        data = fobj.read()
    assert JOURNALIST_ALERT_OUTPUT == data


def test_sdconfig_enable_https_on_source_interface():
    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    child = pexpect.spawn('python {0} --root {1} sdconfig'.format(cmd, SD_DIR))
    verify_username_prompt(child)
    child.sendline('')
    verify_reboot_prompt(child)
    child.sendline('\b5')  # backspace and put 5
    verify_ipv4_appserver_prompt(child)
    child.sendline('')
    verify_ipv4_monserver_prompt(child)
    child.sendline('')
    verify_hostname_app_prompt(child)
    child.sendline('')
    verify_hostname_mon_prompt(child)
    child.sendline('')
    verify_dns_prompt(child)
    child.sendline('')
    verify_app_gpg_key_prompt(child)
    child.sendline('\b' * 14 + 'sd_admin_test.pub')
    verify_https_prompt(child)
    # Default answer is no
    # We will press backspace twice and type yes
    child.sendline('\b\byes')
    verify_https_cert_prompt(child)
    child.sendline('sd.crt')
    verify_https_cert_key_prompt(child)
    child.sendline('key.asc')
    verify_https_cert_chain_file_prompt(child)
    child.sendline('ca.crt')
    verify_app_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_ossec_gpg_key_prompt(child)
    child.sendline('\b' * 9 + 'sd_admin_test.pub')
    verify_ossec_gpg_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_admin_email_prompt(child)
    child.sendline('test@gmail.com')
    # We will provide a key for this question
    verify_journalist_gpg_key_prompt(child)
    child.sendline('sd_admin_test.pub')
    verify_journalist_fingerprint_prompt(child)
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    verify_journalist_email_prompt(child)
    child.sendline('test@gmail.com')
    verify_smtp_relay_prompt(child)
    child.sendline('')
    verify_smtp_port_prompt(child)
    child.sendline('')
    verify_sasl_domain_prompt(child)
    child.sendline('')
    verify_sasl_username_prompt(child)
    child.sendline('testuser')
    verify_sasl_password_prompt(child)
    child.sendline('testpassword')
    verify_ssh_over_lan_prompt(child)
    child.sendline('')
    verify_locales_prompt(child)
    child.sendline('de_DE es_ES')
    verify_v2_onion_for_first_time(child)
    child.sendline('\b' * 3 + 'no')
    verify_v3_onion_for_first_time(child)
    child.sendline('\b' * 4 + 'yes')

    child.expect(pexpect.EOF, timeout=10)  # Wait for validation to occur
    child.close()
    assert child.exitstatus == 0
    assert child.signalstatus is None

    with open(os.path.join(SD_DIR, 'install_files/ansible-base/group_vars/all/site-specific')) as fobj:    # noqa: E501
        data = fobj.read()
    assert HTTPS_OUTPUT == data


# The following is the minimal git configuration which can be used to fetch
# from the SecureDrop Github repository. We want to use this because the
# developers may have the git setup to fetch from git@github.com: instead
# of the https, and that requires authentication information.
GIT_CONFIG = u'''[core]
        repositoryformatversion = 0
        filemode = true
        bare = false
        logallrefupdates = true
[remote "origin"]
        url = https://github.com/freedomofpress/securedrop.git
        fetch = +refs/heads/*:refs/remotes/origin/*
'''


@pytest.fixture
def securedrop_git_repo(tmpdir):
    os.chdir(str(tmpdir))
    # Clone the SecureDrop repository into the temp directory.
    cmd = ['git', 'clone',
           'https://github.com/freedomofpress/securedrop.git']
    subprocess.check_call(cmd)
    os.chdir(os.path.join(str(tmpdir), 'securedrop/admin'))
    subprocess.check_call('git reset --hard'.split())
    # Now we will put in our own git configuration
    with io.open('../.git/config', 'w') as fobj:
        fobj.write(GIT_CONFIG)
    # Let us move to an older tag
    subprocess.check_call('git checkout 0.6'.split())
    yield tmpdir

    # Save coverage information in same directory as unit test coverage
    test_name = str(tmpdir).split('/')[-1]
    try:
        subprocess.check_call(
            ['cp', '{}/securedrop/admin/.coverage'.format(str(tmpdir)),
             '{}/../.coverage.{}'.format(CURRENT_DIR, test_name)])
    except subprocess.CalledProcessError:
        # It means the coverage file may not exist, don't error
        pass


def set_reliable_keyserver(gpgdir):
    # If gpg.conf doesn't exist, create it and set a reliable default
    # keyserver for the tests.
    gpgconf_path = os.path.join(gpgdir, 'gpg.conf')
    if not os.path.exists(gpgconf_path):
        os.mkdir(gpgdir)
        with open(gpgconf_path, 'a') as f:
            f.write('keyserver hkps://keys.openpgp.org')

        # Ensure correct permissions on .gnupg home directory.
        os.chmod(gpgdir, 0o0700)


@flaky(max_runs=3)
def test_check_for_update_when_updates_needed(securedrop_git_repo):
    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    ansible_base = os.path.join(str(securedrop_git_repo),
                                'securedrop/install_files/ansible-base')
    fullcmd = 'coverage run {0} --root {1} check_for_updates'.format(
                cmd, ansible_base)
    child = pexpect.spawn(fullcmd)
    child.expect(b'Update needed', timeout=20)

    child.expect(pexpect.EOF, timeout=10)  # Wait for CLI to exit
    child.close()
    assert child.exitstatus == 0
    assert child.signalstatus is None


@flaky(max_runs=3)
def test_check_for_update_when_updates_not_needed(securedrop_git_repo):
    # Determine latest production tag using GitHub release object
    github_url = 'https://api.github.com/repos/freedomofpress/securedrop/releases/latest'  # noqa: E501
    latest_release = requests.get(github_url).json()
    latest_tag = str(latest_release["tag_name"])

    subprocess.check_call(["git", "checkout", latest_tag])

    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    ansible_base = os.path.join(str(securedrop_git_repo),
                                'securedrop/install_files/ansible-base')
    fullcmd = 'coverage run {0} --root {1} check_for_updates'.format(
        cmd, ansible_base)
    child = pexpect.spawn(fullcmd)
    child.expect(b'All updates applied', timeout=20)

    child.expect(pexpect.EOF, timeout=10)  # Wait for CLI to exit
    child.close()
    assert child.exitstatus == 0
    assert child.signalstatus is None


@flaky(max_runs=3)
def test_update(securedrop_git_repo):
    gpgdir = os.path.join(os.path.expanduser('~'), '.gnupg')
    set_reliable_keyserver(gpgdir)

    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    ansible_base = os.path.join(str(securedrop_git_repo),
                                'securedrop/install_files/ansible-base')
    child = pexpect.spawn('coverage run {0} --root {1} update'.format(
        cmd, ansible_base))

    output = child.read()
    assert b'Updated to SecureDrop' in output
    assert b'Signature verification successful' in output

    child.expect(pexpect.EOF, timeout=10)  # Wait for CLI to exit
    child.close()
    assert child.exitstatus == 0
    assert child.signalstatus is None


@flaky(max_runs=3)
def test_update_fails_when_no_signature_present(securedrop_git_repo):
    gpgdir = os.path.join(os.path.expanduser('~'), '.gnupg')
    set_reliable_keyserver(gpgdir)

    # First we make a very high version tag of SecureDrop so that the
    # updater will try to update to it. Since the tag is unsigned, it
    # should fail.
    subprocess.check_call('git checkout develop'.split())
    subprocess.check_call('git tag 9999999.0.0'.split())

    # Switch back to an older branch for the test
    subprocess.check_call('git checkout 0.6'.split())

    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    ansible_base = os.path.join(str(securedrop_git_repo),
                                'securedrop/install_files/ansible-base')
    child = pexpect.spawn('coverage run {0} --root {1} update'.format(
                          cmd, ansible_base))
    output = child.read()
    assert b'Updated to SecureDrop' not in output
    assert b'Signature verification failed' in output

    child.expect(pexpect.EOF, timeout=10)  # Wait for CLI to exit
    child.close()

    # Failures should eventually exit non-zero.
    assert child.exitstatus != 0
    assert child.signalstatus != 0


@flaky(max_runs=3)
def test_update_with_duplicate_branch_and_tag(securedrop_git_repo):
    gpgdir = os.path.join(os.path.expanduser('~'), '.gnupg')
    set_reliable_keyserver(gpgdir)

    github_url = 'https://api.github.com/repos/freedomofpress/securedrop/releases/latest'  # noqa: E501
    latest_release = requests.get(github_url).json()
    latest_tag = str(latest_release["tag_name"])

    # Create a branch with the same name as a tag.
    subprocess.check_call(['git', 'checkout', '-b', latest_tag])
    # Checkout the older tag again in preparation for the update.
    subprocess.check_call('git checkout 0.6'.split())

    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    ansible_base = os.path.join(str(securedrop_git_repo),
                                'securedrop/install_files/ansible-base')

    child = pexpect.spawn('coverage run {0} --root {1} update'.format(
                          cmd, ansible_base))
    output = child.read()
    # Verify that we do not falsely check out a branch instead of a tag.
    assert b'Switched to branch' not in output
    assert b'Updated to SecureDrop' not in output
    assert b'Signature verification failed' in output

    child.expect(pexpect.EOF, timeout=10)  # Wait for CLI to exit
    child.close()
    assert child.exitstatus != 0
    assert child.signalstatus != 0
