#require 'spec_helper'

describe package('tor') do
  it { should be_installed }
end

describe file('/etc/tor/torrc') do
  it { should be_file }
  it { should be_mode '644' }
  its(:content) { should match "HiddenServiceAuthorizeClient stealth journalist" }
  its(:content) { should match "HiddenServiceAuthorizeClient stealth admin" }
end

describe service('tor') do
  it { should be_enabled }
  it { should be_running }
end

# Likely overkill
describe command('service tor status') do
  its(:exit_status) { should eq 0 }
  its(:stdout) { should match /tor is running/ }
end
