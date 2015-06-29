require 'serverspec'
require 'net/ssh'
require 'tempfile'
require 'yaml'

set :backend, :ssh

if ENV['ASK_SUDO_PASSWORD']
  begin
    require 'highline/import'
  rescue LoadError
    fail "highline is not available. Try installing it."
  end
  set :sudo_password, ask("Enter sudo password: ") { |q| q.echo = false }
else
  set :sudo_password, ENV['SUDO_PASSWORD']
end

host = ENV['TARGET_HOST']

# Using backticks for a subprocess call means
# STDOUT will be masked, which blocks silently for
# a long time if the host isn't up. Using IO.popen
# instead allows for a tee-like interface
#`vagrant up #{host}`
IO.popen("vagrant up #{host}") do |output|
  while line = output.gets do
    # simply echo it back
    puts line
  end
end

# determine SSH config
config = Tempfile.new('', Dir.tmpdir)
config.write(`vagrant ssh-config #{host}`)
config.close
options = Net::SSH::Config.for(host, [config.path])
options[:user]
set :host,        options[:host_name] || host
set :ssh_options, options


# retrieve dynamic vars for given hostname
def retrieve_vars(hostname)

  # accept basename for sought vars file,
  # then return a hash based on those settings
  def read_vars_file(file_basename)
    vars_filepath = File.expand_path(File.join(
      File.dirname(__FILE__), 'vars', "#{file_basename}.yml"
    ))
    return YAML.load_file(vars_filepath)
  end

  # noisy, repetitive if statements to build a list
  # of required dynamic vars.
  if hostname =~ /^development$/
    vars = read_vars_file('development')
  end

  if hostname =~ /-staging$/
    vars = read_vars_file('staging')
    # Ideally these IP addresses would be cached, since they don't
    # change during a test run. Right now, both values are looked up twice,
    # once for each staging host.
    vars['app_ip'] = retrieve_ip_addr('app-staging')
    vars['monitor_ip'] = retrieve_ip_addr('mon-staging')
  end

  if hostname =~ /-prod$/
    vars = read_vars_file('prod')
    vars['app_ip'] = retrieve_ip_addr('app-prod')
    vars['monitor_ip'] = retrieve_ip_addr('mon-prod')
  end

  if hostname =~ /^(app|mon)/
    vars['tor_user_uid'] = vagrant_ssh_cmd(hostname, "id -u debian-tor")
    vars['ssh_group_gid'] = vagrant_ssh_cmd(hostname, "getent group ssh | cut -d: -f3")
  end

  # These vars are host-specific, so check hostname before querying.
  if hostname =~ /^app/
    vars['apache_user_uid'] = vagrant_ssh_cmd(hostname, "id -u www-data")
  end

  if hostname =~ /^mon/
    vars['postfix_user_uid'] = vagrant_ssh_cmd(hostname, "id -u postfix")
  end

  return vars

end

# ssh into vagrant machine, run command, return output
def vagrant_ssh_cmd(hostname, command)
  # Dump stderr, to avoid noisy "Connection closed" messages.
  # Error code is checked below.
  filter_stderr = "2> /dev/null"
  vagrant_cmd = "vagrant ssh #{hostname} --command '#{command}'"
  result = `#{vagrant_cmd} #{filter_stderr}`
  if $? != 0
    puts "Command failed: #{vagrant_cmd}"
    exit(1)
  end
  return result
end

# look up ip address for given hostname,
# so spectests are relevant regardless of provider
def retrieve_ip_addr(hostname)
  ip_output = vagrant_ssh_cmd(hostname, "hostname -I")
  # Vagrant VirtualBox images will always have eth0 as the NAT device,
  # but spectests need the private_network device instead.
  iface1, iface2 = ip_output.split()
  # If we have two devices, assume first is NAT and return second.
  # Otherwise, assume eth0 is the primary address.
  return iface2 ? iface2 : iface1
end

# load dynamic vars for host
set_property retrieve_vars(host)
