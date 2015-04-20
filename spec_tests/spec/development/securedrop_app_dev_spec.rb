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

securedrop_app_directories = [
  TEST_VARS['securedrop_data'],
  "#{TEST_VARS['securedrop_data']}/keys",
  "#{TEST_VARS['securedrop_data']}/tmp",
  "#{TEST_VARS['securedrop_data']}/store",
]
# ensure securedrop app directories exist with correct permissions
securedrop_app_directories.each do |securedrop_app_directory|
  describe file(securedrop_app_directory) do
    it { should be_directory }
    it { should be_owned_by TEST_VARS['securedrop_user'] }
    it { should be_grouped_into TEST_VARS['securedrop_user'] }
    it { should be_mode '700' }
  end
end

# /vagrant has 770 permissions, so test
# separately from the 700 permissions above
describe file(TEST_VARS['securedrop_code']) do
  it { should be_directory }
  it { should be_owned_by TEST_VARS['securedrop_user'] }
  it { should be_grouped_into TEST_VARS['securedrop_user'] }
  it { should be_mode '770' }
end

