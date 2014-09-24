require 'spec_helper'

describe package('tor') do
  it { should be_installed }
end

describe file('/etc/tor/torrc') do
  it { should be_file }
  its(:content) { should contain 'ReachableAddresses *:80,*:8080,*:443,*:8443,*:9001,*:9030' }
end

describe command('service tor status') do
  it { should return_exit_status 0 }
end

