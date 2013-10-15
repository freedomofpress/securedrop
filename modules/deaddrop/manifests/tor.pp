class deaddrop::tor{
  apt::key { "tor":
    key        => "886DDD89",
    key_server => "keys.gnupg.net",
  }

  package { "deb.torproject.org-keyring": ensure => installed, }

  apt::source { "tor":
    location          => "http://deb.torproject.org/torproject.org",
    release           => "precise",
    repos             => "main",
    required_packages => "deb.torproject.org-keyring",
    key               => "886DDD89",
    key_server        => "keys.gnupg.net",
    before            => Package["tor"],
    require           => Package["deb.torproject.org-keyring"],
  }

  package { 'tor':
    ensure => "installed",
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
