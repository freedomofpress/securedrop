class deaddrop::cis_debian_v1_0 {
  ############################################################################ 
  #Ensure root password is not set and account is locked                     #
  #CIS Debian Benchmark v1: 1.6                                              #
  #Note: The CIS Debian Benchmark says to set a secure root password but best#
  #practices for Ubuntu is not to set a root password or allow root to log in#
  ############################################################################

  ############################################################################
  #Update System                                                             #
  #CIS Debian Benchmark v1: 2.1                                              #
  ############################################################################
  exec { 'apt-get update':
    path        => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user        => 'root',
    group       => 'root',
  }

  ############################################################################
  #Configure SSH                                                             #
  #CIS Debian Benchmark v1.0: 2.3                                            #
  #Note: Will also require a Google Authenitcator code for SSH access if set #
  ############################################################################
  file { "ssh_config":
    ensure => file,
    path   => "/etc/ssh/ssh_config",
    source => "puppet:///modules/deaddrop/ssh_config",
    owner  => 'root',
    group  => 'root',
    mode   => '0644',
  }

  file { "sshd_config":
    ensure  => file,
    path    => "/etc/ssh/sshd_config",
    content => template("deaddrop/sshd_config.erb"),
    owner   => 'root',
    group   => 'root',
    mode    => '0600',
  }

  file { "common-auth":
    ensure  => file,
    path    => "/etc/pam.d/common-auth",
    content => template("deaddrop/common-auth.erb"),
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
  }

  ############################################################################ 
  #Enable System Accounting                                                  #
  #CIS Debian Benchmark v1: 2.4                                              #
  ############################################################################
  package { 'sysstat': ensure => installed }

  service {'sysstat':
    ensure  => running,
    require => Package["sysstat"],
  }

  ############################################################################
  #Configure Host-Based Firewall to Limit Access                             #
  #CIS Debian Benchmark v1.0: 3.2                                            #
  ############################################################################
  package { 'iptables': ensure => 'installed' }

  file {'iptables':
    ensure => directory,
    path   => '/etc/iptables',
    owner  => 'root',
    group  => 'root',
  }

  file {'rules_v4':
    ensure  => file,
    path    => '/etc/iptables/rules_v4',
    content => template("deaddrop/iptables_v4.erb"),
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
    require => Package['iptables'],
  }

  exec { 'iptables-restore < /etc/iptables/rules_v4':
    cwd         => '/etc/iptables',
    path        => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user        => 'root',
    group       => 'root',
    subscribe   => File['/etc/iptables/rules_v4'],
    refreshonly => true,
  }

  file {'iptablesload':
    ensure  => file,
    path    => '/etc/network/if-pre-up.d/iptablesload',
    source => "puppet:///modules/deaddrop/iptablessave",
    owner   => 'root',
    group   => 'root',
    mode    => '0740',
  }

  file {'iptablessave':
    ensure  => file,
    path    => '/etc/network/if-post-down.d/iptablessave',
    source => "puppet:///modules/deaddrop/iptablessave",
    owner   => 'root',
    group   => 'root',
    mode    => '0740',
  }

  file { '/etc/hosts.allow':
    ensure  => file,
    path    => '/etc/hosts.allow',
    content => template("deaddrop/hosts.allow.erb"),
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
  }

  file { '/etc/hosts.deny':
    ensure  => file,
    path    => '/etc/hosts.deny',
    content => template("deaddrop/hosts.deny.erb"),
    owner   => 'root',
    group   => 'root',
    mode    => '0644',
  }

  ############################################################################
  #Disable X Font Server If Possible                                         #
  #CIS Debian Benchmark v1.0: 4.4                                            #
  ############################################################################
  exec { 'update-rc.d -f xfs remove':
    path  => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    user  => 'root',
    group => 'root',
  }

  ############################################################################
  #Network Parameter Modifications                                           #
  #CIS Debian Benchmark v1.0: 5.1, 5.2                                       #
  ############################################################################
  file { "sysctl.conf":
    ensure => present,
    path   => '/etc/sysctl.conf',
    source => "puppet:///modules/deaddrop/sysctl.conf",
    owner  => 'root',
    group  => 'root',
    mode   => '0600',
  }

  exec { "sysctl -p":
    cwd         => "/etc/",
    path        => [ "/bin/", "/sbin/" , "/usr/bin/", "/usr/sbin/" ],
    group       => 'root',
    user        => 'root',
    subscribe   => File["sysctl.conf"],
    refreshonly => true,
  }

  ############################################################################
  #Verify passwd, shadow, and group File Permissions                         #
  #CIS Debian Benchmark v1.0: 7.4                                            #
  ############################################################################
  file { 'passwd':
    ensure => present,
    path   => '/etc/passwd',
    mode   => '0644',
  }

  file { "group":
    ensure => present,
    path   => '/etc/group',
    mode   => '0644',
  }

  file { "shadow":
    ensure => present,
    path   => '/etc/shadow',
    mode   => '0400',
  }

  ###########################################################################
  #Restrict at/cron To Authorized Users                                     #
  #CIS Debian Benchmark v1.0: 8.4                                           #
  ###########################################################################
  file { 'cron.allow':
    ensure => file,
    path   => '/etc/cron.allow',
    source => "puppet:///modules/deaddrop/cron.allow",
    mode   => '0400',
  }

  file { 'cron.deny':
    ensure => absent,
    path   => '/etc/cron.deny',
  }

  ############################################################################
  #Restrict Permissions on crontab files                                     #
  #CIS Debian Benchmark v1.0: 8.5                                            #
  ############################################################################
  file { 'crontab':
    ensure => present,
    path   => '/etc/crontab',
    mode   => '0400',
  }

  file { "cron":
    ensure  => directory,
    path    => '/var/spool/cron',
    mode    => '1700',
  }

  ############################################################################
  #Restrict Root Logins To System Console                                    #
  #CIS Debian Benchmark v1.0: 8.7                                            #
  ############################################################################
  file { 'securetty':
    ensure => present,
    path   => '/etc/securetty',
    source => "puppet:///modules/deaddrop/securetty",
    owner  => 'root',
    group  => 'root',
    mode   => '0400',
  }

  ############################################################################
  #Set LILO/GRUB Password                                                    #
  #CIS Debian Benchmark v1.0: 8.8                                            #
  #Note: currently a manual process                                          #
  ############################################################################
}
