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
['auth_basic','authn_file','autoindex','env','setenvif','status'].each do |disModules|
  describe command("a2query -m #{disModules}") do
    it { should return_stderr /No module matches/ }
  end
end

# Are default sites disabled?
['000-default'].each do |dissites|
  describe command("a2query -s #{dissites}") do
    it { should return_stderr /No site matches/ }
  end
end
 
# Are default html files removed?

# Is apache running as user X

# Is apache listening only on localhost:80 and 8080
describe port(80) do
  it { should be_listening.with('tcp') }
end
describe port(8080) do
  it { should be_listening.with('tcp') }
end

# Is the sites-available linked to sites-enabled source.conf document.conf
# Check firewall rule
