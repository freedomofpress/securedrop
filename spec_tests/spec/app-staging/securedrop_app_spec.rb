require 'spec_helper'


# ensure default apache html directory is absent
describe command('/bin/bash -c "[[ ! -e /var/www/html  ]]"') do
  its(:exit_status) { should eq 0 }
end

# declare securedrop app directories
securedrop_app_directories = [
  TEST_VARS['securedrop_code'],
  TEST_VARS['securedrop_data'],
  "#{TEST_VARS['securedrop_data']}/store",
  "#{TEST_VARS['securedrop_data']}/keys",
  "#{TEST_VARS['securedrop_data']}/tmp",
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

# ensure securedrop-app-code package is installed
describe package('securedrop-app-code') do
  it { should be_installed }
end

describe command('su -s /bin/bash -c "gpg --homedir /var/lib/securedrop/keys --import /var/lib/securedrop/test_journalist_key.pub" www-data') do
  its(:exit_status) { should eq 0 }
  expected_output = <<-eos
gpg: key 28271441: "SecureDrop Test/Development (DO NOT USE IN PRODUCTION)" not changed
gpg: Total number processed: 1
gpg:              unchanged: 1
eos
  # gpg dumps a lot of output to stderr, rather than stdout
  its(:stderr) { should eq expected_output }
end

# ensure default logo header file exists
# TODO: add check for custom logo header file
describe file("#{TEST_VARS['securedrop_code']}/static/i/logo.png") do
  it { should be_file }
  # TODO: ansible task declares mode 400 but the file ends up as 644 on host
  it { should be_mode '644' }
  it { should be_owned_by TEST_VARS['securedrop_user'] }
  it { should be_grouped_into TEST_VARS['securedrop_user'] }
end

# declare config options for securedrop worker
securedrop_worker_config_options = [
  '[program:securedrop_worker]',
  'command=/usr/local/bin/rqworker',
  "directory=#{TEST_VARS['securedrop_code']}",
  'autostart=true',
  'autorestart=true',
  'startretries=3',
  'stderr_logfile=/var/log/securedrop_worker/err.log',
  'stdout_logfile=/var/log/securedrop_worker/out.log',
  'user=www-data',
  'environment=HOME="/tmp/python-gnupg"',
]
# ensure securedrop worker config for supervisor is present
describe file('/etc/supervisor/conf.d/securedrop_worker.conf') do
  it { should be_file }
  it { should be_mode '644' }
  it { should be_owned_by 'root' }
  it { should be_grouped_into 'root' }
  securedrop_worker_config_options.each do |securedrop_worker_config_option|
    securedrop_worker_config_option_regex = Regexp.quote(securedrop_worker_config_option)
    its(:content) { should match /^#{securedrop_worker_config_option_regex}$/ }
  end
end

# ensure cronjob for securedrop tmp dir cleanup is enabled
describe cron do
  it { should have_entry "@daily #{TEST_VARS['securedrop_code']}/manage.py clean_tmp" }
end

# ensure directory for worker logs is present
describe file('/var/log/securedrop_worker') do
  it { should be_directory }
  it { should be_mode '644' }
  it { should be_owned_by 'root' }
  it { should be_grouped_into 'root' }
end
