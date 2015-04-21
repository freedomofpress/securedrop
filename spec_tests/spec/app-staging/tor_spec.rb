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

