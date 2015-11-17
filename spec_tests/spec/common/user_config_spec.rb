# ensure sudoers file is present
['/etc/sudoers'].each do |sudoers|
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

# ensure securedrop-specific bashrc additions are present
describe file('/etc/profile.d/securedrop_additions.sh') do
  non_interactive_str = Regexp.quote('[[ $- != *i* ]] && return')
  its(:content) { should match /^#{non_interactive_str}$/ }
  its(:content) { should match /^if which tmux >\/dev\/null 2>&1; then$/ }
  tmux_check = Regexp.quote('test -z "$TMUX" && (tmux attach || tmux new-session)')
  its(:content) { should match /^\s+#{tmux_check}$/ }
end

# TODO: 'vagrant' user only valid in local vbox environment.
# find some way to read this variable dynamically.
# probably best to parse the YAML vars file via spec_helper.rb
describe file('/home/vagrant/.bashrc') do |bashrc|
  # Regression test: SecureDrop bashrc additions were previously added to local
  # ~/.bashrc files in admin accounts, so now we're checking that the line does NOT exist.
  its(:content) { should_not match /^. \/etc\/bashrc\.securedrop_additions$/  }
end
