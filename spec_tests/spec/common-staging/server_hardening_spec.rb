# ensure DNS server is named
# TODO: nameserver var is hard-coded below. consider 
# dynamically populated this var via spec_helper.
describe file('/etc/resolvconf/resolv.conf.d/base') do |resolvconf|
  it { should be_mode '644' }
  its(:content) { should match /^nameserver 8\.8\.8\.8$/ }
end


disabled_kernel_modules = [
  'bluetooth',
  'iwlwifi',
]
disabled_kernel_modules.each do |disabled_kernel_module|
  describe kernel_module(disabled_kernel_module) do
    it { should_not be_loaded }
  end
  describe file('/etc/modprobe.d/blacklist.conf') do
    its(:content) { should match /^blacklist #{disabled_kernel_module}$/ }
  end
end
  
