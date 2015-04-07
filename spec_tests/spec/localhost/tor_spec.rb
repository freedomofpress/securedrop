#require 'spec_helper'

describe package('tor') do
  it { should be_installed }
end

describe file('/etc/tor/torrc') do
  it { should be_file }
  its(:content) { should match "HiddenServiceAuthorizeClient stealth journalist" }
  its(:content) { should match "HiddenServiceAuthorizeClient stealth admin" }
end

describe command('sudo service tor status') do
  it { should return_exit_status 0 }
end
