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

