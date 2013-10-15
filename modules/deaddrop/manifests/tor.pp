class deaddrop::tor{
  exec { 'add_tor_source':
    path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    command => 'echo "deb     http://deb.torproject.org/torproject.org precise main" >> /etc/apt/sources.list',
    user    => 'root',
    group   => 'root',
  }

  exec { 'receive_tor_key':
    path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    command => 'gpg --keyserver keys.gnupg.net --recv 886DDD89',
    user    => 'root',
    group   => 'root',
    require => Exec["add_tor_source"],
  }

  exec { 'add_tor_key':
    path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    command => 'gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | sudo apt-key add -',
    user    => 'root',
    group   => 'root',
    require => Exec["receive_tor_key"],
  }

  exec { 'tor_update':
    path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    command => 'apt-get update',
    user    => 'root',
    group   => 'root',
    require => Exec["add_tor_key"],
  }

  package { "deb.torproject.org-keyring":
    ensure  => installed,
    require => Exec["tor_update"],
  }

  package { 'tor':
    ensure  => "installed",
    require => Package["deb.torproject.org-keyring"],
  }

  file { '/etc/tor/torrc':
    ensure  => file,
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    content => template("deaddrop/torrc.erb"),
    require => Package["tor"],
  }

  service { 'tor':
    ensure     => running,
    hasrestart => true,
    hasstatus  => true,
    subscribe  => File['/etc/tor/torrc'],
    require    => Package['tor'],
  }

  exec { 'passwd -l debian-tor':
    path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user    => 'root',
    group   => 'root',
    require => Package["tor"],
  }
}
