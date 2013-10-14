class deaddrop::journalist {

  user { 'www-data' :
    home => '/var/www',
  }

  file { '/var/www' :
    ensure => directory,
    owner  => 'root',
    group  => 'root',
    require => User['www-data'],
  }

  file { '/var/www/.ssh' :
    ensure  => directory,
    owner   => 'www-data',
    group   => 'www-data',
    require => File['/var/www'],
  }

  ssh::auth::server { "www-data":
    home => "/var/www",
    options => [ "from=\"$source_ip\"" , 'no-port-forwarding' , 'no-X11-forwarding' , 'no-agent-forwarding' , 'no-pty' ],
    user    => 'www-data',
    group   => 'www-data',
    require => File['/var/www/.ssh'],
  }

  package { 'python-pip':
    ensure => installed,
    before => Package["python-dev"],
  }

  package { 'python-dev': ensure => installed }

  $dependencies_install = [ "python-bcrypt ", "python-gnupg ", "pycrypto " ]

  exec { "pip install $dependencies_install":
    path   => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user => 'root',
    group => 'root',
    require => Package["python-dev"],
  }

##### Install Apache #####
  package { 'apache2-mpm-worker':
    ensure => installed,
    notify => Exec["a2dissite $default_sites"],
  }

  package { 'libapache2-mod-wsgi':
    ensure  => installed, 
    require => Package['apache2-mpm-worker'],
    notify  => Exec["a2enmod $enable_mods"],
  }

##### Disable unneeded apache modules #####
  exec { "a2enmod $enable_mods":
    path        => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user        => 'root',
    group       => 'root',
    logoutput   => 'true',
    subscribe   => Package['libapache2-mod-wsgi'],
    refreshonly => true,
  }

  exec { "a2dismod $disabled_mods":
    path        => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user        => 'root',
    group       => 'root',
    logoutput   => 'true',
    subscribe   => Package['apache2-mpm-worker'],
    refreshonly => true,
  }

##### configure vhost #####
  file { "$source_ip":
    path    => '/etc/apache2/sites-enabled/source',
    owner   => 'root',
    group   => 'root',
    content => template("deaddrop/vhost-deaddrop.conf.erb"),
    require => Package['apache2-mpm-worker'],
  }

##### configure apache config files #####
  file { '/var/www/index.html':
    ensure  => 'absent',
    require => Package['apache2-mpm-worker'],
  }

  file { '/etc/apache2/sites-available/default-ssl':
    ensure  => 'absent',
    require => Package['apache2-mpm-worker'],
  }

  file { '/etc/apache2/sites-available/default':
    ensure  => 'absent',
    require => Package['apache2-mpm-worker'],
  }

  exec { "a2dissite $default_sites": 
    path        => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user        => 'root',
    group       => 'root',
    subscribe   => Package['apache2-mpm-worker'],
    refreshonly => true,
  }

  file { 'ports.conf':
    ensure  => file,
    path    => '/etc/apache2/ports.conf',
    content => template("deaddrop/ports.conf.erb"),
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    require => Package['apache2-mpm-worker'],
  }

  file { 'apache2.conf':
    ensure  => file,
    path    => '/etc/apache2/apache2.conf',
    content => template("deaddrop/apache2.conf.erb"),
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    require => Package['apache2-mpm-worker'],
  }

  file { 'security':
    ensure  => file,
    path    => '/etc/apache2/conf.d/security',
    content => template("deaddrop/security.erb"),
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    require => Package['apache2-mpm-worker'],
  }

##### Copy the application file #####
  file { "$deaddrop_home":
    ensure  => directory,
    recurse => true,
    owner   => $apache_user,
    group   => $apache_user,
    mode    => '0600',
    source  => "puppet:///modules/deaddrop/deaddrop",
    before  => File["$deaddrop_home/store"],
  }

  file {"$deaddrop_home/store":
    ensure  => directory,
    owner   => $apache_user,
    group   => $apache_user,
    mode    => "0700",
    before  => File["$deaddrop_home/keys"],
    require => File["$deaddrop_home"],
  }

  file {"$deaddrop_home/keys":
    ensure => directory,
    owner  => $apache_user,
    group  => $apache_user,
    mode   => '0700',
    before => File["$deaddrop_home/config.py"],
  }

  file { "$deaddrop_home/config.py":
    ensure  => file,
    owner   => $apache_user,
    group   => $apache_user,
    mode    => '0600',
    content => template("deaddrop/config.py.erb"),
    before  => File["$deaddrop_home/web"],
  }

  file { "$deaddrop_home/webpy":
    ensure  => directory,
    recurse => true,
    owner   => $apache_user,
    group   => $apache_user,
    mode    => '0600',
    source  => "puppet:///modules/deaddrop/webpy",
    before  => File["$deaddrop_home/web"],
  }

  file { "$deaddrop_home/web":
    ensure  => 'link',
    target  => "$deaddrop_home/webpy/web",
    owner   => 'www-data',
    group   => 'www-data',
    require => File["$deaddrop_home/webpy"],
  }

  file { "/var/www/$app_gpg_pub_key":
    ensure  => file,
    owner   => $apache_user,
    group   => $apache_user,
    mode    => '0700',
    source  => "puppet:///modules/deaddrop/${app_gpg_pub_key}",
    require => File["$deaddrop_home"],
  }

  exec {'import_key':
    command     => "gpg2 --homedir $keys_dir --import /var/www/$app_gpg_pub_key",
    path        => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    cwd         => $keys_dir,
    user        => $apache_user,
    group       => $apache_user,
    subscribe   => File["/var/www/$app_gpg_pub_key"],
    refreshonly => true,
  }

  file { '/var/www/deaddrop/static':
    ensure  => directory,
    recurse => true,
    owner   => $apache_user,
    group   => $apache_user,
    mode    => '0700',
    source  => "puppet:///modules/deaddrop/deaddrop/static/",
    require => File["$deaddrop_home"],
  }
}
