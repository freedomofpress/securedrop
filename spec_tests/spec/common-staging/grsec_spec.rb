#require 'spec_helper'

# ensure ssh motd is disabled (grsec balks at ubuntu's default motd)
describe file('/etc/pam.d/sshd') do
  its(:content) { should_not match /pam\.motd/ }
end

['securedrop-grsec', 'paxctl'].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

unwanted_kernel_metapackages = [
  'linux-signed-image-generic-lts-utopic',
  'linux-signed-image-generic',
  'linux-signed-generic-lts-utopic',
  'linux-signed-generic',
]
unwanted_kernel_metapackages.each do |metapkg|
  describe package(metapkg) do
    it { should_not be_installed }
  end
end

# ensure that system is running grsec kernel
describe file('/proc/sys/kernel/grsecurity/grsec_lock') do
  it { should be_mode '600' }
  it { should be_owned_by('root') }
  its(:size) { should eq 0 }
end

# ensure that system reports it's running grsec kernel (lazy)
describe command("uname -r") do
  its(:stdout) { should match /grsec$/ }
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
  its(:stdout) { should_not match /vulnerable/ }
end

# Check pax flags for apache tor
# paxctl -v /usr/sbin/apache2
# paxctl -v /usr/sbin/tor
# paxctl -v /usr/sbin/ntp
# paxctl -v /usr/sbin/apt
