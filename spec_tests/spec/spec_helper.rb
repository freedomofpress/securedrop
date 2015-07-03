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

  # crude case statement for determining var lookup
  case hostname
  when /^development$/
    vars = read_vars_file('development')
  when /-staging$/
    # Both staging hosts need a similar list of vars.
    vars = read_vars_file('staging')
    vars['tor_user_uid'] = vagrant_ssh_cmd(hostname, "id -u debian-tor")
    vars['ssh_group_gid'] = vagrant_ssh_cmd(hostname, "getent group ssh | cut -d: -f3")
    # Ideally these IP addresses would be cached, since they don't
    # change during a test run. Right now, both values are looked up twice,
    # once for each staging host.
    vars['app_ip'] = retrieve_ip_addr('app-staging')
    vars['monitor_ip'] = retrieve_ip_addr('mon-staging')
    # These vars are host-specific, so check hostname before querying.
    if hostname.match(/^app/)
      vars['apache_user_uid'] = vagrant_ssh_cmd(hostname, "id -u www-data")
    elsif hostname.match(/^mon/)
      vars['postfix_user_uid'] = vagrant_ssh_cmd(hostname, "id -u postfix")
    end
  end
  return vars
end

# ssh into vagrant machine, run command, return output
def vagrant_ssh_cmd(hostname, command)
  # Every ssh connection will end with a "Connection closed" message.
  # Since dynamic variable fetching makes several ssh calls,
  # let's filter to remove that noisy output from stderr.
  filter_stderr = "2> >( grep -vP '^Connection to [\d.]+ closed\.' )"
  # Unfortunately it appears that all of stderr is being filtered,
  # not just the grep pattern. Perhaps the popen4 gem would facilitate
  # smarter filtering, but that doesn't seem worthwhile right now.
  vagrant_cmd = "vagrant ssh #{hostname} --command '#{command}'"
  # Ruby backticks use /bin/sh as shell, and /bin/sh doesn't support
  # process redirection, so force use of /bin/bash
  return `/bin/bash -c "#{vagrant_cmd} #{filter_stderr}"`
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
