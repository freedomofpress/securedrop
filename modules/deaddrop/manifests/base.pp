class deaddrop::base {
  package { 'secure-delete':               ensure => 'installed' }
  package { 'gnupg2':                      ensure => 'installed' }
  package { 'syslog-ng':                   ensure => 'installed' }
  package { 'libpam-google-authenticator': ensure => 'installed' }
  package { 'ntp':                         ensure => 'installed' }
  package { 'haveged':                     ensure => 'installed' }
  package { 'rng-tools':                   ensure => 'installed' }
  package { 'unattended-upgrades':         ensure => 'installed' }

  file { '/etc/apt/apt.conf.d/20auto-upgrades':
    ensure => file,
    source => "puppet:///modules/deaddrop/20auto-upgrades",
    owner => 'root',
    group => 'root',
    mode => '0644',
    require => Package['unattended-upgrades'],
  }

  file { '/etc/apt/apt.conf.d/50unattended-upgrades':
    ensure => file,
    source => "puppet:///modules/deaddrop/50unattended-upgrades",
    owner => 'root',
    group => 'root',
    mode => '0644',
    require => Package['unattended-upgrades'],
  }
    
  exec { 'swapoff -a':
    path    => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user    => 'root',
    group   => 'root',
  }
    
##### Hold Back non grsec kernel upgrades #####

##### Create /etc/ssh/ssh_known_hosts file #####
  @@sshkey { $hostname:
    key          => $sshecdsakey,
    ensure       => 'present',
    host_aliases => "$role", 
    type         => 'rsa',
    target       => '/etc/ssh/ssh_known_hosts',
  }

  Sshkey <<| |>>

##### Create /etc/hosts file #####
  @@host { $fqdn:
    ip           => $ipaddress,
    host_aliases => ["$hostname", "$role"],
  }

  Host <<| |>>

  host { puppet:
    ip => $monitor_ip,
  }

  host { admin_ip:
    ip  => $admin_ip,
  }
}
