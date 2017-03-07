import os

REQUIRED_OSSEC_SERVER_PACKAGES = [
        'postfix',
        'procmail',
        'mailutils',
        'securedrop-ossec-server']

POSTFIX_HEADER_FILE = '/etc/postfix/header_checks'
POSTFIX_SETTINGS_FILE = '/etc/postfix/main.cf'
POSTFIX_HEADER_SETTINGS = [
  '/^X-Originating-IP:/    IGNORE',
  '/^X-Mailer:/    IGNORE',
  '/^Mime-Version:/        IGNORE',
  '/^User-Agent:/  IGNORE',
  '/^Received:/    IGNORE']
POSTFIX_SETTINGS = os.path.dirname(os.path.abspath(__file__))+'/postfix_settings'
OSSEC_GNUPG = "/var/ossec/.gnupg"
OSSEC_ADMIN_KEY = "/var/ossec/test_admin_key.pub"

OSSEC_GPG_KEY_OUTPUT = """pub   4096R/EDDDC102 2014-10-15
uid                  Test/Development (DO NOT USE IN PRODUCTION) (Admin's OSSEC Alert GPG key) <securedrop@freedom.press>
sub   4096R/97D2EB39 2014-10-15"""

OSSEC_KEY_FILES = ['/var/ossec/etc/sslmanager.key',
                   '/var/ossec/etc/sslmanager.cert']

OSSEC_PROCMAIL_FILE = "/var/ossec/.procmailrc"
OSSEC_PROCMAIL_SETTINGS = [
  'VERBOSE=yes',
  'MAILDIR=/var/mail/',
  'DEFAULT=$MAILDIR',
  'LOGFILE=/var/log/procmail.log',
  'SUBJECT=`formail -xSubject:`',
  ':0 c',
  '*^To:.*root.*',
  '|/var/ossec/send_encrypted_alarm.sh',
]
OSSEC_ENCRYPTED_ALARM = "/var/ossec/send_encrypted_alarm.sh"
PROCMAIL_LOG = "/var/log/procmail.log"
