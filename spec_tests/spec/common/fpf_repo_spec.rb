# ensure FPF repo is present
describe file('/etc/apt/sources.list.d/apt_freedom_press.list') do
  its(:content) { should match /^deb \[arch=amd64\] https:\/\/apt\.freedom\.press trusty main$/ }
end

# ensure FPF has correct fingerprint
describe command('apt-key export FC9F6818 | gpg --with-fingerprint --keyring /dev/null') do
  fpf_gpg_pub_key_info = 'pub  4096R/FC9F6818 2014-10-26 Freedom of the Press Foundation Master Signing Key
      Key fingerprint = B89A 29DB 2128 160B 8E4B  1B4C BADD E0C7 FC9F 6818
sub  4096R/4833B9A3 2014-10-26'
  its(:stdout) { should contain(fpf_gpg_pub_key_info) }
end
