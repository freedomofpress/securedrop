# declare desired sysctl flags
sysctl_flags = {
  'net.ipv4.tcp_max_syn_backlog' => 4096,
  'net.ipv4.tcp_syncookies' => 1,
  'net.ipv4.conf.all.rp_filter' => 1,
  'net.ipv4.conf.all.accept_source_route' => 0,
  'net.ipv4.conf.all.accept_redirects' => 0,
  'net.ipv4.conf.all.secure_redirects' => 0,
  'net.ipv4.conf.default.rp_filter' => 1,
  'net.ipv4.conf.default.accept_source_route' => 0,
  'net.ipv4.conf.default.accept_redirects' => 0,
  'net.ipv4.conf.default.secure_redirects' => 0,
  'net.ipv4.icmp_echo_ignore_broadcasts' => 1,
  'net.ipv4.ip_forward' => 0,
  'net.ipv4.conf.all.send_redirects' => 0,
  'net.ipv4.conf.default.send_redirects' => 0,
  'net.ipv6.conf.all.disable_ipv6' => 1,
  'net.ipv6.conf.default.disable_ipv6' => 1,
  'net.ipv6.conf.lo.disable_ipv6' => 1,
}
# ensure sysctl flags are set correctly
describe command('sysctl --all') do
  sysctl_flags.each do |sysctl_flag, value|
    sysctl_flag_regex = Regexp.quote("#{sysctl_flag} = #{value}")
    its(:stdout) { should match /^#{sysctl_flag_regex}$/ }
  end
end

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

describe package('ntp') do
  it { should be_installed }
end

# ensure swap space is disabled
describe command('swapon --summary') do
  # by using the `eq` operator here, we're ensuring the entirety of stdout is checked
  its(:stdout) { should eq "Filename\t\t\t\tType\t\tSize\tUsed\tPriority\n" }
  # a leading slash will indicate a fullpath to a swapfile
  its(:stdout) { should_not match /^\// }
end

