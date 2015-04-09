#require 'spec_helper'

# Apparmor package dependencies
['apparmor', 'apparmor-utils' ].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

# Required apparmor profiles configs
#
# SecureDrop apache apparmor profile
describe file('/etc/apparmor.d/usr.sbin.apache2') do
  it { should be_file }
  it { should be_owned_by 'root' }
  it { should be_mode '644' }
  # The following line should not contain `complain`
  # And should have the correct path for apache2
  its(:content) { should match "/usr/sbin/apache2 {" }
end

# Check that apparmor is enabled.
# The command returns error code if AppArmor not enabled
describe command("aa-status --enabled") do
  it { should_not return_stderr }
end

# Check that the expected profiles are present in the aa-status command.
[ 'apache', 'tor', 'ntp'].each do |enforcedProfiles|
  describe command("aa-status") do
    it { should return_stdout /#{enforcedProfiles}/ }
  end
end

# Ensure that there are no processes in complain mode
describe command("aa-status --complaining") do
  it { should return_stdout "0" }
end

# Ensure that there are no processes that are unconfined but have a profile
describe command("aa-status") do
  it { should return_stdout /0 processes are unconfined but have a profile defined/ }
end
