#require 'spec_helper'

['apache2-mpm-worker', 'libapache2-mod-wsgi', 'libapache2-mod-xsendfile' ].each do |pkg|
  describe package(pkg) do
    it { should be_installed }
  end
end

# Are the apache config file there
describe file('/etc/apache2/apache2.conf') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match "ErrorLog /dev/null" }
  its(:content) { should match "LogLevel crit" }
  its(:content) { should match "ServerTokens Prod" }
  its(:content) { should match "ServerSignature Off" }
  its(:content) { should match "TraceEnable Off" }
end

describe file('/etc/apache2/ports.conf') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match "Listen 0.0.0.0:8080" }
  its(:content) { should match "Listen 0.0.0.0:80" }
end

describe file('/etc/apache2/security') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match "ServerTokens Prod" }
  its(:content) { should match "ServerSignature Off" }
  its(:content) { should match "TraceEnable Off" }
end

describe file('/etc/apache2/sites-available/document.conf') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match "<VirtualHost 0.0.0.0:8080>" }
  its(:content) { should match "WSGIScriptAlias / /var/www/document.wsgi/" }
end

describe file('/etc/apache2/sites-available/source.conf') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match "<VirtualHost 0.0.0.0:80>" }
  its(:content) { should match "WSGIScriptAlias / /var/www/source.wsgi/" }
  its(:content) { should match "ErrorLog /var/log/apache2/source-error.log" }
end

['access_compat','authn_core','alias','authz_core','authz_host','authz_user','deflate','filter','dir','headers','mime','mpm_event','negotiation','reqtimeout','rewrite','wsgi','xsendfile'].each do |enabled_module|
  describe command("a2query -m #{enabled_module}") do
    its(:stdout) { should match /^#{enabled_module} \(enabled/ }
  end
end

# are the correct apache modules disabled
['auth_basic','authn_file','autoindex','env','setenvif','status'].each do |disabled_module|
  describe command("a2query -m #{disabled_module}") do
    its(:stderr) { should match /^No module matches #{disabled_module}/ }
  end
end

# Are source and document interface sites enabled?
['source', 'document'].each do |enabled_site|
  describe command("a2query -s #{enabled_site}") do
    its(:stdout) { should match /^#{enabled_site} \(enabled/ }
  end
end

# Are default sites disabled?
['000-default'].each do |disabled_site|
  describe command("a2query -s #{disabled_site}") do
    its(:stderr) { should match /^No site matches #{disabled_site}/ }
  end
end

# Are default html files removed?

# Is apache running as user X
describe service('apache2') do
 it { should be_enabled }
 it { should be_running }
end

describe user('www-data') do
  it { should exist }
  it { should have_home_directory '/var/www' }
  it { should have_login_shell '/usr/sbin/nologin' }
end

# Is apache listening only on localhost:80 and 8080
describe port(80) do
  it { should be_listening.with('tcp') }
  it { should be_listening.on('0.0.0.0').with('tcp') }
end
describe port(8080) do
  it { should be_listening.with('tcp') }
  it { should be_listening.on('0.0.0.0').with('tcp') }
end

# Check firewall rule
