require 'spec_helper'


# these checks are for the role `app-test`,
# which is different from simply `app`, which
# is tested in `securedrop_app_spec.rb`.
# the development machine should NOT have these files

# ensure wsgi file is absent in development
describe command("/bin/bash -c '[[ ! -e /var/www/source.wsgi ]]'") do
  its(:exit_status) { should eq 0 }
end

# ensure app-armor profiles are NOT in complain mode
# that's only for staging. in staging, these profiles complain:
# - usr.sbin.apache2
# - usr.sbin.tor
describe command('aa-status') do
  its(:stdout) { should contain('0 profiles are in complain mode.') }
end
