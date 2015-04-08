#require 'spec_helper'

['postfix', 'procmail'].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

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
  
