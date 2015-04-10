#require 'spec_helper'

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


# Make sure that ONLY two profiles are in complain mode.
describe command("aa-status --complaining") do
  its(:stdout) { should eq "2\n" }
end

# Check that the expected profiles are present in the aa-status command.
#[ 'apache', 'tor', 'ntp'].each do |enforced_profile|
#  describe command("aa-status") do
#    it { should return_stdout /#{enforced_profile}/ }
#  end
#end

# Ensure that there are no processes that are unconfined but have a profile
describe command("aa-status") do
  its(:stdout) { should match /0 processes are unconfined but have a profile defined/ }
end
