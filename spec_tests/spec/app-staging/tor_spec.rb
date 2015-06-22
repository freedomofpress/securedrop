# declare app-staging torrc settings
torrc_settings = [
  'HiddenServiceDir /var/lib/tor/services/source',
  'HiddenServicePort 80 127.0.0.1:80',
  'HiddenServiceDir /var/lib/tor/services/document',
  'HiddenServicePort 80 127.0.0.1:8080',
  'HiddenServiceAuthorizeClient stealth journalist',
]
# ensure torrc for app-staging host contains entries
# for both journalist and source ATHSes. the admin
# ATHS and other settings are already checked as part of the
# common-staging serverspec tests
describe file('/etc/tor/torrc') do
  torrc_settings.each do |torrc_setting|
    torrc_setting_regex = Regexp.quote(torrc_setting)
    its(:content) { should match /^#{torrc_setting_regex}$/ }
  end
end

# declare app-specific tor service directories,
# for mode and ownership checks. the parent dir
# and the "ssh" service are validated in the
# common-staging spectests.
tor_service_directories = %w(
  /var/lib/tor/services/document
  /var/lib/tor/services/source
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
