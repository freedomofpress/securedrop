# Declare desired iptables rules
# The 'development' machine doesn't have any custom
# iptables rules, so just check for the default chains.
desired_iptables_rules = [
  '-P INPUT ACCEPT',
  '-P FORWARD ACCEPT',
  '-P OUTPUT ACCEPT',
]

# check for wanted and unwanted iptables rules
describe iptables do
  desired_iptables_rules.each do |desired_iptables_rule|
    it { should have_rule(desired_iptables_rule) }
  end
end

# if any iptables rules are ever added, this test will
# fail, so tests can be written for the new rules.
describe command('iptables -S | wc -l') do
  its(:stdout) { should eq desired_iptables_rules.length.to_s + "\n" }
end

# check for ssh listening (this really shouldn't ever fail)
describe port(22) do
  it { should be_listening.on('0.0.0.0').with('tcp') }
end

# check for ssh listening (this really shouldn't ever fail)
describe port(22) do
  it { should be_listening.on('0.0.0.0').with('tcp') }
end

# check for redis worker port listening
describe port(6379) do
  it { should be_listening.on('127.0.0.1').with('tcp') }
end

# The Flask runners for the source and journalist interfaces
# aren't configured to run by default, e.g. on boot. Nor
# do the app tests cause them to be run. So, we shouldn't
# really expected them to be running.
## check for source interface flask port listening
#describe port(8080) do
#  it { should be_listening.on('0.0.0.0').with('tcp') }
#end
#
## check for journalist interface flask port listening
#describe port(8081) do
#  it { should be_listening.on('0.0.0.0').with('tcp') }
#end
