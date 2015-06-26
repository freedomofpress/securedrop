# Apparmor package dependencies
['apparmor', 'apparmor-utils' ].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

# Check that apparmor is enabled.
# The command returns error code if AppArmor not enabled
describe command("aa-status --enabled") do
  its(:exit_status) { should eq 0 }
end

# SecureDrop apache apparmor profile
# Staging role has two profiles in complain mode:
# tor and apache2. Make sure the config file includes
# that flag, since restarting apparmor will load
# whatever's on disk
['tor', 'apache2'].each do |complaining_process|
  describe file("/etc/apparmor.d/usr.sbin.#{complaining_process}") do
    it { should be_file }
    it { should be_owned_by 'root' }
    it { should be_mode '644' }
    its(:content) { should match /^\/usr\/sbin\/#{complaining_process} flags=\(complain\) \{/ }
  end
end

# declare expected app-armor capabilities for apache2
apache2_capabilities = %w(
  dac_override
  kill
  net_bind_service
  sys_ptrace
)
# check for exact list of expected app-armor capabilities for apache2
describe command('perl -nE \'/^\s+capability\s+(\w+),$/ && say $1\' /etc/apparmor.d/usr.sbin.apache2') do
  apache2_capabilities.each do |apache2_capability|
    its(:stdout) { should contain(apache2_capability) }
  end
end

# ensure no extra capabilities are defined for apache2
describe command('grep -ic capability /etc/apparmor.d/usr.sbin.apache2') do
  its(:stdout) { should eq apache2_capabilities.length.to_s + "\n" }
end

# check for exact list of expected app-armor capabilities for tor
describe command('perl -nE \'/^\s+capability\s+(\w+),$/ && say $1\' /etc/apparmor.d/usr.sbin.tor') do
  its(:stdout) { should contain("setgid") }
end

# ensure no extra capabilities are defined for tor
describe command('grep -ic capability /etc/apparmor.d/usr.sbin.tor') do
  its(:stdout) { should eq "1\n" }
end

# Explicitly check that enforced profiles are NOT
# present in /etc/apparmor.d/disable. Polling aa-status
# only checks the last config that was loaded, whereas
# checking for symlinks in the `disabled` dir checks
# the config to be loaded when the apparmor service is bounced.
enforced_profiles = [
  'ntpd',
  'apache2',
  'tcpdump',
  'tor',
]
enforced_profiles.each do |enforced_profile|
  describe file("/etc/apparmor.d/disabled/usr.sbin.#{enforced_profile}") do
    it { should_not be_file }
    it { should_not be_directory }
    it { should_not be_symlink }
  end
end

# declare app-armor profiles expected to be enforced
enforced_apparmor_profiles = %w(
  /sbin/dhclient
  /usr/lib/NetworkManager/nm-dhcp-client.action
  /usr/lib/connman/scripts/dhclient-script
  /usr/sbin/apache2//DEFAULT_URI
  /usr/sbin/apache2//HANDLING_UNTRUSTED_INPUT
  /usr/sbin/ntpd
  /usr/sbin/tcpdump
  system_tor
)
# check for enforced app-armor profiles
# this klunky one-liner uses bash, because serverspec defaults to sh,
# then provides START and STOP patterns to sed, filters by profile
# names according to leading whitespace, then trims leading whitespace
describe command("aa-status") do
  enforced_apparmor_profiles.each do |enforced_apparmor_profile|
    its(:stdout) { should contain(enforced_apparmor_profile).from(/profiles are in enforce mode/).to(/profiles are in complain mode/) }
  end
end

# ensure number of expected enforced profiles matches number checked
describe command("aa-status --enforced") do
  its(:stdout) { should eq enforced_apparmor_profiles.length.to_s + "\n" }
end

# declare app-armor profiles expected to be complaining
# the staging hosts enabled "complain" mode for more verbose
# logging during development and testing; production hosts
# should not have any complain mode.
complaining_apparmor_profiles = %w(
  /usr/sbin/apache2
  /usr/sbin/tor
)

# check for complaining app-armor profiles
describe command("aa-status") do
  complaining_apparmor_profiles.each do |complaining_apparmor_profile|
    its(:stdout) { should contain(complaining_apparmor_profile).from(/profiles are in complain mode/).to(/\d+ processes have profiles defined/) }
  end
end

# ensure number of expected complaining profiles matches number checked
describe command("aa-status --complaining") do
  its(:stdout) { should eq complaining_apparmor_profiles.length.to_s + "\n" }
end

# ensure number of total profiles is sum of enforced and complaining profiles
describe command("aa-status --profiled") do
  total_profiles = enforced_apparmor_profiles.length + complaining_apparmor_profiles.length
  its(:stdout) { should eq total_profiles.to_s + "\n" }
end

# Ensure that there are no processes that are unconfined but have a profile
describe command("aa-status") do
  its(:stdout) { should contain("0 processes are unconfined but have a profile defined") }
end
