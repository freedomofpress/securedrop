class deaddrop::sshfs_remote {
    include deaddrop::sshfs

    service { "networking":
        hasrestart => true,
        hasstatus => false,
        restart => "/etc/init.d/networking restart",
        ensure => running,
        provider => upstart,
    }

    mount { "$store_dir":
        notify => Service["networking"],
        ensure => present,
        device => "sshfs#${apache_user}@${journalist_ip}:${store_dir}",
        fstype => 'fuse',
        options => 'comment=sshfs,noauto,users,exec,uid=33,gid=33,allow_other,reconnect,transform_symlinks,BatchMode=yes',
        atboot => no,
        remounts => false,
    }

    mount { "$keys_dir":
        notify => Service["networking"],
        ensure => present,
        device => "sshfs#${apache_user}@${journalist_ip}:${keys_dir}",
        fstype => 'fuse',
        options => 'comment=sshfs,noauto,users,exec,uid=33,gid=33,allow_other,reconnect,transform_symlinks,BatchMode=yes',
        atboot => no,
        remounts => false,
    }
  
    file { '/etc/network/if-up.d/mountsshfs':
        ensure => file,
        source => "puppet:///modules/deaddrop/mountsshfs",
        owner => 'root',
        group => 'root',
        mode => '0755',
    }
 
    file { '/etc/network/if-down.d/umountsshfs':
        ensure => file,
        source => "puppet:///modules/deaddrop/umountsshfs",
        owner => 'root',
        group => 'root',
        mode => '0755',
    }
}
