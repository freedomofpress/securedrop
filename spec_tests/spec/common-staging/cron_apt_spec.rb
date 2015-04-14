#require 'spec_helper'

# Check for critical packages
['cron-apt', 'ntp', 'paxctl', 'ossec-agent', 'haveged', 'securedrop-grsec', 'securedrop-app-code', 'securedrop-ossec-agent'].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

# ensure custom cron-apt config file is present
describe file('/etc/cron-apt/config') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match /^SYSLOGON="always"$/ }
  its(:content) { should match /^EXITON=error$/ }
end

# list desired security repositories
security_repositories = [
  'deb http://security.ubuntu.com/ubuntu trusty-security main',
  'deb-src http://security.ubuntu.com/ubuntu trusty-security main',
  'deb http://security.ubuntu.com/ubuntu trusty-security universe',
  'deb-src http://security.ubuntu.com/ubuntu trusty-security universe',
  'deb [arch=amd64] https://apt.freedom.press trusty main',
  'deb http://deb.torproject.org/torproject.org trusty main',
]
# ensure custom security.list file is present
describe file('/etc/apt/security.list') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  security_repositories.each do |repo|
    repo_regex = Regexp.quote(repo)
    its(:content) { should match /^#{repo_regex}$/ }
  end
end

# ensure cron-apt updates the security.list packages
describe file('/etc/cron-apt/action.d/0-update') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  repo_regex = Regexp.quote('update -o quiet=2 -o Dir::Etc::SourceList=/etc/apt/security.list -o Dir::Etc::SourceParts=""')
  its(:content) { should match /^#{repo_regex}$/ }
end

# ensure cron-apt upgrades the security.list packages
describe file('/etc/cron-apt/action.d/5-security') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match /^autoclean -y$/ }
  config_regex = Regexp.quote('dist-upgrade -y -o APT::Get::Show-Upgraded=true -o Dir::Etc::SourceList=/etc/apt/security.list -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold')
  its(:content) { should match /^#{config_regex}$/ }
  its(:content) { should match /^autoremove -y$/ }
end

# TODO: In order to validate the intended system state post-provisioning, 
# may be simplest to compare output of `dpkg --get-selections` 
# from a clean box versus a post-provisioned one. However,
# there will be environment-specific items in this list (e.g. vbox)
# that must be pruned.
