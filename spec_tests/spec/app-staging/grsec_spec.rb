#require 'spec_helper'

['securedrop-grsec'].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

# Check that the system is booted in grsec
describe command("uname -r") do
  it { should return_stdout /grsec/ }
end

# Check that the grsec sysctl settings are correct
describe 'Grsecurity kernel parameters' do
  context linux_kernel_parameter('kernel.grsecurity.grsec_lock') do
    its(:value) { should eq 1 }
  end

  context linux_kernel_parameter('kernel.grsecurity.rwxmap_logging') do
    its(:value) { should eq 0 }
  end
end

# Check that paxtest does not report anything vulnerable
# Requires the package paxtest to be installed
# The paxtest package is currently being installed in the app-test role
describe command("paxtest blackhat") do
  it { should_not return_stdout /vulnerable/ }
end

# Check pax flags for apache tor
# paxctl -v /usr/sbin/apache2
# paxctl -v /usr/sbin/tor
# paxctl -v /usr/sbin/ntp
# paxctl -v /usr/sbin/apt
