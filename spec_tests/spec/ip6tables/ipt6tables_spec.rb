# All servers should have default DROP chains
# for IPv6 iptables rules. Therefore the ip6tables
# spec tests are isolated in a separate directory,
# for easy reuse among hosts.

# Declare exact output for ip6tables-save
desired_ip6tables_output = <<END_IPV6_TABLE_RULES
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT DROP [0:0]
COMMIT
END_IPV6_TABLE_RULES
# Check for DROP rules on ip6tables.
# serverspec does have support for the 'ip6tables' type,
# but that doesn't ensure rule order. Since the expected IPv6 rules
# are simply default DROP rules for default chains,
# check for the exact output. Make sure to filter out first and
# last lines, which are just comments with the date.
describe command("ip6tables-save | sed '1d;$d'") do
  its(:stdout) { should eq desired_ip6tables_output }
end

