# ensure logging is enabled for source interface in staging
describe file('/var/www/source.wsgi') do
  it { should be_file }
  it { should be_owned_by 'www-data' }
  it { should be_grouped_into 'www-data' }
  it { should be_mode '640' }
  its(:content) { should match /^import logging$/ }
  its(:content) { should match /^logging\.basicConfig\(stream=sys\.stderr\)$/ }
end

# ensure app-armor profiles are in complain mode for staging
# there are two profiles that should be in complain mode:
# - usr.sbin.apache2
# - usr.sbin.tor
describe command('aa-status') do
  expected_output = <<-eos
2 profiles are in complain mode.
   /usr/sbin/apache2
   /usr/sbin/tor
eos
  its(:stdout) { should contain(expected_output) }
end
