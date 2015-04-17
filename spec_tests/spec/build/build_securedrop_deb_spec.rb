# TODO: dynamically read the securedrop_app_code_version var
securedrop_app_code_version = "0.3.2"
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

# declare required directories
required_directories = [
#  "/tmp/build/securedrop-ossec-agent-2.8.1+#{securedrop_app_code_version}-amd64/",
#  "/tmp/build/securedrop-ossec-server-2.8.1+#{securedrop_app_code_version}-amd64/",
  '/vagrant/build',
]
# ensure required directories exist
required_directories.each do |required_directory|
  describe file(required_directory) do
    it { should be_directory }
  end
end

# declare filenames for built debs
wanted_debs = [
  "/vagrant/build/securedrop-app-code-#{securedrop_app_code_version}-amd64.deb",
  "/vagrant/build/securedrop-ossec-agent-2.8.1+#{securedrop_app_code_version}-amd64.deb",
  "/vagrant/build/securedrop-ossec-server-2.8.1+#{securedrop_app_code_version}-amd64.deb",
]
wanted_debs.each do |wanted_deb|
  # ensure required debs exist
  describe file(wanted_deb) do
    it { should be_file }
  end
end
