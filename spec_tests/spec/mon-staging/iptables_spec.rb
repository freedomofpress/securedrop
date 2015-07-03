# declare desired iptables rules
# These rules should be present in prod and staging
# TODO: There are also hardcoded IP addresses in this section.
# These rules were exported from a fully provisioned
# mon-staging host running the develop branch around 2015-04-10.
# That means they are post-0.3.2 and therefore may need to be tweaked
# to test older versions.
desired_iptables_rules = [
  '-A INPUT -p udp -m udp --sport 53 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT',
  '-A INPUT -p tcp -m tcp --dport 22 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT',
  '-A INPUT -p tcp -m state --state RELATED,ESTABLISHED -m comment --comment "Allow traffic back for tor" -j ACCEPT',
  '-A INPUT -s 8.8.8.8/32 -p tcp -m tcp --sport 53 -m state --state RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT',
  '-A INPUT -s 8.8.8.8/32 -p udp -m udp --sport 53 -m state --state RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT',
  '-A INPUT -p udp -m udp --sport 123 --dport 123 -m state --state RELATED,ESTABLISHED -m comment --comment ntp -j ACCEPT',
  '-A INPUT -p tcp -m multiport --sports 80,8080,443 -m state --state RELATED,ESTABLISHED -m comment --comment "apt updates" -j ACCEPT',
  "-A INPUT -s #{property['app_ip']}/32 -p udp -m udp --dport 1514 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment \"Allow OSSEC agent to monitor\" -j ACCEPT",
  '-A INPUT -p tcp -m tcp --sport 587 -m state --state RELATED,ESTABLISHED -m comment --comment "Allow ossec email alerts out" -j ACCEPT',
  '-A INPUT -i lo -m comment --comment "Allow lo to lo traffic all protocols" -j ACCEPT',
  '-A INPUT -p tcp -m state --state INVALID -m comment --comment "drop but do not log inbound invalid state packets" -j DROP',
  '-A INPUT -m comment --comment "Log and drop all other incomming traffic" -j LOGNDROP',
  '-A OUTPUT -p udp -m udp --dport 53 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT',
  '-A OUTPUT -p tcp -m tcp --sport 22 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT',
  "-A OUTPUT -p tcp -m owner --uid-owner #{property['tor_user_uid']} -m state --state NEW,RELATED,ESTABLISHED -m comment --comment \"Allow Tor out\" -j ACCEPT",
  "-A OUTPUT -o lo -p tcp -m tcp --dport 22 -m owner --uid-owner #{property['tor_user_uid']} -m state --state NEW -m limit --limit 3/min --limit-burst 3 -m comment --comment \"SSH with rate limiting only thur tor\" -j ACCEPT",
  "-A OUTPUT -o lo -p tcp -m tcp --dport 22 -m owner --uid-owner #{property['tor_user_uid']} -m state --state RELATED,ESTABLISHED -m comment --comment \"SSH with rate limiting only thur tor\" -j ACCEPT",
  "-A OUTPUT -m owner --uid-owner #{property['tor_user_uid']} -m comment --comment \"Drop all other traffic for the tor instance used for ssh\" -j LOGNDROP",
  "-A OUTPUT -m owner --gid-owner #{property['ssh_group_gid']} -m comment --comment \"Drop all other outbound traffic for ssh user\" -j LOGNDROP",
  '-A OUTPUT -d 8.8.8.8/32 -p tcp -m tcp --dport 53 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT',
  '-A OUTPUT -d 8.8.8.8/32 -p udp -m udp --dport 53 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT',
  '-A OUTPUT -p udp -m udp --sport 123 --dport 123 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment ntp -j ACCEPT',
  '-A OUTPUT -p tcp -m multiport --dports 80,8080,443 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "apt updates" -j ACCEPT',
  "-A OUTPUT -d #{property['app_ip']}/32 -p udp -m udp --sport 1514 -m state --state RELATED,ESTABLISHED -m comment --comment \"Allow OSSEC agent to monitor\" -j ACCEPT",
  "-A OUTPUT -d 8.8.8.8/32 -p tcp -m tcp --dport 53 -m owner --uid-owner #{property['postfix_user_uid']} -m state --state NEW,RELATED,ESTABLISHED -m comment --comment \"postfix dns rule\" -j ACCEPT",
  "-A OUTPUT -d 8.8.8.8/32 -p udp -m udp --dport 53 -m owner --uid-owner #{property['postfix_user_uid']} -m state --state NEW,RELATED,ESTABLISHED -m comment --comment \"postfix dns rule\" -j ACCEPT",
  "-A OUTPUT -p tcp -m tcp --dport 587 -m owner --uid-owner #{property['postfix_user_uid']} -m state --state NEW,RELATED,ESTABLISHED -m comment --comment \"Allow ossec email alerts out\" -j ACCEPT",
  '-A OUTPUT -o lo -m comment --comment "Allow lo to lo traffic all protocols" -j ACCEPT',
  '-A OUTPUT -m comment --comment "Drop all other outgoing traffic" -j DROP',
  '-A LOGNDROP -p tcp -m limit --limit 5/min -j LOG --log-tcp-options --log-ip-options --log-uid',
  '-A LOGNDROP -p udp -m limit --limit 5/min -j LOG --log-ip-options --log-uid',
  '-A LOGNDROP -p icmp -m limit --limit 5/min -j LOG --log-ip-options --log-uid',
  '-A LOGNDROP -j DROP',
]

# declare unwanted iptables rules
# These rules should have been removed by the `remove_authd_exceptions` role
# TODO: The Vagrantfile virtualbox static IP was hardcoded into the two rules
# below. This will need to be fixed. Possibly with using something like
# https://github.com/volanja/ansible_spec Using the values for IP addresses
# from the ansible inventory should cover most use cases (except inventories
# with just the *.onion addresses).
unwanted_iptables_rules = [
  "-A INPUT -s #{property['app_ip']} -p tcp --sport 1515 -m state --state ESTABLISHED,RELATED -v ACCEPT -m comment --comment \"ossec authd rule only required for initial agent registration\"",
  "-A OUTPUT -d #{property['app_ip']} -p tcp --dport 1515 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT -m comment --comment \"ossec authd rule only required for initial agent registration\"",
  "-A INPUT -s #{property['app_ip']} -p tcp --dport 1515 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT",
  "-A OUTPUT -d #{property['app_ip']} -p tcp --sport 1515 -m state --state ESTABLISHED,RELATED -j ACCEPT",
]

# check for wanted and unwanted iptables rules
describe iptables do
  unwanted_iptables_rules.each do |unwanted_iptables_rule|
    it { should_not have_rule(unwanted_iptables_rule) }
  end

  desired_iptables_rules.each do |desired_iptables_rule|
    it { should have_rule(desired_iptables_rule) }
  end
end
