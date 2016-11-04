# ensure tor repo is present
describe file('/etc/apt/sources.list.d/deb_torproject_org_torproject_org.list') do
  repo_regex = Regexp.quote('deb http://deb.torproject.org/torproject.org trusty main')
  its(:content) { should match /^#{repo_regex}$/ }
end

# ensure packages from tor repo are installed
['deb.torproject.org-keyring', 'tor'].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

# declare common settings for torrc
torrc_settings = [
  'SocksPort 0',
  'SafeLogging 1',
  'RunAsDaemon 1',
  'Sandbox 1',
  'HiddenServiceDir /var/lib/tor/services/ssh',
  'HiddenServicePort 22 127.0.0.1:22',
  'HiddenServiceAuthorizeClient stealth admin',
]
# ensure common settings are present in torrc
# these settings should exist in both app-staging and mon-staging
describe file('/etc/tor/torrc') do
  it { should be_file }
  it { should be_mode '644' }
  it { should be_owned_by 'debian-tor' }
  torrc_settings.each do |torrc_setting|
    torrc_setting_regex = Regexp.quote(torrc_setting)
    its(:content) { should match /^#{torrc_setting_regex}$/ }
  end
end

# declare tor service directories, for mode and ownership checks
tor_service_directories = %w(
  /var/lib/tor/services
  /var/lib/tor/services/ssh
)
# ensure tor service dirs are owned by tor user and mode 0700
tor_service_directories.each do |tor_service_directory|
  describe file(tor_service_directory) do
    it { should be_directory  }
    it { should be_mode('700')  }
    it { should be_owned_by 'debian-tor' }
    it { should be_grouped_into 'debian-tor' }
  end
end

# ensure tor service is running
describe service('tor') do
  it { should be_running }
  it { should be_enabled }
end

# Likely overkill
describe command('service tor status') do
  its(:exit_status) { should eq 0 }
  its(:stdout) { should match /tor is running/ }
end

# ensure tor repo gpg key matches
describe command('apt-key finger') do
  tor_gpg_pub_key_info = '/etc/apt/trusted.gpg.d/deb.torproject.org-keyring.gpg
-----------------------------------------------------
pub   2048R/886DDD89 2009-09-04 [expires: 2020-08-29]
      Key fingerprint = A3C4 F0F9 79CA A22C DBA8  F512 EE8C BC9E 886D DD89
uid                  deb.torproject.org archive signing key
sub   2048R/219EC810 2009-09-04 [expires: 2018-08-30]'

  # Using Regexp.quote() to escape regex special chars such as [].
  its(:stdout) { should contain(Regexp.quote(tor_gpg_pub_key_info)) }
end
