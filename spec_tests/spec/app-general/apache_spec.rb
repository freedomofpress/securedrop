# declare required apache packages
apache_packages = [
  'apache2-mpm-worker',
  'libapache2-mod-wsgi',
  'libapache2-mod-xsendfile',
]
# ensure required apache packages are installed
apache_packages.each do |apache_package|
  describe package(apache_package) do
    it { should be_installed }
  end
end

# ensure required apache2 security config file is present
# TODO: /etc/apache2/security is superfluous, see issue #643
# once ansible playbook is updated to remove it, this check
# should be removed as well.
describe file('/etc/apache2/security') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match "ServerTokens Prod" }
  its(:content) { should match "ServerSignature Off" }
  its(:content) { should match "TraceEnable Off" }
end

# declare required apache2 config settings
apache2_config_settings = [
  'Mutex file:${APACHE_LOCK_DIR} default',
  'PidFile ${APACHE_PID_FILE}',
  'Timeout 60',
  'KeepAlive On',
  'MaxKeepAliveRequests 100',
  'KeepAliveTimeout 5',
  'User www-data',
  'Group www-data',
  'AddDefaultCharset UTF-8',
  'DefaultType None',
  'HostnameLookups Off',
  'ErrorLog /dev/null',
  'LogLevel crit',
  'IncludeOptional mods-enabled/*.load',
  'IncludeOptional mods-enabled/*.conf',
  'Include ports.conf',
  'IncludeOptional sites-enabled/*.conf',
  'ServerTokens Prod',
  'ServerSignature Off',
  'TraceEnable Off',
]
# ensure required apache2 config settings are present
describe file('/etc/apache2/apache2.conf') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  apache2_config_settings.each do |apache2_config_setting|
    apache2_config_setting_regex = Regexp.quote(apache2_config_setting)
    its(:content) { should match /^#{apache2_config_setting_regex}$/ }
  end
end

# ensure apache2 ports conf is present
describe file('/etc/apache2/ports.conf') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_mode '644' }
  its(:content) { should match /^Listen 0\.0\.0\.0:8080$/ }
  its(:content) { should match /^Listen 0\.0\.0\.0:80$/ }
end

# declare desired apache headers for vhost configs
apache2_common_headers = [
  'Header set Cache-Control "max-age=0, no-cache, no-store, must-revalidate"',
  'Header edit Set-Cookie ^(.*)$ $1;HttpOnly',
  'Header set Pragma "no-cache"',
  'Header set Expires "-1"',
  'Header always append X-Frame-Options: DENY',
  'Header set X-XSS-Protection: "1; mode=block"',
  'Header set X-Content-Type-Options: nosniff',
  'Header set X-Download-Options: noopen',
  # using string literal syntax here (%{}) to avoid manual quote escaping
  %{Header set X-Content-Security-Policy: "default-src 'self'"},
  %{Header set Content-Security-Policy: "default-src 'self'"},
  'Header unset Etag',
]
# declare block of directory declarations common to both
# source and document interfaces.
common_apache2_directory_declarations = <<eos
<Directory />
  Options None
  AllowOverride None
  Order deny,allow
  Deny from all
</Directory>

<Directory /var/www/>
  Options None
  AllowOverride None
  <Limit GET POST HEAD>
    Order allow,deny
    allow from all
  </Limit>
  <LimitExcept GET POST HEAD>
    Order deny,allow
    Deny from all
  </LimitExcept>
</Directory>

<Directory #{property['securedrop_code']}>
  Options None
  AllowOverride None
  <Limit GET POST HEAD>
    Order allow,deny
    allow from all
  </Limit>
  <LimitExcept GET POST HEAD>
    Order deny,allow
    Deny from all
  </LimitExcept>
</Directory>
eos
# declare desired apache2 available sites
apache2_available_sites = [
  '/etc/apache2/sites-available/document.conf',
  '/etc/apache2/sites-available/source.conf',
]
# check desired apache2 available sites for common headers
apache2_available_sites.each do |apache2_available_site|
  describe file(apache2_available_site) do
    it { should be_file }
    it { should be_owned_by 'root' }
    it { should be_mode '644' }
    apache2_common_headers.each do |apache2_common_header|
      apache2_common_header_regex = Regexp.quote(apache2_common_header)
      its(:content) { should match /^#{apache2_common_header_regex}$/ }
    end
    its(:content) { should contain(common_apache2_directory_declarations) }
  end
end

# declare source-specific apache configs
source_apache2_config_settings = [
  '<VirtualHost 0.0.0.0:80>',
  "DocumentRoot #{property['securedrop_code']}/static",
  "Alias /static #{property['securedrop_code']}/static",
  "WSGIDaemonProcess source  processes=2 threads=30 display-name=%{GROUP} python-path=#{property['securedrop_code']}",
  'WSGIProcessGroup source',
  'WSGIScriptAlias / /var/www/source.wsgi/',
  'AddType text/html .py',
  'XSendFile        Off',
  'LimitRequestBody 524288000',
  'ErrorDocument 400 /notfound',
  'ErrorDocument 401 /notfound',
  'ErrorDocument 403 /notfound',
  'ErrorDocument 404 /notfound',
  'ErrorDocument 500 /notfound',
  'ErrorLog /var/log/apache2/source-error.log',
]
# check source-specific apache2 config
describe file('/etc/apache2/sites-available/source.conf') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_grouped_into  'root' }
  it { should be_mode '644' }
  source_apache2_config_settings.each do |source_apache2_config_setting|
    source_apache2_config_setting_regex = Regexp.quote(source_apache2_config_setting)
    its(:content) { should match /^#{source_apache2_config_setting_regex}$/ }
  end
end

# declare document-specific apache configs
document_apache2_config_settings = [
  '<VirtualHost 0.0.0.0:8080>',
  "DocumentRoot #{property['securedrop_code']}/static",
  "Alias /static #{property['securedrop_code']}/static",
  "WSGIDaemonProcess document  processes=2 threads=30 display-name=%{GROUP} python-path=#{property['securedrop_code']}",
  'WSGIProcessGroup document',
  'WSGIScriptAlias / /var/www/document.wsgi/',
  'AddType text/html .py',
  'XSendFile        On',
  'XSendFilePath    /var/lib/securedrop/store/',
  'XSendFilePath    /var/lib/securedrop/tmp/',
  'ErrorLog /var/log/apache2/document-error.log',
  'CustomLog /var/log/apache2/document-access.log combined',
]
# check document-specific apache2 config
describe file('/etc/apache2/sites-available/document.conf') do
  it { should be_file }
  it { should be_owned_by  'root' }
  it { should be_grouped_into  'root' }
  it { should be_mode '644' }
  document_apache2_config_settings.each do |document_apache2_config_setting|
    document_apache2_config_setting_regex = Regexp.quote(document_apache2_config_setting)
    its(:content) { should match /^#{document_apache2_config_setting_regex}$/ }
  end
end

# declare apache2 enabled modules
apache2_enabled_modules = [
  'access_compat',
  'authn_core',
  'alias',
  'authz_core',
  'authz_host',
  'authz_user',
  'deflate',
  'filter',
  'dir',
  'headers',
  'mime',
  'mpm_event',
  'negotiation',
  'reqtimeout',
  'rewrite',
  'wsgi',
  'xsendfile',
]
# ensure required apache2 modules are enabled
apache2_enabled_modules.each do |enabled_module|
  describe command("a2query -m #{enabled_module}") do
    its(:stdout) { should match /^#{enabled_module} \(enabled/ }
  end
end

# declare apache2 disabled modules
apache2_disabled_modules = [
  'auth_basic',
  'authn_file',
  'autoindex',
  'env',
  'setenvif',
  'status',
]
# ensure unwanted apache2 modules are disabled
apache2_disabled_modules.each do |disabled_module|
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

# Is apache running as user X
describe service('apache2') do
 it { should be_enabled }
 it { should be_running }
end

# ensure securedrop user account is configured properly
describe user('www-data') do
  it { should exist }
  it { should have_home_directory '/var/www' }
  it { should have_login_shell '/usr/sbin/nologin' }
end

# Is apache listening only on localhost:80 and 8080
listening_ports = ['80', '8080']
listening_ports.each do |listening_port|
  describe port(listening_port) do
    it { should be_listening.with('tcp') }
    it { should be_listening.on('0.0.0.0').with('tcp') }
  end
end

# Check firewall rule
