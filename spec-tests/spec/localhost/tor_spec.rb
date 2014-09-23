require 'spec_helper'

describe package('tor') do
  it { should be_installed }
end

describe file('/etc/tor/torrc') do
  it { should be_file }
  its(:content) { should match /SocksPort 0/ }
end
