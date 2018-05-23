import os
import time
import pexpect
import tempfile

SD_DIR = ''
CURRENT_DIR = os.path.dirname(__file__)
ANSIBLE_BASE = ''

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
'''


def setup_function(function):
    global SD_DIR
    SD_DIR = tempfile.mkdtemp()
    ANSIBLE_BASE = '{0}/install_files/ansible-base'.format(SD_DIR)
    os.system('mkdir -p {0}/group_vars/all'.format(ANSIBLE_BASE))
    os.system('cp -r {0}/files/* {1}'.format(CURRENT_DIR, ANSIBLE_BASE))
    for name in ['de_DE', 'es_ES', 'fr_FR', 'pt_BR']:
        dircmd = 'mkdir -p {0}/securedrop/translations/{1}'.format(
            SD_DIR, name)
        os.system(dircmd)


def teardown_function(function):
    os.system('rm -rf {0}'.format(SD_DIR))


def test_firstrun():
    cmd = os.path.join(os.path.dirname(CURRENT_DIR),
                       'securedrop_admin/__init__.py')
    child = pexpect.spawn('python {0} --root {1} sdconfig'.format(cmd, SD_DIR))
    child.expect("Username for SSH access to the servers:")
    child.sendline('')
    child.expect(
        "Daily reboot time of the server \(24\-hour clock\):", timeout=2)
    child.sendline('\b5')
    child.expect('Local IPv4 address for the Application Server\:', timeout=2)
    child.sendline('')
    child.expect('Local IPv4 address for the Monitor Server\:', timeout=2)
    child.sendline('')
    child.expect('Hostname for Application Server', timeout=2)
    child.expect_exact('\x1b[0ma\x1b[0mp\x1b[0mp\x1b[36D\x1b[36C\x1b[?7h\x1b[0m\x1b[?12l\x1b[?25h', timeout=2)  # noqa: E501
    child.sendline('')
    child.expect('Hostname for Monitor Server\:', timeout=2)
    child.sendline('')
    child.expect('DNS server specified during installation\:', timeout=2)
    child.expect_exact('\x1b[0m8\x1b[0m.\x1b[0m8\x1b[0m.\x1b[0m8\x1b[0m.\x1b[0m8\x1b[49D\x1b[49C\x1b[?7h\x1b[0m\x1b[?12l\x1b[?25h')  # noqa: E501
    child.sendline('')
    child.expect('Local filepath to public key for SecureDrop Application GPG public key\:', timeout=2)  # noqa: E501
    child.sendline('\b' * 14 + 'sd_admin_test.pub')
    child.expect('Whether HTTPS should be enabled on Source Interface \(requires EV cert\)\:', timeout=2)  # noqa: E501
    child.expect_exact('\x1b[0mn\x1b[0mo\x1b[74D\x1b[74C\x1b[?7h\x1b[0m\x1b[?12l\x1b[?25h')  # noqa: E501
    child.sendline('')
    child.expect('Full fingerprint for the SecureDrop Application GPG Key\:', timeout=2)  # noqa: E501
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    child.expect('Local filepath to OSSEC alerts GPG public key\:', timeout=2)  # noqa: E501
    child.sendline('\b' * 9 + 'sd_admin_test.pub')
    child.expect('Full fingerprint for the OSSEC alerts GPG public key\:', timeout=2)  # noqa: E501
    child.sendline('1F544B31C845D698EB31F2FF364F1162D32E7E58')
    child.expect('Admin email address for receiving OSSEC alerts\:', timeout=2)  # noqa: E501
    child.sendline('test@gmail.com')
    child.expect('Local filepath to journalist alerts GPG public key \(optional\)\:', timeout=2)  # noqa: E501
    child.sendline('')
    child.expect('SMTP relay for sending OSSEC alerts\:', timeout=2)
    child.expect_exact('[0ms\x1b[0mm\x1b[0mt\x1b[0mp\x1b[0m.\x1b[0mg\x1b[0mm\x1b[0ma\x1b[0mi\x1b[0ml\x1b[0m.\x1b[0mc\x1b[0mo\x1b[0mm\x1b[51D\x1b[51C\x1b[?7h\x1b[0m\x1b[?12l\x1b[?25h')  # noqa: E501
    child.sendline('')
    child.expect('SMTP port for sending OSSEC alerts\:', timeout=2)
    child.expect_exact('\x1b[0m5\x1b[0m8\x1b[0m7\x1b[39D\x1b[39C\x1b[?7h\x1b[0m\x1b[?12l\x1b[?25h')  # noqa: E501
    child.sendline('')
    child.expect('SASL domain for sending OSSEC alerts\:', timeout=2)
    child.expect_exact('\x1b[0mg\x1b[0mm\x1b[0ma\x1b[0mi\x1b[0ml\x1b[0m.\x1b[0mc\x1b[0mo\x1b[0mm\x1b[47D\x1b[47C\x1b[?7h\x1b[0m\x1b[?12l\x1b[?25h')  # noqa: E501
    child.sendline('')
    child.expect('SASL username for sending OSSEC alerts\:', timeout=2)
    child.sendline('testuser')
    child.expect('SASL password for sending OSSEC alerts\:', timeout=2)
    child.sendline('testpassword')
    child.expect('will be available over LAN only\:', timeout=2)
    child.expect_exact('\x1b[0my\x1b[0me\x1b[0ms\x1b[37D\x1b[37C\x1b[?7h\x1b[0m\x1b[?12l\x1b[?25h')  # noqa: E501
    child.sendline('')
    child.expect('Space separated list of additional locales to support')  # noqa: E501
    child.sendline('de_DE es_ES')
    time.sleep(2)  # Give time for validation
    with open(os.path.join(SD_DIR, 'install_files/ansible-base/group_vars/all/site-specific')) as fobj:    # noqa: E501
        data = fobj.read()
    assert data == OUTPUT1
