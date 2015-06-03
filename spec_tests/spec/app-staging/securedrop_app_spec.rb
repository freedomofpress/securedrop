# declare securedrop app directories
securedrop_app_directories = [
  property['securedrop_code'],
  property['securedrop_data'],
  "#{property['securedrop_data']}/store",
  "#{property['securedrop_data']}/keys",
  "#{property['securedrop_data']}/tmp",
]

# ensure securedrop app directories exist with correct permissions
securedrop_app_directories.each do |securedrop_app_directory|
  describe file(securedrop_app_directory) do
    it { should be_directory }
    it { should be_owned_by property['securedrop_user'] }
    it { should be_grouped_into property['securedrop_user'] }
    it { should be_mode '700' }
  end
end

# ensure securedrop-app-code package is installed
describe package('securedrop-app-code') do
  it { should be_installed }
end

# ensure test gpg key is present in app keyring
describe command('su -s /bin/bash -c "gpg --homedir /var/lib/securedrop/keys --list-keys 28271441" www-data') do
  its(:exit_status) { should eq 0 }
  expected_output = <<-eos
pub   4096R/28271441 2013-10-12
uid                  SecureDrop Test/Development (DO NOT USE IN PRODUCTION)
sub   4096R/A2201B2A 2013-10-12

eos
  its(:stdout) { should eq expected_output }
end

# ensure default logo header file exists
# TODO: add check for custom logo header file
describe file("#{property['securedrop_code']}/static/i/logo.png") do
  it { should be_file }
  # TODO: ansible task declares mode 400 but the file ends up as 644 on host
  it { should be_mode '644' }
  it { should be_owned_by property['securedrop_user'] }
  it { should be_grouped_into property['securedrop_user'] }
end

# ensure cronjob for securedrop tmp dir cleanup is enabled
describe cron do
  it { should have_entry "@daily #{property['securedrop_code']}/manage.py clean_tmp" }
end

# ensure directory for worker logs is present
describe file('/var/log/securedrop_worker') do
  it { should be_directory }
  it { should be_mode '644' }
  it { should be_owned_by 'root' }
  it { should be_grouped_into 'root' }
end
