require 'spec_helper'

# development role excludes apache, in favor of flask runner,
# so ensure that apache is not installed.
unwanted_packages = %w(
  securedrop-app-code
  apache2-mpm-worker
  libapache2-mod-wsgi
  libapache2-mod-xsendfile
)
unwanted_packages.each do |unwanted_package|
  describe package(unwanted_package) do
    it { should_not be_installed }
  end
end

# ensure default html dir is absent
describe command("/bin/bash -c '[[ ! -e /var/www/html ]]'") do
  its(:exit_status) { should eq 0 }
end

desired_directories = [
  TEST_VARS['securedrop_code'],
  TEST_VARS['securedrop_data'],
  "#{TEST_VARS['securedrop_data']}/keys",
  "#{TEST_VARS['securedrop_data']}/tmp",
  "#{TEST_VARS['securedrop_data']}/store",
]
desired_directories.each do |desired_directory|
  describe file(desired_directory) do
    it { should be_directory }
    it { should be_owned_by TEST_VARS['securedrop_user'] }
  end
end

