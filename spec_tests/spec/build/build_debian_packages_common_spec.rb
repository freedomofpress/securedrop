
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
