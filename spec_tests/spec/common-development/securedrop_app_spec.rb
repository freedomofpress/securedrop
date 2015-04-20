require 'spec_helper'


# this file tests for app-related config
# common to "development" and "app-staging"

# ensure default apache html directory is absent
describe command('/bin/bash -c "[[ ! -e /var/www/html  ]]"') do
  its(:exit_status) { should eq 0 }
end

# declare securedrop-app package dependencies
securedrop_package_dependencies = [
  'apparmor-utils',
  'gnupg2',
  'haveged',
  'python',
  'python-pip',
  'redis-server',
  'secure-delete',
  'sqlite',
  'supervisor',
]
# ensure securedrop-app dependencies are installed
securedrop_package_dependencies.each do |securedrop_package_dependency|
  describe package(securedrop_package_dependency) do
    it { should be_installed }
  end
end

# ensure haveged's low entrop watermark is sufficiently high
describe file('/etc/default/haveged') do
  it { should be_file }
  it { should be_mode '644' }
  it { should be_owned_by 'root' }
  it { should be_grouped_into 'root' }
  # TODO: lineinfile is appending needlessly here, let's just template this file
  its(:content) { should match /^DAEMON_ARGS="-w 2400"$/ }
end

# ensure haveged is running
describe service('haveged') do
  it { should be_enabled }
  it { should be_running }
end
# ensure haveged's low entrop watermark is sufficiently high
describe file('/etc/default/haveged') do
  it { should be_file }
  it { should be_mode '644' }
  it { should be_owned_by 'root' }
  it { should be_grouped_into 'root' }
  # TODO: lineinfile is appending needlessly here, let's just template this file
  its(:content) { should match /^DAEMON_ARGS="-w 2400"$/ }
end

# ensure haveged is running
describe service('haveged') do
  it { should be_enabled }
  it { should be_running }
end
