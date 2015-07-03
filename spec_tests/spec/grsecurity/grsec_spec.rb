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
paxtest_check_killed = [
  "Executable anonymous mapping",
  "Executable bss",
  "Executable data",
  "Executable heap",
  "Executable stack",
  "Executable shared library bss",
  "Executable shared library data",
  "Executable anonymous mapping (mprotect)",
  "Executable bss (mprotect)",
  "Executable data (mprotect)",
  "Executable heap (mprotect)",
  "Executable stack (mprotect)",
  "Executable shared library bss (mprotect)",
  "Executable shared library data (mprotect)",
  "Writable text segments",
  "Return to function (memcpy)",
  "Return to function (memcpy, PIE)",
]
# TODO: enable the paxtest checks below once the "paxtest"
# package is included via the grsecurity role.
#describe command("paxtest blackhat") do
#  paxtest_check_killed.each do |killed|
#    its(:stdout) { should match /^#{Regexp.escape(killed)}\s*:\sKilled/ }
#  end
#  its(:stdout) { should_not match /Vulnerable/i }
#  its(:exit_status) { should eq 0 }
#end

# ensure generic linux kernels have been removed
describe command("dpkg --get-selections '^linux-image-.*generic$'") do
  its(:stdout) { should_not match /^linux-image-.*generic$/ }
  its(:stderr) { should match /^dpkg: no packages found matching / }
  its(:exit_status) { should eq 0 }
end

# ensure linux kernel headers have been removed
describe command("dpkg --get-selections '^linux-headers-.*'") do
  its(:stdout) { should_not match /^linux-headers-.*/ }
  its(:stderr) { should match /^dpkg: no packages found matching / }
  its(:exit_status) { should eq 0 }
end

# ensure grub-pc is marked as manually installed (necessary vagrant/vbox)
describe command('apt-mark showmanual grub-pc') do
  its(:stdout) { should match /^grub-pc$/ }
end

# ensure old packages have been autoremoved
describe command('apt-get --dry-run autoremove') do
  its(:stdout) { should match /^0 upgraded, 0 newly installed, 0 to remove and 0 not upgraded\.$/ }
  its(:exit_status) { should eq 0 }
end

# Check pax flags for apache tor
# paxctl -v /usr/sbin/apache2
# paxctl -v /usr/sbin/tor
# paxctl -v /usr/sbin/ntp
# paxctl -v /usr/sbin/apt
