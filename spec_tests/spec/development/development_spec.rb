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
  'beautifulsoup4==4.3.2',
  'Flask-WTF==0.11',
  'Flask==0.10.1',
  'gnupg-securedrop==1.2.5-9-g6f9d63a-dirty',
  'itsdangerous==0.24',
  'Jinja2==2.7.3',
  'MarkupSafe==0.23',
  'pip-tools==0.3.5',
  'psutil==2.2.0',
  'py==1.4.26',
  'pycrypto==2.6.1',
  'pyotp==1.4.1',
  'qrcode==5.1',
  'redis==2.10.3',
  'rq==0.4.6',
  'scrypt==0.6.1',
  'six==1.9.0',
  'SQLAlchemy==0.9.8',
  'Werkzeug==0.9.6',
  'WTForms==2.0.2',
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

