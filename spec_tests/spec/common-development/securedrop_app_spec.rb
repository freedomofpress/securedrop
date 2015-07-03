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

# ensure the securedrop application gpg pubkey is present
describe file("#{property['securedrop_data']}/test_journalist_key.pub") do
  it { should be_file }
  it { should be_owned_by 'root' }
  it { should be_grouped_into 'root' }
  it { should be_mode '644' }
end

# ensure config.py (settings for securedrop app) exists
describe file("#{property['securedrop_code']}/config.py") do
  it { should be_file }
  it { should be_owned_by property['securedrop_user'] }
  it { should be_grouped_into property['securedrop_user'] }
  it { should be_mode '600' }
  its(:content) { should match /^JOURNALIST_KEY = '65A1B5FF195B56353CC63DFFCC40EF1228271441'$/ }
end

# ensure sqlite database exists for application
describe file("#{property['securedrop_data']}/db.sqlite") do
  it { should be_file }
  # TODO: perhaps 640 perms would work here
  it { should be_mode '644' }
  it { should be_owned_by property['securedrop_user'] }
  it { should be_grouped_into property['securedrop_user'] }
end

# declare config options for securedrop worker
securedrop_worker_config_options = [
  '[program:securedrop_worker]',
  'command=/usr/local/bin/rqworker',
  "directory=#{property['securedrop_code']}",
  'autostart=true',
  'autorestart=true',
  'startretries=3',
  'stderr_logfile=/var/log/securedrop_worker/err.log',
  'stdout_logfile=/var/log/securedrop_worker/out.log',
  "user=#{property['securedrop_user']}",
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

