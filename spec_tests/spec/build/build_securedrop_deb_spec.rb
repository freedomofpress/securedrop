# TODO: dynamically read the securedrop_app_code_version var
securedrop_app_code_version = "0.3.6"
ossec_version = "2.8.2"

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
  "/tmp/build/securedrop-ossec-agent-#{ossec_version}+#{securedrop_app_code_version}-amd64/",
  "/tmp/build/securedrop-ossec-server-#{ossec_version}+#{securedrop_app_code_version}-amd64/",
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
  "/vagrant/build/securedrop-ossec-agent-#{ossec_version}+#{securedrop_app_code_version}-amd64.deb",
  "/vagrant/build/securedrop-ossec-server-#{ossec_version}+#{securedrop_app_code_version}-amd64.deb",
]
wanted_debs.each do |wanted_deb|
  # ensure required debs exist
  describe file(wanted_deb) do
    it { should be_file }
  end

  # get file basename of package, stripping leading dirs
  deb_basename = File.basename(wanted_deb)

  # cut up filename to extract package name
  # this garish regex finds just the package name and strips the version info, e.g.
  # from 'securedrop-ossec-agent-2.8.1+0.3.1-amd64.deb' it will return
  # 'securedrop-ossec-agent'
  package_name = deb_basename.scan(/^([a-z\-]+(?!\d))/)[0][0].to_s

  # ensure required debs appear installable
  describe command("dpkg --install --dry-run #{wanted_deb}") do
    its(:exit_status) { should eq 0 }
    its(:stdout) { should contain("Selecting previously unselected package #{package_name}.") }
#    its(:stdout) { should contain("Preparing to unpack #{deb_basename} ...")}
  end

  # ensure control fields are populated as expected
  # TODO: these checks are rather superficial, and don't actually confirm that the
  # .deb files are not broken. at a later date, consider integration tests
  # that actually use these built files during an ansible provisioning run.
  describe command("dpkg-deb --field #{wanted_deb}") do
    its(:exit_status) { should eq 0 }
    its(:stdout) { should contain("Maintainer: SecureDrop Team <securedrop@freedom.press>") }
    its(:stdout) { should contain("Homepage: https://securedrop.org") }
    its(:stdout) { should contain("Package: #{package_name}")}
    its(:stdout) { should contain("Architecture: amd64") }
  end
end
