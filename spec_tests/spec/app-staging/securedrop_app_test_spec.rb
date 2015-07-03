# these checks are for the role `app-test`,
# which is different from simply `app`, which
# is tested in `securedrop_app_spec.rb`.

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

# ensure logging is enabled for source interface in staging
describe file('/var/www/source.wsgi') do
  it { should be_file }
  it { should be_owned_by 'www-data' }
  it { should be_grouped_into 'www-data' }
  it { should be_mode '640' }
  its(:content) { should match /^import logging$/ }
  its(:content) { should match /^logging\.basicConfig\(stream=sys\.stderr\)$/ }
end

# ensure app-armor profiles are in complain mode for staging
# there are two profiles that should be in complain mode:
# - usr.sbin.apache2
# - usr.sbin.tor
describe command('aa-status') do
  expected_output = <<-eos
2 profiles are in complain mode.
   /usr/sbin/apache2
   /usr/sbin/tor
eos
  its(:stdout) { should contain(expected_output) }
end
