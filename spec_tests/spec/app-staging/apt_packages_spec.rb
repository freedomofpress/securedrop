#require 'spec_helper'

['cron-apt', 'ntp', 'paxctl'].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

# Check for cron-apt auto-update config
describe file('/etc/cron-apt/action.d/0-update') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match 'update -o quiet=2 -o Dir::Etc::SourceList=/etc/apt/security.list -o Dir::Etc::SourceParts=""' }
end

# Check for cron-apt security.list config
describe file('/etc/cron-apt/action.d/5-security') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match /^autoclean -y$/ }
  its(:content) { should match "dist-upgrade -y -o APT::Get::Show-Upgraded=true -o Dir::Etc::SourceList=/etc/apt/security.list -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold"}
  its(:content) { should match /^autoremove -y$/ }
end

# TODO: In order to validate the intended system state post-provisioning, 
# may be simplest to compare output of `dpkg --get-selections` 
# from a clean box versus a post-provisioned one. 

