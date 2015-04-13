# ensure sudoers file is present
['/etc/sudoers', '/etc/sudoers.tmp'].each do |sudoers|
  describe file(sudoers) do
    it { should be_mode '440' }
    it { should be_readable.by_user('root') }
    it { should_not be_readable.by('others') }
    its(:content) { should match /^Defaults\s+env_reset$/ }
    its(:content) { should match /^Defaults\s+mail_badpass$/ }
    its(:content) { should contain('Defaults\s+secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"') }
    its(:content) { should match /^%sudo\s+ALL=\(ALL\)\s+NOPASSWD:\s+ALL$/ }
    its(:content) { should contain('Defaults:%sudo\s+!requiretty') }
  end
end

