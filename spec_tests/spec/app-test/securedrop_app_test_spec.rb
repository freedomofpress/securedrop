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

