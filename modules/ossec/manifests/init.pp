# == Class: ossec
#
# Installs and configures ossec server, agent and local
#
# === Parameters
#
# Document parameters here.
#
# [*sample_parameter*]
#   Explanation of what this parameter affects and what it defaults to.
#   e.g. "Specify one or more upstream ntp servers as an array."
#
# === Variables
#
# Here you should define a list of variables that this module would require.
#
# [*sample_variable*]
#   Explanation of how this variable affects the funtion of this class and if it
#   has a default. e.g. "The parameter enc_ntp_servers must be set by the
#   External Node Classifier as a comma separated list of hostnames." (Note,
#   global variables should not be used in preference to class parameters  as of
#   Puppet 2.6.)
#
# === Examples
#
#  class { ossec:
#    servers => [ 'pool.ntp.org', 'ntp.local.company.com' ]
#  }
#
# === Authors
#
# Author Name <author@domain.com>
#
# === Copyright
#
# Copyright 2013 Your name here, unless otherwise noted.
#
# call this module via:  node 'name' {include ossec::server}
# replace server with  local or agent  depending on the type of ossec install you
# want to perform.
class ossec {

  class install {
    $osseczip     = "ossec-binary.tgz"
    $ossecversion = "ossec-hids-2.7"
    $workdir      = "/opt/working"

    file { "$workdir":
      ensure => directory,
      owner  => 'root',
      mode   => 760,
    }

    file {"$osseczip":
      path    => "${workdir}/${osseczip}",
      source  => "puppet:///modules/ossec/${osseczip}",
      require => File["$workdir"],
      owner   => 'root',
    }

    exec {"extract-ossec":
      cwd     => "${workdir}",
      command => "/bin/tar xzf ${osseczip}",
      creates => "${workdir}/${ossecversion}",
      user    => 'root',
      require => File["${osseczip}"],
    }

      file {"ossecvars":
      path    => "${workdir}/${ossecversion}/etc/preloaded-vars.conf",
      ensure  => present,
      content => template("ossec/preloaded-vars.conf.erb"),
      owner   => 'root',
      require => Exec["extract-ossec"],
    }

    exec {"install-ossec":
      cwd     => "${workdir}/${ossecversion}",
      command => "${workdir}/${ossecversion}/install.sh",
      creates => "/var/ossec/etc",
      user    => 'root',
      require => File["ossecvars"],
    }

    service { "ossec":
      enable => true,
      ensure => running,
      require => Exec["install-ossec"],
    }
  }

  class server inherits ossec::install {
    $ossectype = "server"

    # manage ossec.conf file
    file { "ossec.conf":
      path    => "/var/ossec/etc/ossec.conf",
      ensure  => present,
      owner   => 'root',
      group   => 'ossec',
      mode    => 0440,
      content => template("ossec/${role}-ossec-conf.erb"),
      require => Exec["install-ossec"],
    }

    exec { 'ossec-restart1' :
      command     => "/var/ossec/bin/ossec-control restart",
      subscribe   => File[ "ossec.conf" ],
      refreshonly => true,  # Only run command if monitored files change
      user        => 'root',
      group       => 'ossec',
    }
  }

  class sslkeys inherits ossec::server {
    $ossectype = "server"

    exec {'generate-ecdsa-key':
      cwd     => '/var/ossec',
      command => 'openssl ecparam -name prime256v1 -genkey -out /var/ossec/etc/sslmanager.key',
      user    => 'root',
      creates => '/var/ossec/etc/sslmanger.key',
      require => Exec["install-ossec"],
    }

    exec {'generate-cert':
      cwd     => '/var/ossec',
      user    => 'root',
      group   => 'ossec',
      command => 'openssl req -new -x509 -key /var/ossec/etc/sslmanager.key -out /var/ossec/etc/sslmanager.cert -days 365',
      require => Exec['generate-ecdsa-key'],
      creates => '/var/oss/esec/etc/sslmanager.cert'
    }
  }

  class ossec-authd inherits ossec::sslkeys {
    $ossectype = "server"

    exec {'ossec-authd':
      cwd     => '/var/ossec',
      command => "/var/ossec/bin/ossec-authd -p 1515 -i ${source_ip} ${journalist_ip} >/dev/null 2>&1 &",
      user    => 'root',
      require => Exec["install-ossec"],
    }
  }

  class agent inherits ossec::install {
    $ossectype = "agent"

    # manage ossec.conf file
    file { "ossec.conf":
      path    => "/var/ossec/etc/ossec.conf",
      ensure  => present,
      owner   => 'root',
      group   => 'ossec',
      mode    => 550,
      content => template("ossec/${role}-ossec-conf.erb"),
      require => Exec["install-ossec"],
   }

    exec {ossec-restart:
      command     => "/var/ossec/bin/ossec-control restart",
      subscribe   => File["ossec.conf"],
      refreshonly => true,  # Only run command if monitored files chang
    }
  }

  class agent-auth inherits ossec::agent {
    $ossectype = 'agent'

    exec {'add-agent':
      cwd     => '/var/ossec/bin/',
      command => "/var/ossec/bin/agent-auth -m $monitor_ip",
      owner   => 'root',
      require => Exec["install-ossec"],
    }
  }
}
