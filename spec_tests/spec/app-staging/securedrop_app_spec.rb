#require 'spec_helper'

# ensure default apache html directory is absent
describe command('/bin/bash -c "[[ ! -e /var/www/html  ]]"') do
  its(:exit_status) { should eq 0 }
end

# declare securedrop app directories
securedrop_app_directories = [
  '/var/www/securedrop',
  '/var/lib/securedrop',
  '/var/lib/securedrop/store',
  '/var/lib/securedrop/keys',
  '/var/lib/securedrop/tmp',
]

# ensure securedrop app directories exist with correct permissions
securedrop_app_directories.each do |securedrop_app_directory|
  describe file(securedrop_app_directory) do
    it { should be_directory }
    it { should be_owned_by  'www-data' }
    it { should be_grouped_into  'www-data' }
    it { should be_mode '700' }
  end
end

['/var/lib/securedrop','/var/lib/securedrop/store','/var/lib/securedrop/keys'].each do |myDir|
  describe file(myDir) do
    it { should be_directory }
    it { should be_owned_by  'www-data' }
    it { should be_mode '700' }
  end
end

describe file('/var/www/securedrop/config.py') do
  it { should be_file }
  it { should be_owned_by  'www-data' }
  it { should be_mode '600' }
end
