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

# accept basename for sought vars file,
# then return a hash based on those settings
def retrieve_vars(file_basename)
  vars_filepath = File.expand_path(File.join(File.dirname(__FILE__), 'vars', "#{file_basename}.yml"))
  vars = YAML.load_file(vars_filepath)
  # Look up dynamic vars from live systems
  if file_basename == 'staging'
    vars['monitor_ip'] = retrieve_ip_addr('mon-staging')
    vars['app_ip'] = retrieve_ip_addr('app-staging')
    vars['tor_user_uid'] = vagrant_ssh_cmd(ENV['TARGET_HOST'], "id -u debian-tor")
    vars['postfix_user_uid'] = vagrant_ssh_cmd(ENV['TARGET_HOST'], "id -u postfix")
    vars['ssh_group_gid'] = vagrant_ssh_cmd(ENV['TARGET_HOST'], "getent group ssh | cut -d: -f3")
  end
  return vars
end

# ssh into vagrant machine, run command, return output
def vagrant_ssh_cmd(hostname, command)
  # every ssh connection will end with a "Connection closed" message.
  # since dynamic variable fetching makes several ssh calls,
  # let's filter to remove that noisy output from stderr.
  filter_stderr = "2> >( grep -vP '^Connection to [\d.]+ closed\.' )"
  # unfortunately it appears that all of stderr is being filtered,
  # not just the grep pattern. perhaps the popen4 gem would facilitate
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
case host
when /^development$/
  set_property retrieve_vars('development')
when /-staging$/
  set_property retrieve_vars('staging')
end
