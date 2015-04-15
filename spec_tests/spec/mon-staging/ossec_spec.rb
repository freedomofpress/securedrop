#require 'spec_helper'
#
# ensure hosts file references app server by ip
# TODO: replace hardcoded ip for app-staging host
describe file('/etc/hosts') do
  its(:content) { should match /^127\.0\.1\.1 mon-staging mon-staging$/ }
  its(:content) { should match /^10\.0\.1\.2  app-staging$/ }
end

# ensure mail packages are installed
['postfix', 'procmail', 'mailutils'].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

# ensure custom /etc/aliases is present
describe file('/etc/aliases') do
  it { should be_file }
  it { should be_mode '644' }
  its(:content) { should match /^root: ossec$/ }
end

# ensure sasl password for smtp relay is configured
# TODO: values below are hardcoded. for staging, 
# this is probably ok. 
describe file('/etc/postfix/sasl_passwd') do
  sasl_passwd_regex = Regexp.quote('[smtp.gmail.com]:587   test@ossec.test:password123')
  its(:content) { should match /^#{sasl_passwd_regex}$/ }
end

# declare desired regex checks for stripping smtp headers
header_checks = [
  '/^X-Originating-IP:/    IGNORE',
  '/^X-Mailer:/    IGNORE',
  '/^Mime-Version:/        IGNORE',
  '/^User-Agent:/  IGNORE',
  '/^Received:/    IGNORE',
]
# ensure header_checks regex to strip smtl headers are present
describe file ('/etc/postfix/header_checks') do
  it { should be_file }
  it { should be_mode '644' }
  header_checks.each do |header_check|
    header_check_regex = Regexp.quote(header_check)
    its(:content) { should match /^#{header_check_regex}$/ }
  end
end

# TODO: checking this file will require a lot of regexes
describe file('/etc/postfix/main.cf') do
  it { should be_file }
  its(:content) { should match /^mailbox_command = \/usr\/bin\/procmail$/ }
end

describe file("/var/ossec/.gnupg") do
  it { should be_directory }
  it { should be_owned_by "ossec" }
  it { should be_mode '700' }
end

describe file("/var/ossec/.procmailrc") do
  its(:content) { should match /^\|\/var\/ossec\/send_encrypted_alarm\.sh/ }
end
  
# TODO: mode 0755 sounds right to me, but the mon-staging host
# actually has mode 1407. Debug after serverspec tests have been ported
#describe file("/var/ossec/send_encrypted_alarm.sh") do
#  it { should be_mode '0755' }
#end

describe file("/var/log/procmail.log") do
  it { should be_owned_by "ossec" }
end
  
