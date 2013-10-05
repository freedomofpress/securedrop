# Class: deaddrop::sshfs
#
# This class installs sshfs
#
# Actions:
#   - Install the sshfs package
#
# Sample Usage:
#  class { 'deaddrop::sshfs': }
#
class deaddrop::sshfs {
        package { 'sshfs':
        ensure => installed,
        notify => File['fuse.conf'],
    }

    file { 'fuse.conf':
        ensure => file,
        path => '/etc/fuse.conf',
        source => "puppet:///modules/deaddrop/fuse.conf",
        owner => 'root',
        group => 'root',
    }

    exec { "usermod -a -G fuse $apache_user":
        user => 'root',
        group => 'root',
    } 

    file { '/dev/fuse':
        ensure => present,
        owner => 'root',
        group => 'fuse',
    }

    exec { "chmod g+rw /dev/fuse":
        user => 'root',
        group => 'root',
    }
}
