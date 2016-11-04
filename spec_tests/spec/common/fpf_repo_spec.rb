# ensure FPF repo is present
describe file('/etc/apt/sources.list.d/apt_freedom_press.list') do
  its(:content) { should match /^deb \[arch=amd64\] https:\/\/apt\.freedom\.press trusty main$/ }
end

# ensure FPF has correct fingerprint
describe command('apt-key finger') do
  fpf_gpg_pub_key_info = '/etc/apt/trusted.gpg.d/securedrop-keyring.gpg
---------------------------------------------
pub   4096R/00F4AD77 2016-10-20 [expires: 2017-10-20]
      Key fingerprint = 2224 5C81 E3BA EB41 38B3  6061 310F 5612 00F4 AD77
uid                  SecureDrop Release Signing Key'

  # Using Regexp.quote() to escape regex special characters such as [].
  its(:stdout) { should contain(Regexp.quote(fpf_gpg_pub_key_info)) }

  fpf_gpg_pub_key_fingerprint_expired = 'B89A 29DB 2128 160B 8E4B  1B4C BADD E0C7 FC9F 6818'
  fpf_gpg_pub_key_info_expired = "pub   4096R/FC9F6818 2014-10-26 [expired: 2016-10-27]
      Key fingerprint = #{fpf_gpg_pub_key_fingerprint_expired}
uid                  Freedom of the Press Foundation Master Signing Key"

  its(:stdout) { should_not contain(Regexp.quote(fpf_gpg_pub_key_info_expired)) }
  # Extra check to for just the old fingerprint; more durable in case formatting is off.
  its(:stdout) { should_not contain(fpf_gpg_pub_key_fingerprint_expired) }
end
