# ensure development apt dependencies are installed
development_apt_dependencies = [
  'libssl-dev',
  'python-dev',
  'python-pip',
]
# ensure development apt dependencies are installed
development_apt_dependencies.each do |development_apt_dependency|
  describe package(development_apt_dependency) do
    it { should be_installed }
  end
end

# declare securedrop app pip requirements
# since this is the development role, the pip dependencies
# should be installed directly, rather than relying on the
# apt packages, which would clobber local changes
# versions here are intentionally hardcoded
pip_requirements = [
  'Flask-Testing==0.4.2',
  'Flask==0.10.1',
  'Jinja2==2.8',
  'MarkupSafe==0.23',
  'Werkzeug==0.11.9',
  'beautifulsoup4==4.4.1',
  'click==6.6',
  'coverage==4.2',
  'first==2.0.1',
  'funcsigs==1.0.2',
  'itsdangerous==0.24',
  'mock==2.0.0',
  'pbr==1.9.1',
  'pip-tools==1.6.5',
  'py==1.4.31',
  'pytest-cov==2.3.1',
  'pytest==2.9.1',
  'selenium==2.53.6',
  'six==1.10.0',
]
# ensure securedrop app pip requirements are installed
describe command('pip freeze') do
  pip_requirements.each do |pip_requirement|
    its(:stdout) { should contain(pip_requirement) }
  end
end

# ensure that the SECUREDROP_ENV var is set to "dev"
# TODO: this isn't really checking that the env var is set,
# just that it's declared in the bashrc. spec_helper ignores
# env vars via ssh by default, so start there.
describe file('/home/vagrant/.bashrc') do
  it { should be_file }
  it { should be_owned_by 'vagrant' }
  its(:content) { should match /^export SECUREDROP_ENV=dev$/ }
end

