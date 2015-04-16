# declare development apt dependencies for building
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

# ensure "wheel" is installed via pip
describe command('pip freeze') do
  its(:stdout) { should contain('wheel==0.24.0') }
end
