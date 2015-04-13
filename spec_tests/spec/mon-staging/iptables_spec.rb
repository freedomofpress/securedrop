#require 'spec_helper'

describe iptables do
  # These rules should only exist when the while the ossec agent is registering
  # with the OSSEC server and then should be removed prior to the playbook
  # finishing
  # TODO: The Vagrantfile virtualbox static IP was hardcoded into the two rules
  # below. This will need to be fixed. Possibly with using something like
  # https://github.com/volanja/ansible_spec Using the values for IP addresses
  # from the ansible inventory should cover most use cases. (except inventories
  # with just the *.onion address.
  it { should_not have_rule(' OUTPUT -d 10.0.1.3 -p tcp --dport 1515 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT -m comment --comment "ossec authd rule only required for initial agent registration"') }
  it { should_not have_rule(' INPUT -s 10.0.1.3 -p tcp --sport 1515 -m state --state ESTABLISHED,RELATED -v ACCEPT -m comment --comment "ossec authd rule only required for initial agent registration"') }

  # These rules should be present in prod and staging
  # TODO: There are also hardcoded IP addresses in this section.
  # These rules were exported from a fully provisioned
  # mon-staging host running the develop branch around 2015-04-10.
  # That means they are post-0.3.2 and therefore may need to be tweaked
  # to test older versions.
  it { should have_rule('-A INPUT -p udp -m udp --sport 53 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') } 
  it { should have_rule('-A INPUT -p tcp -m tcp --dport 22 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') } 
  it { should have_rule('-A INPUT -p tcp -m state --state RELATED,ESTABLISHED -m comment --comment "Allow traffic back for tor" -j ACCEPT') } 
  it { should have_rule('-A INPUT -s 8.8.8.8/32 -p tcp -m tcp --sport 53 -m state --state RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT') } 
  it { should have_rule('-A INPUT -s 8.8.8.8/32 -p udp -m udp --sport 53 -m state --state RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT') } 
  it { should have_rule('-A INPUT -p udp -m udp --sport 123 --dport 123 -m state --state RELATED,ESTABLISHED -m comment --comment ntp -j ACCEPT') } 
  it { should have_rule('-A INPUT -p tcp -m multiport --sports 80,8080,443 -m state --state RELATED,ESTABLISHED -m comment --comment "apt updates" -j ACCEPT') } 
  it { should have_rule('-A INPUT -s 10.0.1.2/32 -p udp -m udp --dport 1514 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "Allow OSSEC agent to monitor" -j ACCEPT') } 
  it { should have_rule('-A INPUT -p tcp -m tcp --sport 587 -m state --state RELATED,ESTABLISHED -m comment --comment "Allow ossec email alerts out" -j ACCEPT') } 
  it { should have_rule('-A INPUT -i lo -m comment --comment "Allow lo to lo traffic all protocols" -j ACCEPT') } 
  it { should have_rule('-A INPUT -p tcp -m state --state INVALID -m comment --comment "drop but do not log inbound invalid state packets" -j DROP') } 
  it { should have_rule('-A INPUT -m comment --comment "Log and drop all other incomming traffic" -j LOGNDROP') } 
  it { should have_rule('-A INPUT -s 10.0.1.2/32 -p udp -m udp --dport 1514 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "Allow OSSEC agent to monitor" -j ACCEPT') }
  it { should have_rule('-A OUTPUT -d 10.0.1.2/32 -p udp -m udp --sport 1514 -m state --state RELATED,ESTABLISHED -m comment --comment "Allow OSSEC agent to monitor" -j ACCEPT') }
  it { should have_rule('-A OUTPUT -p udp -m udp --dport 53 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -p tcp -m tcp --sport 22 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -p tcp -m owner --uid-owner 109 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "Allow Tor out" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -o lo -p tcp -m tcp --dport 22 -m owner --uid-owner 109 -m state --state NEW -m limit --limit 3/min --limit-burst 3 -m comment --comment "SSH with rate limiting only thur tor" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -o lo -p tcp -m tcp --dport 22 -m owner --uid-owner 109 -m state --state RELATED,ESTABLISHED -m comment --comment "SSH with rate limiting only thur tor" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -m owner --uid-owner 109 -m comment --comment "Drop all other traffic for the tor instance used for ssh" -j LOGNDROP') } 
  it { should have_rule('-A OUTPUT -m owner --gid-owner 108 -m comment --comment "Drop all other outbound traffic for ssh user" -j LOGNDROP') } 
  it { should have_rule('-A OUTPUT -d 8.8.8.8/32 -p tcp -m tcp --dport 53 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -d 8.8.8.8/32 -p udp -m udp --dport 53 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -p udp -m udp --sport 123 --dport 123 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment ntp -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -p tcp -m multiport --dports 80,8080,443 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "apt updates" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -d 10.0.1.2/32 -p udp -m udp --sport 1514 -m state --state RELATED,ESTABLISHED -m comment --comment "Allow OSSEC agent to monitor" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -d 8.8.8.8/32 -p tcp -m tcp --dport 53 -m owner --uid-owner 110 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "postfix dns rule" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -d 8.8.8.8/32 -p udp -m udp --dport 53 -m owner --uid-owner 110 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "postfix dns rule" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -p tcp -m tcp --dport 587 -m owner --uid-owner 110 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "Allow ossec email alerts out" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -o lo -m comment --comment "Allow lo to lo traffic all protocols" -j ACCEPT') } 
  it { should have_rule('-A OUTPUT -m comment --comment "Drop all other outgoing traffic" -j DROP') } 
  it { should have_rule('-A LOGNDROP -p tcp -m limit --limit 5/min -j LOG --log-tcp-options --log-ip-options --log-uid') } 
  it { should have_rule('-A LOGNDROP -p udp -m limit --limit 5/min -j LOG --log-ip-options --log-uid') } 
  it { should have_rule('-A LOGNDROP -p icmp -m limit --limit 5/min -j LOG --log-ip-options --log-uid') } 
  it { should have_rule('-A LOGNDROP -j DROP') } 
end
