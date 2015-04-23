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

`vagrant up #{host}`

config = Tempfile.new('', Dir.tmpdir)
config.write(`vagrant ssh-config #{host}`)
config.close

options = Net::SSH::Config.for(host, [config.path])

options[:user] ||= Etc.getlogin

set :host,        options[:host_name] || host
set :ssh_options, options

# accept basename for sought vars file,
# then return a hash based on those settings
def retrieve_vars(file_basename)
  fullpath = File.expand_path(File.join(File.dirname(__FILE__), 'vars', "#{file_basename}.yml"))
  vars_file = YAML.load_file(fullpath)
  return vars_file
end

# load custom vars for host
case host
when /^development$/
  TEST_VARS = retrieve_vars('development')
when /^app-staging$/
  TEST_VARS = retrieve_vars('staging')
end

# Disable sudo
# set :disable_sudo, true


# Set environment variables
# set :env, :LANG => 'C', :LC_MESSAGES => 'C'

# Set PATH
# set :path, '/sbin:/usr/local/sbin:$PATH'
