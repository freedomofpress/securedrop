require 'spec_helper'


# declare required pip dependencies.
# these checks explicitly reference version number
# to make sure the stack and tests are in sync.
pip_dependencies = [
  'Flask-Testing==0.4.2',
  'mock==1.0.1',
  'pytest==2.6.4',
  'selenium==2.45.0',
]
# ensure pip depdendencies are installed in staging.
# these are required for running unit and functional tests
describe command('pip freeze') do
  pip_dependencies.each do |pip_dependency|
    its(:stdout) { should contain(pip_dependency) }
  end
end

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
