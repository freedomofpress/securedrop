require 'spec_helper'

describe iptables do
  it { should have_rule(' INPUT -p tcp -m tcp --dport 8080 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') }
  it { should have_rule(' INPUT -p tcp -m tcp --dport 80 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') }
  it { should have_rule(' INPUT -p udp -m udp --sport 53 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') }
  it { should have_rule(' INPUT -p tcp -m tcp --dport 22 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') }
  it { should have_rule(' INPUT -p tcp -m state --state RELATED,ESTABLISHED -m comment --comment "Allow traffic back for tor" -j ACCEPT') }
  it { should have_rule(' INPUT -i lo -p tcp -m tcp --dport 80 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "Allow tor connection from local loopback to connect to source int" -j ACCEPT') }
  it { should have_rule(' INPUT -i lo -p tcp -m tcp --dport 8080 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "Allow tor connection from local loopback to connect to document int" -j ACCEPT') }
  it { should have_rule(' INPUT -s 127.0.0.1/32 -d 127.0.0.1/32 -i lo -p tcp -m state --state RELATED,ESTABLISHED -m comment --comment "for redis worker all application user local loopback user" -j ACCEPT') }
  it { should have_rule(' INPUT -s 8.8.8.8/32 -p tcp -m tcp --sport 53 -m state --state RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT') }
  it { should have_rule(' INPUT -s 8.8.8.8/32 -p udp -m udp --sport 53 -m state --state RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT') }
  it { should have_rule(' INPUT -p udp -m udp --sport 123 --dport 123 -m state --state RELATED,ESTABLISHED -m comment --comment ntp -j ACCEPT') }
  it { should have_rule(' INPUT -p tcp -m multiport --sports 80,8080,443 -m state --state RELATED,ESTABLISHED -m comment --comment "apt updates" -j ACCEPT') }
  it { should have_rule(' INPUT -s 10.0.1.3/32 -p udp -m udp --sport 1514 -m state --state RELATED,ESTABLISHED -m comment --comment "OSSEC server agent" -j ACCEPT') }
  it { should have_rule(' INPUT -i lo -m comment --comment "Allow lo to lo traffic all protocols" -j ACCEPT') }
  it { should have_rule(' INPUT -p tcp -m state --state INVALID -m comment --comment "drop but do not log inbound invalid state packets" -j DROP') }
  it { should have_rule(' INPUT -m comment --comment "Drop and log all other incomming traffic" -j LOGNDROP') }
  it { should have_rule(' OUTPUT -p tcp -m tcp --sport 8080 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') }
  it { should have_rule(' OUTPUT -p tcp -m tcp --sport 80 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') }
  it { should have_rule(' OUTPUT -p udp -m udp --dport 53 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') }
  it { should have_rule(' OUTPUT -p tcp -m tcp --sport 22 -m state --state NEW,RELATED,ESTABLISHED -j ACCEPT') }
  it { should have_rule(' OUTPUT -p tcp -m owner --uid-owner 109 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "tor instance that provides ssh access" -j ACCEPT') }
  it { should have_rule(' OUTPUT -o lo -p tcp -m tcp --dport 22 -m owner --uid-owner 109 -m state --state NEW -m limit --limit 3/min --limit-burst 3 -m comment --comment "SSH with rate limiting only thru tor" -j ACCEPT') }
  it { should have_rule(' OUTPUT -o lo -p tcp -m tcp --dport 22 -m owner --uid-owner 109 -m state --state RELATED,ESTABLISHED -m comment --comment "SSH with rate limiting only thru tor" -j ACCEPT') }
  it { should have_rule(' OUTPUT -m owner --uid-owner 109 -m comment --comment "Drop all other traffic for the tor instance used for ssh" -j LOGNDROP') }
  it { should have_rule(' OUTPUT -o lo -p tcp -m tcp --sport 80 -m owner --uid-owner 33 -m state --state RELATED,ESTABLISHED -m comment --comment "Restrict the apache user outbound connections" -j ACCEPT') }
  it { should have_rule(' OUTPUT -o lo -p tcp -m tcp --sport 8080 -m owner --uid-owner 33 -m state --state RELATED,ESTABLISHED -m comment --comment "Restrict the apache user outbound connections" -j ACCEPT') }
  it { should have_rule(' OUTPUT -s 127.0.0.1/32 -d 127.0.0.1/32 -o lo -p tcp -m owner --uid-owner 33 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "for redis worker all application user local loopback user" -j ACCEPT') }
  it { should have_rule(' OUTPUT -m owner --uid-owner 33 -m comment --comment "Drop all other traffic by the securedrop user" -j LOGNDROP') }
  it { should have_rule(' OUTPUT -m owner --gid-owner 108 -m comment --comment "Drop all other outbound traffic for ssh user" -j LOGNDROP') }
  it { should have_rule(' OUTPUT -d 8.8.8.8/32 -p tcp -m tcp --dport 53 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT') }
  it { should have_rule(' OUTPUT -d 8.8.8.8/32 -p udp -m udp --dport 53 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "tcp/udp dns" -j ACCEPT') }
  it { should have_rule(' OUTPUT -p udp -m udp --sport 123 --dport 123 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment ntp -j ACCEPT') }
  it { should have_rule(' OUTPUT -p tcp -m multiport --dports 80,8080,443 -m owner --uid-owner 0 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "apt updates" -j ACCEPT') }
  it { should have_rule(' OUTPUT -d 10.0.1.3/32 -p udp -m udp --dport 1514 -m state --state NEW,RELATED,ESTABLISHED -m comment --comment "OSSEC server agent" -j ACCEPT') }
  it { should have_rule(' OUTPUT -o lo -m comment --comment "Allow lo to lo traffic all protocols" -j ACCEPT') }
  it { should have_rule(' OUTPUT -m comment --comment "Drop all other outgoing traffic" -j DROP') }
  it { should have_rule(' LOGNDROP -p tcp -m limit --limit 5/min -j LOG --log-tcp-options --log-ip-options --log-uid') }
  it { should have_rule(' LOGNDROP -p udp -m limit --limit 5/min -j LOG --log-ip-options --log-uid') }
  it { should have_rule(' LOGNDROP -p icmp -m limit --limit 5/min -j LOG --log-ip-options --log-uid') }
  it { should have_rule(' LOGNDROP -j DROP') }
end
