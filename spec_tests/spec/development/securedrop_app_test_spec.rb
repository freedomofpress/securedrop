# These checks are for the role `app-test`,
# which is different from simply `app`, which
# is tested in `securedrop_app_spec.rb`.
# TODO: the Ansible role filters tasks from the
# app-test role via the "non-development" tag.
# There should be better separation between hosts
# and roles, e.g. "development" and "app-test",
# perhaps leveraging host_vars. Fix that, then
# come back here and refactor the various versions
# of `securedrop_app_test_spec.rb`.

# ensure wsgi file is absent in development
describe file("/var/www/source.wsgi") do
  it { should_not exist }
end

# ensure app-armor profiles are NOT in complain mode
# that's only for staging. in staging, these profiles complain:
# - usr.sbin.apache2
# - usr.sbin.tor
describe command('aa-status') do
  its(:stdout) { should contain('0 profiles are in complain mode.') }
end
