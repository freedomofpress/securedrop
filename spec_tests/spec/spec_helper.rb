require 'serverspec'
require 'net/ssh'
require 'tempfile'
require 'yaml'

set :backend, :ssh

host = ENV['TARGET_HOST']

# Determine SSH config for this host.
config = Tempfile.new('', Dir.tmpdir)
config.write(`vagrant ssh-config #{host}`)
config.close
options = Net::SSH::Config.for(host, [config.path])
options[:user]
set :host,        options[:host_name] || host
set :ssh_options, options


# Given a hostname, return dynamic variables for spectests.
# Variables include entries hard-coded in a YAML file specifically
# for spectests, as well as values retrieved from VMs over SSH.
def retrieve_vars(hostname)

  # Accept basename for vars YAML file,
  # then return a hash of those settings.
  def read_vars_file(file_basename)
    vars_filepath = File.expand_path(File.join(
      File.dirname(__FILE__), 'vars', "#{file_basename}.yml"
    ))
    return YAML.load_file(vars_filepath)
  end
  # This clunky if statement ain't pretty, but it gets the job done.
  # A case statement assumes only one permissible match, whereas many
  # matches should be able to add variables before this function returns.
  if hostname.match(/^development$/)
    vars = read_vars_file('development')
  end
  if hostname.match(/-staging$/)
    vars = read_vars_file('staging')
    # Ideally these IP addresses would be cached, since they don't
    # change during a test run. Right now, both values are looked up twice,
    # once for each app/mon host.
    vars['app_ip'] = retrieve_ip_addr('app-staging')
    vars['monitor_ip'] = retrieve_ip_addr('mon-staging')
  end
  if hostname.match(/-prod$/)
    vars = read_vars_file('prod')
    vars['app_ip'] = retrieve_ip_addr('app-prod')
    vars['monitor_ip'] = retrieve_ip_addr('mon-prod')
  end
  if hostname.match(/^(app|mon)/)
    vars['tor_user_uid'] = vagrant_ssh_cmd(hostname, "id -u debian-tor")
    vars['ssh_group_gid'] = vagrant_ssh_cmd(hostname, "getent group ssh | cut -d: -f3")
  end
  if hostname.match(/^app/)
    vars['apache_user_uid'] = vagrant_ssh_cmd(hostname, "id -u www-data")
  end
  if hostname.match(/^mon/)
    vars['postfix_user_uid'] = vagrant_ssh_cmd(hostname, "id -u postfix")
  end
  if hostname.match(/^build$/)
    vars = read_vars_file('build')
  end
  return vars
end

# SSH into Vagrant machine, run command, return output.
def vagrant_ssh_cmd(hostname, command)
  # Dump STDERR, to avoid noisy "Connection closed" messages.
  # Error code is checked below.
  filter_stderr = "2> /dev/null"
  vagrant_cmd = "vagrant ssh #{hostname} --command '#{command}'"
  result = `#{vagrant_cmd} #{filter_stderr}`.rstrip
  if $? != 0
    puts "Command failed: #{vagrant_cmd}"
    exit(1)
  end
  return result
end

# Look up IP address for given hostname, so spectests
# have accurate dynamic vars regardless of provider.
def retrieve_ip_addr(hostname)
  ip_output = vagrant_ssh_cmd(hostname, "hostname -I")
  iface1, iface2 = ip_output.split()
  # Vagrant VirtualBox images will always have eth0 as the NAT device,
  # so we actually what the IP address from the eth1 device on VirtualBox hosts.
  # In other testing environments, we can assume the first address is correct.
  if `vagrant status #{hostname} --machine-readable`.match(/#{hostname},provider-name,virtualbox/m)
    return iface2
  else
    return iface1
  end
end

# Load dynamic variables for current host.
set_property retrieve_vars(host)
