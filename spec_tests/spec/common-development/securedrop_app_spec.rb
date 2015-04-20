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


