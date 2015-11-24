
# Ensure development apt dependencies are installed.
# These packages are not marked as dependencies of the SecureDrop app code,
# but are apparently vital for packaging. The build will succeed without them!
# But the package installation will fail when the postinst hook runs.
#
# When `libssl-dev` is missing:
#   Could not find any downloads that satisfy the requirement scrypt==0.6.1
#
# When `python-dev` is missing:
#   Could not find any downloads that satisfy the requirement psutil==0.2.2
property['development_apt_dependencies'].each do |development_apt_dependency|
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
  "/tmp/securedrop-ossec-agent-#{property['ossec_version']}+#{property['securedrop_app_code_version']}-amd64/",
  "/tmp/securedrop-ossec-server-#{property['ossec_version']}+#{property['securedrop_app_code_version']}-amd64/",
]
# ensure required directories exist
required_directories.each do |required_directory|
  describe file(required_directory) do
    it { should be_directory }
  end
end

# declare filenames for built debs
wanted_debs = [
  { "path" => "/tmp/securedrop-app-code-#{property['securedrop_app_code_version']}-amd64.deb",
    "dependencies" => %w( python-pip apparmor-utils gnupg2 haveged python python-pip secure-delete sqlite apache2-mpm-worker libapache2-mod-wsgi libapache2-mod-xsendfile redis-server supervisor ),
  },
  { "path" => "/tmp/securedrop-ossec-agent-#{property['ossec_version']}+#{property['securedrop_app_code_version']}-amd64.deb",
    "dependencies" => %w(ossec-agent),
  },
  { "path" => "/tmp/securedrop-ossec-server-#{property['ossec_version']}+#{property['securedrop_app_code_version']}-amd64.deb",
    "dependencies" => %w(ossec-server),
  },
]
wanted_debs.each do |wanted_deb|
  # ensure required debs exist
  describe file(wanted_deb['path']) do
    it { should be_file }
  end

  # get file basename of package, stripping leading dirs
  deb_basename = File.basename(wanted_deb['path'])

  # cut up filename to extract package name
  # this garish regex finds just the package name and strips the version info, e.g.
  # from 'securedrop-ossec-agent-2.8.1+0.3.1-amd64.deb' it will return
  # 'securedrop-ossec-agent'
  package_name = deb_basename.scan(/^([a-z\-]+(?!\d))/)[0][0].to_s

  # ensure required debs appear installable
  describe command("dpkg --install --dry-run #{wanted_deb['path']}") do
    its(:exit_status) { should eq 0 }
    its(:stdout) { should contain("Selecting previously unselected package #{package_name}.") }
#    its(:stdout) { should contain("Preparing to unpack #{deb_basename} ...")}
  end

  # Ensure control fields are populated as expected
  describe command("dpkg-deb --field #{wanted_deb['path']}") do
    its(:exit_status) { should eq 0 }
    its(:stdout) { should contain("Maintainer: SecureDrop Team <securedrop@freedom.press>") }
    its(:stdout) { should contain("Homepage: https://securedrop.org") }
    its(:stdout) { should contain("Package: #{package_name}")}
    its(:stdout) { should contain("Architecture: amd64") }
    its(:stdout) { should contain("Depends: #{wanted_deb['dependencies'].join(',')}")}
  end

  describe command("dpkg --contents #{wanted_deb['path']}") do
    # Regression test to ensure that umask is set correctly in the build scripts.
    # All files in the deb package should be root-owned.
    its(:stdout) { should_not contain("vagrant") }

    # Regression test to ensure that AppArmor profiles are embedded in the package.
    # Actual contents out of the profiles and output from `aa-status` checked in the
    # spectests for AppArmor profiles.
    if package_name == "securedrop-app-code"
      its(:stdout) { should contain("etc/apparmor.d/usr.sbin.apache2") }
      its(:stdout) { should contain("etc/apparmor.d/usr.sbin.tor") }
    end
  end
end
