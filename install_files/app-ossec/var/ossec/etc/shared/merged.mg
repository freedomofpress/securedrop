!9501 cis_debian_linux_rcl.txt
# @(#) $Id: ./src/rootcheck/db/cis_debian_linux_rcl.txt, 2011/09/08 dcid Exp $

#
# OSSEC Linux Audit - (C) 2008 Daniel B. Cid - dcid@ossec.net
#
# Released under the same license as OSSEC.
# More details at the LICENSE file included with OSSEC or online
# at: http://www.ossec.net/en/licensing.html
#
# [Application name] [any or all] [reference]
# type:<entry name>;
#
# Type can be:
#             - f (for file or directory)
#             - p (process running)
#             - d (any file inside the directory)
#
# Additional values:
# For the registry , use "->" to look for a specific entry and another
# "->" to look for the value.
# For files, use "->" to look for a specific value in the file.
#
# Values can be preceeded by: =: (for equal) - default
#                             r: (for ossec regexes)
#                             >: (for strcmp greater)
#                             <: (for strcmp  lower)
# Multiple patterns can be specified by using " && " between them.
# (All of them must match for it to return true).


# CIS Checks for Debian/Ubuntu
# Based on Center for Internet Security Benchmark for Debian Linux v1.0


# Main one. Only valid for Debian/Ubuntu.
[CIS - Testing against the CIS Debian Linux Benchmark v1.0] [all required] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/debian_version;
f:/proc/sys/kernel/ostype -> Linux;



# Section 1.4 - Partition scheme.
[CIS - Debian Linux 1.4 - Robust partition scheme - /tmp is not on its own partition] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:/tmp;

[CIS - Debian Linux 1.4 - Robust partition scheme - /opt is not on its own partition] [all] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/opt;
f:/etc/fstab -> !r:/opt;

[CIS - Debian Linux 1.4 - Robust partition scheme - /var is not on its own partition] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:/var;



# Section 2.3 - SSH configuration
[CIS - Debian Linux 2.3 - SSH Configuration - Protocol version 1 enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/ssh/sshd_config -> !r:^# && r:Protocol\.+1;

[CIS - Debian Linux 2.3 - SSH Configuration - IgnoreRHosts disabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/ssh/sshd_config -> !r:^# && r:IgnoreRhosts\.+no;

[CIS - Debian Linux 2.3 - SSH Configuration - Empty passwords permitted] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/ssh/sshd_config -> !r:^# && r:^PermitEmptyPasswords\.+yes;

[CIS - Debian Linux 2.3 - SSH Configuration - Host based authentication enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/ssh/sshd_config -> !r:^# && r:HostbasedAuthentication\.+yes;

[CIS - Debian Linux 2.3 - SSH Configuration - Root login allowed] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/ssh/sshd_config -> !r:^# && r:PermitRootLogin\.+yes;



# Section 2.4 Enable system accounting
#[CIS - Debian Linux 2.4 - System Accounting - Sysstat not installed] [all] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
#f:!/etc/default/sysstat;
#f:!/var/log/sysstat;

#[CIS - Debian Linux 2.4 - System Accounting - Sysstat not enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
#f:!/etc/default/sysstat;
#f:/etc/default/sysstat -> !r:^# && r:ENABLED="false";



# Section 2.5 Install and run Bastille
#[CIS - Debian Linux 2.5 - System harderning - Bastille is not installed] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
#f:!/etc/Bastille;



# Section 2.6 Ensure sources.list Sanity
[CIS - Debian Linux 2.6 - Sources list sanity - Security updates not enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:!/etc/apt/sources.list;
f:!/etc/apt/sources.list -> !r:^# && r:http://security.debian|http://security.ubuntu;



# Section 3 - Minimize inetd services
[CIS - Debian Linux 3.3 - Telnet enabled on inetd] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/inetd.conf -> !r:^# && r:telnet;

[CIS - Debian Linux 3.4 - FTP enabled on inetd] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/inetd.conf -> !r:^# && r:/ftp;

[CIS - Debian Linux 3.5 - rsh/rlogin/rcp enabled on inetd] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/inetd.conf -> !r:^# && r:shell|login;

[CIS - Debian Linux 3.6 - tftpd enabled on inetd] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/inetd.conf -> !r:^# && r:tftp;

[CIS - Debian Linux 3.7 - imap enabled on inetd] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/inetd.conf -> !r:^# && r:imap;

[CIS - Debian Linux 3.8 - pop3 enabled on inetd] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/inetd.conf -> !r:^# && r:pop;

[CIS - Debian Linux 3.9 - Ident enabled on inetd] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/inetd.conf -> !r:^# && r:ident;



# Section 4 - Minimize boot services
[CIS - Debian Linux 4.1 - Disable inetd - Inetd enabled but no services running] [all] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
p:inetd;
f:!/etc/inetd.conf -> !r:^# && r:wait;

[CIS - Debian Linux 4.3 - GUI login enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/inittab -> !r:^# && r:id:5;

[CIS - Debian Linux 4.6 - Disable standard boot services - Samba Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/samba;

[CIS - Debian Linux 4.7 - Disable standard boot services - NFS Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/nfs-common;
f:/etc/init.d/nfs-user-server;
f:/etc/init.d/nfs-kernel-server;

[CIS - Debian Linux 4.9 - Disable standard boot services - NIS Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/nis;

[CIS - Debian Linux 4.13 - Disable standard boot services - Web server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/apache;
f:/etc/init.d/apache2;

[CIS - Debian Linux 4.15 - Disable standard boot services - DNS server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/bind;

[CIS - Debian Linux 4.16 - Disable standard boot services - MySQL server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/mysql;

[CIS - Debian Linux 4.16 - Disable standard boot services - PostgreSQL server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/postgresql;

[CIS - Debian Linux 4.17 - Disable standard boot services - Webmin Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/webmin;

[CIS - Debian Linux 4.18 - Disable standard boot services - Squid Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/init.d/squid;



# Section 5 - Kernel tuning
[CIS - Debian Linux 5.1 - Network parameters - Source routing accepted] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/proc/sys/net/ipv4/conf/all/accept_source_route -> 1;

[CIS - Debian Linux 5.1 - Network parameters - ICMP broadcasts accepted] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/proc/sys/net/ipv4/icmp_echo_ignore_broadcasts -> 0;

[CIS - Debian Linux 5.2 - Network parameters - IP Forwarding enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/proc/sys/net/ipv4/ip_forward -> 1;
f:/proc/sys/net/ipv6/ip_forward -> 1;



# Section 7 - Permissions
[CIS - Debian Linux 7.1 - Partition /var without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:^# && r:ext2|ext3 && r:/var && !r:nodev;

[CIS - Debian Linux 7.1 - Partition /tmp without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:^# && r:ext2|ext3 && r:/tmp && !r:nodev;

[CIS - Debian Linux 7.1 - Partition /opt without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:^# && r:ext2|ext3 && r:/opt && !r:nodev;

[CIS - Debian Linux 7.1 - Partition /home without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:^# && r:ext2|ext3 && r:/home && !r:nodev ;

[CIS - Debian Linux 7.2 - Removable partition /media without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:^# && r:/media && !r:nodev;

[CIS - Debian Linux 7.2 - Removable partition /media without 'nosuid' set] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:^# && r:/media && !r:nosuid;

[CIS - Debian Linux 7.3 - User-mounted removable partition /media] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/fstab -> !r:^# && r:/media && r:user;



# Section 8 - Access and authentication
[CIS - Debian Linux 8.8 - LILO Password not set] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/lilo.conf -> !r:^# && !r:restricted;
f:/etc/lilo.conf -> !r:^# && !r:password=;

[CIS - Debian Linux 8.8 - GRUB Password not set] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/boot/grub/menu.lst -> !r:^# && !r:password;

[CIS - Debian Linux 9.2 - Account with empty password present] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/shadow -> r:^\w+::;

[CIS - Debian Linux 13.11 - Non-root account with uid 0] [any] [http://www.ossec.net/wiki/index.php/CIS_DebianLinux]
f:/etc/passwd -> !r:^# && !r:^root: && r:^\w+:\w+:0:;


# EOF
!8192 cis_rhel5_linux_rcl.txt
# @(#) $Id: ./src/rootcheck/db/cis_rhel5_linux_rcl.txt, 2011/09/08 dcid Exp $

#
# OSSEC Linux Audit - (C) 2008 Daniel B. Cid - dcid@ossec.net
#
# Released under the same license as OSSEC.
# More details at the LICENSE file included with OSSEC or online
# at: http://www.ossec.net/en/licensing.html
#
# [Application name] [any or all] [reference]
# type:<entry name>;
#
# Type can be:
#             - f (for file or directory)
#             - p (process running)
#             - d (any file inside the directory)
#
# Additional values:
# For the registry , use "->" to look for a specific entry and another
# "->" to look for the value.
# For files, use "->" to look for a specific value in the file.
#
# Values can be preceeded by: =: (for equal) - default
#                             r: (for ossec regexes)
#                             >: (for strcmp greater)
#                             <: (for strcmp  lower)
# Multiple patterns can be specified by using " && " between them.
# (All of them must match for it to return true).


# CIS Checks for Red Hat (RHEL 2.1, 3.0, 4.0 and Fedora Core 1,2,3,4 and 5).
# Based on CIS Benchmark for Red Hat Enterprise Linux 5 v1.1



# RC scripts location
$rc_dirs=/etc/rc.d/rc2.d,/etc/rc.d/rc3.d,/etc/rc.d/rc4.d,/etc/rc.d/rc5.d;



# Main one. Only valid for Red Hat 5.
[CIS - Testing against the CIS Red Hat Enterprise Linux 5 Benchmark v1.1] [any required] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/redhat-release -> r:^Red Hat Enterprise Linux \S+ release 5;
f:/etc/redhat-release -> r:^CentOS && r:release 5.2;



# Build considerations - Partition scheme.
[CIS - RHEL5 - Build considerations - Robust partition scheme - /var is not on its own partition] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/fstab -> !r:/var;



# Section 2.3 - SSH configuration
[CIS - RHEL5 2.3 - SSH Configuration - Protocol version 1 enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/ssh/sshd_config -> !r:^# && r:Protocol\.+1;

[CIS - RHEL5 2.3 - SSH Configuration - IgnoreRHosts disabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/ssh/sshd_config -> !r:^# && r:IgnoreRhosts\.+no;

[CIS - RHEL5 2.3 - SSH Configuration - Empty passwords permitted] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/ssh/sshd_config -> !r:^# && r:^PermitEmptyPasswords\.+yes;

[CIS - RHEL5 2.3 - SSH Configuration - Host based authentication enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/ssh/sshd_config -> !r:^# && r:HostbasedAuthentication\.+yes;

[CIS - RHEL5 2.3 - SSH Configuration - Root login allowed] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/ssh/sshd_config -> !r:^# && r:PermitRootLogin\.+yes;



# Section 2.4 Enable system accounting
#[CIS - RHEL5 2.4 - System Accounting - Sysstat not installed] [all] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
#f:!/var/log/sa;



# Section 3 - Minimize xinetd services
[CIS - RHEL5 3.3 - Telnet enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/xinetd.c/telnet -> !r:^# && r:disable && r:no;

[CIS - RHEL5 3.4 - VSFTP enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/xinetd.c/vsftpd -> !r:^# && r:disable && r:no;

[CIS - RHEL5 3.5 - rsh/rlogin/rcp enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/xinetd.c/rlogin -> !r:^# && r:disable && r:no;
f:/etc/xinetd.c/rsh -> !r:^# && r:disable && r:no;
f:/etc/xinetd.c/shell -> !r:^# && r:disable && r:no;

[CIS - RHEL5 3.6 - tftpd enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/xinetd.c/tftpd -> !r:^# && r:disable && r:no;

[CIS - RHEL5 3.7 - imap enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/xinetd.c/cyrus-imapd -> !r:^# && r:disable && r:no;

[CIS - RHEL5 3.8 - pop3 enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/xinetd.c/dovecot -> !r:^# && r:disable && r:no;



# Section 4 - Minimize boot services
[CIS - RHEL5 4.1 - Set daemon umask - Default umask is higher than 027] [all] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/init.d/functions -> !r:^# && r:^umask && <:umask 027;

[CIS - RHEL5 4.4 - GUI login enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/inittab -> !r:^# && r:id:5;

[CIS - RHEL5 4.7 - Disable standard boot services - Samba Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dsamba$;
d:$rc_dirs -> ^S\d\dsmb$;

[CIS - RHEL5 4.8 - Disable standard boot services - NFS Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dnfs$;
d:$rc_dirs -> ^S\d\dnfslock$;

[CIS - RHEL5 4.10 - Disable standard boot services - NIS Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dypbind$;
d:$rc_dirs -> ^S\d\dypserv$;

[CIS - RHEL5 4.13 - Disable standard boot services - NetFS Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dnetfs$;

[CIS - RHEL5 4.15 - Disable standard boot services - Apache web server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dapache$;

[CIS - RHEL5 4.16 - Disable standard boot services - SNMPD process Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dsnmpd$;

[CIS - RHEL5 4.17 - Disable standard boot services - DNS server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dnamed$;

[CIS - RHEL5 4.18 - Disable standard boot services - MySQL server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dmysqld$;

[CIS - RHEL5 4.18 - Disable standard boot services - PostgreSQL server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dpostgresql$;

[CIS - RHEL5 4.19 - Disable standard boot services - Squid Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dsquid$;

[CIS - RHEL5 4.20 - Disable standard boot services - Kudzu hardware detection Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
d:$rc_dirs -> ^S\d\dkudzu$;



# Section 5 - Kernel tuning
[CIS - RHEL5 5.1 - Network parameters - Source routing accepted] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/proc/sys/net/ipv4/conf/all/accept_source_route -> 1;

[CIS - RHEL5 5.1 - Network parameters - ICMP redirects accepted] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/proc/sys/net/ipv4/conf/all/accept_redirects -> 1;

[CIS - RHEL5 5.1 - Network parameters - ICMP secure redirects accepted] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/proc/sys/net/ipv4/conf/all/secure_redirects -> 1;

[CIS - RHEL5 5.1 - Network parameters - ICMP broadcasts accepted] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/proc/sys/net/ipv4/icmp_echo_ignore_broadcasts -> 0;

[CIS - RHEL5 5.2 - Network parameters - IP Forwarding enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/proc/sys/net/ipv4/ip_forward -> 1;
f:/proc/sys/net/ipv6/ip_forward -> 1;



# Section 7 - Permissions
[CIS - RHEL5 7.2 - Removable partition /media without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/fstab -> !r:^# && r:/media && !r:nodev;

[CIS - RHEL5 7.2 - Removable partition /media without 'nosuid' set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/fstab -> !r:^# && r:/media && !r:nosuid;

[CIS - RHEL5 7.3 - User-mounted removable partition allowed on the console] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/security/console.perms -> r:^<console>  \d+ <cdrom>;
f:/etc/security/console.perms -> r:^<console>  \d+ <floppy>;



# Section 8 - Access and authentication
[CIS - RHEL5 8.7 - GRUB Password not set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/boot/grub/menu.lst -> !r:^# && !r:password;

[CIS - RHEL5 9.2 - Account with empty password present] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/shadow -> r:^\w+::;

[CIS - RHEL5 SN.11 - Non-root account with uid 0] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL5]
f:/etc/passwd -> !r:^# && !r:^root: && r:^\w+:\w+:0:;


# EOF
!4457 system_audit_rcl.txt
# @(#) $Id: ./src/rootcheck/db/system_audit_rcl.txt, 2012/02/13 dcid Exp $

#
# OSSEC Linux Audit - (C) 2007 Daniel B. Cid - dcid@ossec.net
#
# Released under the same license as OSSEC.
# More details at the LICENSE file included with OSSEC or online
# at: http://www.ossec.net/en/licensing.html
#
# [Application name] [any or all] [reference]
# type:<entry name>;
#
# Type can be:
#             - f (for file or directory)
#             - p (process running)
#             - d (any file inside the directory)
#
# Additional values:
# For the registry , use "->" to look for a specific entry and another
# "->" to look for the value.
# For files, use "->" to look for a specific value in the file.
#
# Values can be preceeded by: =: (for equal) - default
#                             r: (for ossec regexes)
#                             >: (for strcmp greater)
#                             <: (for strcmp  lower)
# Multiple patterns can be specified by using " && " between them.
# (All of them must match for it to return true).
 
$php.ini=/etc/php.ini,/var/www/conf/php.ini,/etc/php5/apache2/php.ini;
$web_dirs=/var/www,/var/htdocs,/home/httpd,/usr/local/apache,/usr/local/apache2,/usr/local/www;


# PHP checks
[PHP - Register globals are enabled] [any] [http://www.ossec.net/wiki]
f:$php.ini -> r:^register_globals = On;


# PHP checks
[PHP - Expose PHP is enabled] [any] []
f:$php.ini -> r:^expose_php = On;


# PHP checks
[PHP - Allow URL fopen is enabled] [any] []
f:$php.ini -> r:^allow_url_fopen = On;



# PHP checks
[PHP - Displaying of errors is enabled] [any] []
f:$php.ini -> r:^display_errors = On;


# PHP checks - consider open_basedir && disable_functions


## Looking for common web exploits (might indicate that you are owned).
## Using http://www.ossec.net/wiki/index.php/WebAttacks_links as a reference.
#[Web exploits - Possible compromise] [any] [http://www.ossec.net/wiki/index.php/WebAttacks_links]
#d:$web_dirs -> .txt$ -> r:^<?php|^#!;


## Looking for common web exploits files (might indicate that you are owned).
## There are not specific, like the above.
## Using http://www.ossec.net/wiki/index.php/WebAttacks_links as a reference.
[Web exploits (uncommon file name inside htdocs) - Possible compromise] [any] [http://www.ossec.net/wiki/index.php/WebAttacks_links]
d:$web_dirs -> ^.yop$;

[Web exploits (uncommon file name inside htdocs) - Possible compromise] [any] [http://www.ossec.net/wiki/index.php/WebAttacks_links]
d:$web_dirs -> ^id$;

[Web exploits (uncommon file name inside htdocs) - Possible compromise] [any] [http://www.ossec.net/wiki/index.php/WebAttacks_links]
d:$web_dirs -> ^.ssh$;

[Web exploits (uncommon file name inside htdocs) - Possible compromise] [any] [http://www.ossec.net/wiki/index.php/WebAttacks_links]
d:$web_dirs -> ^...$;

[Web exploits (uncommon file name inside htdocs) - Possible compromise] [any] [http://www.ossec.net/wiki/index.php/WebAttacks_links]
d:$web_dirs -> ^.shell$;


## Looking for outdated Web applications
## Taken from http://sucuri.net/latest-versions
[Web vulnerability - Outdated WordPress installation] [any] [http://sucuri.net/latest-versions]
d:$web_dirs -> ^version.php$ -> r:^\.wp_version && >:$wp_version = '3.2.1';

[Web vulnerability - Outdated Joomla (v1.0) installation] [any] [http://sucuri.net/latest-versions]
d:$web_dirs -> ^version.php$ -> r:var \.RELEASE && r:'1.0';

#[Web vulnerability - Outdated Joomla (v1.5) installation] [any] [http://sucuri.net/latest-versions]
#d:$web_dirs -> ^version.php$ -> r:var \.RELEASE && r:'1.5' && r:'23'

[Web vulnerability - Outdated osCommerce (v2.2) installation] [any] [http://sucuri.net/latest-versions]
d:$web_dirs -> ^application_top.php$ -> r:'osCommerce 2.2-;


## Looking for known backdoors
[Web vulnerability - Backdoors / Web based malware found - eval(base64_decode] [any] []
d:$web_dirs -> .php$ -> r:eval\(base64_decode\(\paWYo;

[Web vulnerability - Backdoors / Web based malware found - eval(base64_decode(POST] [any] []
d:$web_dirs -> .php$ -> r:eval\(base64_decode\(\S_POST;

[Web vulnerability - .htaccess file compromised] [any] [http://blog.sucuri.net/2011/05/understanding-htaccess-attacks-part-1.html]
d:$web_dirs -> ^.htaccess$ -> r:RewriteCond \S+HTTP_REFERERS \S+google;

[Web vulnerability - .htaccess file compromised - auto append] [any] [http://blog.sucuri.net/2011/05/understanding-htaccess-attacks-part-1.html]
d:$web_dirs -> ^.htaccess$ -> r:php_value auto_append_file;


# EOF #
!14251 cis_rhel_linux_rcl.txt
# @(#) $Id: ./src/rootcheck/db/cis_rhel_linux_rcl.txt, 2011/09/08 dcid Exp $

#
# OSSEC Linux Audit - (C) 2008 Daniel B. Cid - dcid@ossec.net
#
# Released under the same license as OSSEC.
# More details at the LICENSE file included with OSSEC or online
# at: http://www.ossec.net/en/licensing.html
#
# [Application name] [any or all] [reference]
# type:<entry name>;
#
# Type can be:
#             - f (for file or directory)
#             - p (process running)
#             - d (any file inside the directory)
#
# Additional values:
# For the registry , use "->" to look for a specific entry and another
# "->" to look for the value.
# For files, use "->" to look for a specific value in the file.
#
# Values can be preceeded by: =: (for equal) - default
#                             r: (for ossec regexes)
#                             >: (for strcmp greater)
#                             <: (for strcmp  lower)
# Multiple patterns can be specified by using " && " between them.
# (All of them must match for it to return true).


# CIS Checks for Red Hat (RHEL 2.1, 3.0, 4.0 and Fedora Core 1,2,3,4 and 5).
# Based on CIS Benchmark for Red Hat Enterprise Linux v1.0.5



# RC scripts location
$rc_dirs=/etc/rc.d/rc2.d,/etc/rc.d/rc3.d,/etc/rc.d/rc4.d,/etc/rc.d/rc5.d;



# Main one. Only valid for Red Hat/Fedora.
[CIS - Testing against the CIS Red Hat Enterprise Linux Benchmark v1.0.5] [any required] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/redhat-release -> r:^Red Hat Enterprise Linux \S+ release 4;
f:/etc/redhat-release -> r:^Red Hat Enterprise Linux \S+ release 3;
f:/etc/redhat-release -> r:^Red Hat Enterprise Linux \S+ release 2.1;
f:/etc/fedora-release -> r:^Fedora && r:release 1;
f:/etc/fedora-release -> r:^Fedora && r:release 2;
f:/etc/fedora-release -> r:^Fedora && r:release 3;
f:/etc/fedora-release -> r:^Fedora && r:release 4;
f:/etc/fedora-release -> r:^Fedora && r:release 5;



# Build considerations - Partition scheme.
[CIS - Red Hat Linux - Build considerations - Robust partition scheme - /var is not on its own partition] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/fstab -> !r:/var;

[CIS - Red Hat Linux - Build considerations - Robust partition scheme - /home is not on its own partition] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/fstab -> !r:/home;




# Section 1.3 - SSH configuration
[CIS - Red Hat Linux 1.3 - SSH Configuration - Protocol version 1 enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/ssh/sshd_config -> !r:^# && r:Protocol\.+1;

[CIS - Red Hat Linux 1.3 - SSH Configuration - IgnoreRHosts disabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/ssh/sshd_config -> !r:^# && r:IgnoreRhosts\.+no;

[CIS - Red Hat Linux 1.3 - SSH Configuration - Empty passwords permitted] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/ssh/sshd_config -> !r:^# && r:^PermitEmptyPasswords\.+yes;

[CIS - Red Hat Linux 1.3 - SSH Configuration - Host based authentication enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/ssh/sshd_config -> !r:^# && r:HostbasedAuthentication\.+yes;

[CIS - Red Hat Linux 1.3 - SSH Configuration - Root login allowed] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/ssh/sshd_config -> !r:^# && r:PermitRootLogin\.+yes;



# Section 1.4 Enable system accounting
#[CIS - Red Hat Linux 1.4 - System Accounting - Sysstat not installed] [all] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
#f:!/var/log/sa;



# Section 2.5 Install and run Bastille
#[CIS - Red Hat Linux 1.5 - System harderning - Bastille is not installed] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
#f:!/etc/Bastille;



# Section 2 - Minimize xinetd services
[CIS - Red Hat Linux 2.3 - Telnet enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/xinetd.c/telnet -> !r:^# && r:disable && r:no;

[CIS - Red Hat Linux 2.4 - VSFTP enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/xinetd.c/vsftpd -> !r:^# && r:disable && r:no;

[CIS - Red Hat Linux 2.4 - WU-FTP enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/xinetd.c/wu-ftpd -> !r:^# && r:disable && r:no;

[CIS - Red Hat Linux 2.5 - rsh/rlogin/rcp enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/xinetd.c/rlogin -> !r:^# && r:disable && r:no;
f:/etc/xinetd.c/rsh -> !r:^# && r:disable && r:no;
f:/etc/xinetd.c/shell -> !r:^# && r:disable && r:no;

[CIS - Red Hat Linux 2.6 - tftpd enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/xinetd.c/tftpd -> !r:^# && r:disable && r:no;

[CIS - Red Hat Linux 2.7 - imap enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/xinetd.c/imap -> !r:^# && r:disable && r:no;
f:/etc/xinetd.c/imaps -> !r:^# && r:disable && r:no;

[CIS - Red Hat Linux 2.8 - pop3 enabled on xinetd] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/xinetd.c/ipop3 -> !r:^# && r:disable && r:no;
f:/etc/xinetd.c/pop3s -> !r:^# && r:disable && r:no;



# Section 3 - Minimize boot services
[CIS - Red Hat Linux 3.1 - Set daemon umask - Default umask is higher than 027] [all] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/init.d/functions -> !r:^# && r:^umask && >:umask 027;

[CIS - Red Hat Linux 3.4 - GUI login enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/inittab -> !r:^# && r:id:5;

[CIS - Red Hat Linux 3.7 - Disable standard boot services - Samba Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dsamba$;
d:$rc_dirs -> ^S\d\dsmb$;

[CIS - Red Hat Linux 3.8 - Disable standard boot services - NFS Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dnfs$;
d:$rc_dirs -> ^S\d\dnfslock$;

[CIS - Red Hat Linux 3.10 - Disable standard boot services - NIS Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dypbind$;
d:$rc_dirs -> ^S\d\dypserv$;

[CIS - Red Hat Linux 3.13 - Disable standard boot services - NetFS Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dnetfs$;

[CIS - Red Hat Linux 3.15 - Disable standard boot services - Apache web server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dapache$;
d:$rc_dirs -> ^S\d\dhttpd$;

[CIS - Red Hat Linux 3.15 - Disable standard boot services - TUX web server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dtux$;

[CIS - Red Hat Linux 3.16 - Disable standard boot services - SNMPD process Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dsnmpd$;

[CIS - Red Hat Linux 3.17 - Disable standard boot services - DNS server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dnamed$;

[CIS - Red Hat Linux 3.18 - Disable standard boot services - MySQL server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dmysqld$;

[CIS - Red Hat Linux 3.18 - Disable standard boot services - PostgreSQL server Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dpostgresql$;

[CIS - Red Hat Linux 3.19 - Disable standard boot services - Webmin Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dwebmin$;

[CIS - Red Hat Linux 3.20 - Disable standard boot services - Squid Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dsquid$;

[CIS - Red Hat Linux 3.21 - Disable standard boot services - Kudzu hardware detection Enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
d:$rc_dirs -> ^S\d\dkudzu$;



# Section 4 - Kernel tuning
[CIS - Red Hat Linux 4.1 - Network parameters - Source routing accepted] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/proc/sys/net/ipv4/conf/all/accept_source_route -> 1;

[CIS - Red Hat Linux 4.1 - Network parameters - ICMP broadcasts accepted] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/proc/sys/net/ipv4/icmp_echo_ignore_broadcasts -> 0;

[CIS - Red Hat Linux 4.2 - Network parameters - IP Forwarding enabled] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/proc/sys/net/ipv4/ip_forward -> 1;
f:/proc/sys/net/ipv6/ip_forward -> 1;



# Section 6 - Permissions
[CIS - Red Hat Linux 6.1 - Partition /var without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/fstab -> !r:^# && r:ext2|ext3 && r:/var && !r:nodev;

[CIS - Red Hat Linux 6.1 - Partition /tmp without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/fstab -> !r:^# && r:ext2|ext3 && r:/tmp && !r:nodev;

[CIS - Red Hat Linux 6.1 - Partition /opt without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/fstab -> !r:^# && r:ext2|ext3 && r:/opt && !r:nodev;

[CIS - Red Hat Linux 6.1 - Partition /home without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/fstab -> !r:^# && r:ext2|ext3 && r:/home && !r:nodev ;

[CIS - Red Hat Linux 6.2 - Removable partition /media without 'nodev' set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/fstab -> !r:^# && r:/media && !r:nodev;

[CIS - Red Hat Linux 6.2 - Removable partition /media without 'nosuid' set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/fstab -> !r:^# && r:/media && !r:nosuid;

[CIS - Red Hat Linux 6.3 - User-mounted removable partition allowed on the console] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/security/console.perms -> r:^<console>  \d+ <cdrom>;
f:/etc/security/console.perms -> r:^<console>  \d+ <floppy>;



# Section 7 - Access and authentication
[CIS - Red Hat Linux 7.8 - LILO Password not set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/lilo.conf -> !r:^# && !r:restricted;
f:/etc/lilo.conf -> !r:^# && !r:password=;

[CIS - Red Hat Linux 7.8 - GRUB Password not set] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/boot/grub/menu.lst -> !r:^# && !r:password;

[CIS - Red Hat Linux 8.2 - Account with empty password present] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/shadow -> r:^\w+::;

[CIS - Red Hat Linux SN.11 - Non-root account with uid 0] [any] [http://www.ossec.net/wiki/index.php/CIS_RHEL]
f:/etc/passwd -> !r:^# && !r:^root: && r:^\w+:\w+:0:;



# Tests specific for VMware ESX - Runs on Red Hat Linux
# Will not be tested anywhere else.
[VMware ESX - Testing against the Security Harderning benchmark VI3 for ESX 3.5] [any required] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
f:/etc/vmware-release -> r:^VMware ESX;


# Virtual Machine Files and Settings - 1
# 1.1
[VMware ESX - VM settings - Copy operation between guest and console enabled] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> !r:^isolation.tools.copy.disable;
d:/vmfs/volumes -> .vmx$ -> r:^isolation.tools.copy.disable && r:false;

# 1.2
[VMware ESX - VM settings - Paste operation between guest and console enabled] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> !r:^isolation.tools.paste.disable;
d:/vmfs/volumes -> .vmx$ -> r:^isolation.tools.paste.disable && r:false;

# 1.3
[VMware ESX - VM settings - GUI Options enabled] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> r:^isolation.tools.setGUIOptions.enable && r:true;

# 1.4
[VMware ESX - VM settings - Data Flow from the Virtual Machine to the Datastore not limited - Rotate size not 100KB] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> !r:^log.rotateSize;
d:/vmfs/volumes -> .vmx$ -> r:^log.rotateSize && !r:"100000";

# 1.5
[VMware ESX - VM settings - Data Flow from the Virtual Machine to the Datastore not limited - Maximum number of logs not 10] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> !r:^log.keepOld;
d:/vmfs/volumes -> .vmx$ -> r:^log.keepOld && r:"10";

# 1.6
[VMware ESX - VM settings - Data Flow from the Virtual Machine to the Datastore not limited - Guests allowed to write SetInfo data to config] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> !r:^isolation.tools.setinfo.disable;
d:/vmfs/volumes -> .vmx$ -> r:^isolation.tools.setinfo.disable && r:false;

# 1.7
[VMware ESX - VM settings - Nonpersistent Disks being used] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> r:^scsi\d:\d.mode && r:!independent-nonpersistent;

# 1.8
[VMware ESX - VM settings - Floppy drive present] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> r:^floppy\d+.present && r:!false;

[VMware ESX - VM settings - Serial port present] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> r:^serial\d+.present && r:!false;

[VMware ESX - VM settings - Parallel port present] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> r:^parallel\d+.present && r:!false;

# 1.9
[VMware ESX - VM settings - Unauthorized Removal or Connection of Devices allowed] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> !r:^Isolation.tools.connectable.disable;
d:/vmfs/volumes -> .vmx$ -> r:^Isolation.tools.connectable.disable && r:false;

# 1.10
[VMware ESX - VM settings - Avoid Denial of Service Caused by Virtual Disk Modification Operations - diskWiper enabled] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> !r:^isolation.tools.diskWiper.disable;
d:/vmfs/volumes -> .vmx$ -> r:^isolation.tools.diskWiper.disable && r:false;

[VMware ESX - VM settings - Avoid Denial of Service Caused by Virtual Disk Modification Operations - diskShrink enabled] [any] [http://www.ossec.net/wiki/index.php/SecurityHardening_VMwareESX]
d:/vmfs/volumes -> .vmx$ -> !r:^isolation.tools.diskShrink.disable;
d:/vmfs/volumes -> .vmx$ -> r:^isolation.tools.diskShrink.disable && r:false;


# Configuring the Service Console in ESX 3.5 - 2
# 2.1


# EOF
!14872 rootkit_files.txt
# @(#) $Id: ./src/rootcheck/db/rootkit_files.txt, 2011/09/08 dcid Exp $

#
# rootkit_files.txt, (C) Daniel B. Cid
# Imported from the rootcheck project.
#
# Lines starting with '#' are not going to be read.
# Blank lines are not going to be read too.
# 
# Each line must be in the following format:
# file_name ! Name ::Link to it

# Files that start with an '*' are going to be searched
# in the whole system.


# Bash door
tmp/mcliZokhb			! Bash door ::/rootkits/bashdoor.php
tmp/mclzaKmfa			! Bash door ::/rootkits/bashdoor.php


#adore Worm
dev/.shit/red.tgz		! Adore Worm ::/rootkits/adorew.php
usr/lib/libt			! Adore Worm ::/rootkits/adorew.php
usr/bin/adore			! Adore Worm ::/rootkits/adorew.php
*/klogd.o               ! Adore Worm ::/rootkits/adorew.php
*/red.tar               ! Adore Worm ::/rootkits/adorew.php


#T.R.K rootkit
usr/bin/soucemask		! TRK rootkit ::/rootkits/trk.php
usr/bin/sourcemask		! TRK rootkit ::/rootkits/trk.php


# 55.808.A Worm
tmp/.../a			    ! 55808.A Worm ::
tmp/.../r			    ! 55808.A Worm ::


# Volc Rootkit
usr/lib/volc			! Volc Rootkit ::
usr/bin/volc 			! Volc Rootkit ::


# Illogic
lib/security/.config	! Illogic Rootkit ::rootkits/illogic.php
usr/bin/sia			    ! Illogic Rootkit ::rootkits/illogic.php
etc/ld.so.hash			! Illogic Rootkit ::rootkits/illogic.php
*/uconf.inv 			! Illogic Rootkit ::rootkits/illogic.php


#T0rnkit installed
usr/src/.puta			! t0rn Rootkit ::rootkits/torn.php 
usr/info/.t0rn			! t0rn Rootkit ::rootkits/torn.php
lib/ldlib.tk			! t0rn Rootkit ::rootkits/torn.php
etc/ttyhash			    ! t0rn Rootkit ::rootkits/torn.php
sbin/xlogin			    ! t0rn Rootkit ::rootkits/torn.php
*/ldlib.tk              ! t0rn Rootkit ::rootkits/torn.php
*/.t0rn                 ! t0rn Rootkit ::rootkits/torn.php
*/.puta                 ! t0rn Rootkit ::rootkits/torn.php


#RK17
bin/rtty			! RK17 ::
bin/squit			! RK17 ::
sbin/pback			! RK17 ::
proc/kset			! RK17 ::
usr/src/linux/modules/autod.o	! RK17 ::
usr/src/linux/modules/soundx.o	! RK17 ::


# Ramen Worm
usr/lib/ldlibps.so 		! Ramen Worm ::rootkits/ramen.php
usr/lib/ldlibns.so 		! Ramen Worm ::rootkits/ramen.php
usr/lib/ldliblogin.so 	! Ramen Worm ::rootkits/ramen.php
usr/src/.poop			! Ramen Worm ::rootkits/ramen.php
tmp/ramen.tgz			! Ramen Worm ::rootkits/ramen.php
etc/xinetd.d/asp		! Ramen Worm ::rootkits/ramen.php


# Sadmind/IIS Worm
dev/cuc				    ! Sadmind/IIS Worm ::


#Monkit
lib/defs		    	! Monkit ::
usr/lib/libpikapp.a		! Monkit found ::


#RSHA
usr/bin/kr4p 			! RSHA ::
usr/bin/n3tstat			! RSHA ::
usr/bin/chsh2			! RSHA ::
usr/bin/slice2			! RSHA ::
etc/rc.d/rsha			! RSHA ::


#ShitC worm
bin/home			    ! ShitC ::
sbin/home			    ! ShitC ::
usr/sbin/in.slogind		! ShitC ::


#Omega Worm
dev/chr				    ! Omega Worm ::


#rh-sharpe
bin/.ps				    ! Rh-Sharpe ::
usr/bin/cleaner			! Rh-Sharpe ::
usr/bin/slice			! Rh-Sharpe ::
usr/bin/vadim			! Rh-Sharpe ::
usr/bin/.ps			    ! Rh-Sharpe ::
bin/.lpstree			! Rh-Sharpe ::
usr/bin/.lpstree		! Rh-Sharpe ::
usr/bin/lnetstat		! Rh-Sharpe ::
bin/lnetstat			! Rh-Sharpe ::
usr/bin/ldu			    ! Rh-Sharpe ::
bin/ldu				    ! Rh-Sharpe ::
usr/bin/lkillall		! Rh-Sharpe ::
bin/lkillall			! Rh-Sharpe ::
usr/include/rpcsvc/du	! Rh-Sharpe ::


#Maniac RK 
usr/bin/mailrc			! Maniac RK ::


#Showtee / romaniam
usr/lib/.egcs			! Showtee ::
usr/lib/.wormie			! Showtee ::
usr/lib/.kinetic		! Showtee ::
usr/lib/liblog.o		! Showtee ::
usr/include/addr.h		! Showtee / Romanian rootkit ::
usr/include/cron.h		! Showtee ::
usr/include/file.h		! Showtee / Romaniam rootkit ::
usr/include/syslogs.h	! Showtee / Romaniam rootkit ::
usr/include/proc.h		! Showtee / Romaniam rootkit ::
usr/include/chk.h		! Showtee ::
usr/sbin/initdl			! Romanian rootkit ::
usr/sbin/xntps			! Romanian rootkit ::


#Optickit
usr/bin/xchk			! Optickit ::
usr/bin/xsf			    ! Optickit ::


# LDP worm 
dev/.kork			! LDP Worm ::
bin/.login			! LDP Worm ::
bin/.ps				! LDP Worm ::


# Telekit
dev/hda06			! TeLeKit trojan ::
usr/info/libc1.so 		! TeleKit trojan ::


# Tribe bot
dev/wd4 			! Tribe bot ::


# LRK
dev/ida/.inet 			! LRK rootkit ::rootkits/lrk.php
*/bindshell 			! LRK rootkit ::rootkits/lrk.php


# Adore Rootkit
etc/bin/ava 			! Adore Rootkit ::
etc/sbin/ava 			! Adore Rootkit ::


# Slapper
tmp/.bugtraq 			! Slapper installed ::
tmp/.bugtraq.c 			! Slapper installed ::
tmp/.cinik 			    ! Slapper installed ::
tmp/.b 				    ! Slapper installed ::
tmp/httpd 			    ! Slapper installed ::
tmp./update 			! Slapper installed ::
tmp/.unlock 			! Slapper installed ::
tmp/.font-unix/.cinik   ! Slapper installed ::
tmp/.cinik              ! Slapper installed ::



# Scalper
tmp/.uua 			! Scalper installed ::
tmp/.a 				! Scalper installed ::


# Knark 
proc/knark 			! Knark Installed ::rootkits/knark.php
dev/.pizda 			! Knark Installed ::rootkits/knark.php
dev/.pula 			! Knark Installed ::rootkits/knark.php
dev/.pula 			! Knark Installed ::rootkits/knark.php
*/taskhack          ! Knark Installed ::rootkits/knark.php
*/rootme            ! Knark Installed ::rootkits/knark.php
*/nethide           ! Knark Installed ::rootkits/knark.php
*/hidef             ! Knark Installed ::rootkits/knark.php
*/ered              ! Knark Installed ::rootkits/knark.php


# Lion worm
dev/.lib 			! Lion Worm ::rootkits/lion.php
dev/.lib/1iOn.sh 	! Lion Worm ::rootkits/lion.php
bin/mjy				! Lion Worm ::rootkits/lion.php
bin/in.telnetd		! Lion Worm ::rootkits/lion.php
usr/info/torn		! Lion Worm ::rootkits/lion.php
*/1iOn\.sh  		! Lion Worm ::rootkits/lion.php


# Bobkit
usr/include/.../		! Bobkit Rootkit ::rootkits/bobkit.php
usr/lib/.../			! Bobkit Rootkit ::rootkits/bobkit.php
usr/sbin/.../			! Bobkit Rootkit ::rootkits/bobkit.php
usr/bin/ntpsx			! Bobkit Rootkit ::rootkits/bobkit.php
tmp/.bkp			    ! Bobkit Rootkit ::rootkits/bobkit.php
usr/lib/.bkit-		    ! Bobkit Rootkit ::rootkits/bobkit.php
*/bkit-	    		    ! Bobkit Rootkit ::rootkits/bobkit.php

# Hidrootkit
var/lib/games/.k		! Hidr00tkit ::

 
# Ark
dev/ptyxx			! Ark rootkit ::


#Mithra Rootkit
usr/lib/locale/uboot 		! Mithra`s rootkit ::


# Optickit
usr/bin/xsf 			! OpticKit ::
usr/bin/xchk 			! OpticKit ::


# LOC rookit
tmp/xp 				! LOC rookit ::
tmp/kidd0.c 			! LOC rookit ::
tmp/kidd0 			! LOC rookit ::


# TC2 worm
usr/info/.tc2k	 		! TC2 Worm ::
usr/bin/util 			! TC2 Worm ::
usr/sbin/initcheck 		! TC2 Worm ::
usr/sbin/ldb 			! TC2 Worm ::


# Anonoiyng rootkit
usr/sbin/mech 			! Anonoiyng rootkit ::
usr/sbin/kswapd 		! Anonoiyng rootkit ::


# SuckIt
lib/.x				! SuckIt rootkit ::
*/hide.log          ! Suckit rootkit ::
lib/sk              ! SuckIT rootkit ::


# Beastkit
usr/local/bin/bin		! Beastkit rootkit ::rootkits/beastkit.php
usr/man/.man10			! Beastkit rootkit ::rootkits/beastkit.php
usr/sbin/arobia			! Beastkit rootkit ::rootkits/beastkit.php
usr/lib/elm/arobia		! Beastkit rootkit ::rootkits/beastkit.php
usr/local/bin/.../bktd	! Beastkit rootkit ::rootkits/beastkit.php


# Tuxkit
dev/tux				! Tuxkit rootkit ::rootkits/Tuxkit.php
usr/bin/xsf			! Tuxkit rootkit ::rootkits/Tuxkit.php
usr/bin/xchk		! Tuxkit rootkit ::rootkits/Tuxkit.php
*/.file             ! Tuxkit rootkit ::rootkits/Tuxkit.php
*/.addr             ! Tuxkit rootkit ::rootkits/Tuxkit.php


# Old rootkits
usr/include/rpc/ ../kit		! Old rootkits ::rootkits/Old.php
usr/include/rpc/ ../kit2	! Old rootkits ::rootkits/Old.php
usr/doc/.sl			    ! Old rootkits ::rootkits/Old.php
usr/doc/.sp			    ! Old rootkits ::rootkits/Old.php
usr/doc/.statnet		! Old rootkits ::rootkits/Old.php
usr/doc/.logdsys		! Old rootkits ::rootkits/Old.php
usr/doc/.dpct			! Old rootkits ::rootkits/Old.php
usr/doc/.gifnocfi		! Old rootkits ::rootkits/Old.php
usr/doc/.dnif			! Old rootkits ::rootkits/Old.php
usr/doc/.nigol			! Old rootkits ::rootkits/Old.php


# Kenga3 rootkit
usr/include/. .         ! Kenga3 rootkit


# ESRK rootkit
usr/lib/tcl5.3          ! ESRK rootkit


# Fu rootkit
sbin/xc                 ! Fu rootkit
usr/include/ivtype.h    ! Fu rootkit
bin/.lib                ! Fu rootkit


# ShKit rootkit
lib/security/.config    ! ShKit rootkit
etc/ld.so.hash          ! ShKit rootkit


# AjaKit rootkit
lib/.ligh.gh            ! AjaKit rootkit
lib/.libgh.gh           ! AjaKit rootkit
lib/.libgh-gh           ! AjaKit rootkit
dev/tux                 ! AjaKit rootkit
dev/tux/.proc           ! AjaKit rootkit
dev/tux/.file           ! AjaKit rootkit


# zaRwT rootkit
bin/imin                ! zaRwT rootkit
bin/imout               ! zaRwT rootkit


# Madalin rootkit
usr/include/icekey.h    ! Madalin rootkit
usr/include/iceconf.h   ! Madalin rootkit
usr/include/iceseed.h   ! Madalin rootkit


# shv5 rootkit XXX http://www.askaboutskating.com/forum/.../shv5/setup
lib/libsh.so            ! shv5 rootkit
usr/lib/libsh           ! shv5 rootkit


# BMBL rootkit (http://www.giac.com/practical/GSEC/Steve_Terrell_GSEC.pdf)
etc/.bmbl               ! BMBL rootkit
etc/.bmbl/sk            ! BMBL rootkit


# rootedoor rootkit
*/rootedoor             ! Rootedoor rootkit


# 0vason rootkit
*/ovas0n                ! ovas0n rootkit ::/rootkits/ovason.php
*/ovason                ! ovas0n rootkit ::/rootkits/ovason.php


# Rpimp reverse telnet
*/rpimp                 ! rpv21 (Reverse Pimpage)::/rootkits/rpimp.php


# Cback Linux worm
tmp/cback              ! cback worm ::/rootkits/cback.php
tmp/derfiq             ! cback worm ::/rootkits/cback.php


# aPa Kit (from rkhunter)
usr/share/.aPa          ! Apa Kit


# enye-sec Rootkit
etc/.enyelkmHIDE^IT.ko  ! enye-sec Rootkit ::/rootkits/enye-sec.php


# Override Rootkit
dev/grid-hide-pid-     ! Override rootkit ::/rootkits/override.php
dev/grid-unhide-pid-   ! Override rootkit ::/rootkits/override.php
dev/grid-show-pids     ! Override rootkit ::/rootkits/override.php
dev/grid-hide-port-    ! Override rootkit ::/rootkits/override.php
dev/grid-unhide-port-  ! Override rootkit ::/rootkits/override.php


# PHALANX rootkit
usr/share/.home*        ! PHALANX rootkit ::
usr/share/.home*/tty    ! PHALANX rootkit ::
etc/host.ph1            ! PHALANX rootkit ::
bin/host.ph1            ! PHALANX rootkit ::


# ZK rootkit (http://honeyblog.org/junkyard/reports/redhat-compromise2.pdf)
# and from chkrootkit
usr/share/.zk                   ! ZK rootkit ::
usr/share/.zk/zk                ! ZK rootkit ::
etc/1ssue.net                   ! ZK rootkit ::
usr/X11R6/.zk                   ! ZK rootkit ::
usr/X11R6/.zk/xfs               ! ZK rootkit ::
usr/X11R6/.zk/echo              ! ZK rootkit ::
etc/sysconfig/console/load.zk   ! ZK rootkit ::


# Public sniffers
*/.linux-sniff          ! Sniffer log ::
*/sniff-l0g             ! Sniffer log ::
*/core_$                ! Sniffer log ::
*/tcp.log               ! Sniffer log ::
*/chipsul               ! Sniffer log ::
*/beshina               ! Sniffer log ::
*/.owned$               | Sniffer log ::


# Solaris worm -
# http://blogs.sun.com/security/entry/solaris_in_telnetd_worm_seen
var/adm/.profile        ! Solaris Worm ::
var/spool/lp/.profile   ! Solaris Worm ::
var/adm/sa/.adm         ! Solaris Worm ::
var/spool/lp/admins/.lp ! Solaris Worm ::


#Suspicious files
etc/rc.d/init.d/rc.modules	! Suspicious file ::rootkits/Suspicious.php
lib/ldd.so			        ! Suspicious file ::rootkits/Suspicious.php
usr/man/muie			    ! Suspicious file ::rootkits/Suspicious.php
usr/X11R6/include/pain		! Suspicious file ::rootkits/Suspicious.php
usr/bin/sourcemask 		    ! Suspicious file ::rootkits/Suspicious.php
usr/bin/ras2xm			    ! Suspicious file ::rootkits/Suspicious.php
usr/bin/ddc			        ! Suspicious file ::rootkits/Suspicious.php
usr/bin/jdc			        ! Suspicious file ::rootkits/Suspicious.php
usr/sbin/in.telnet		    ! Suspicious file ::rootkits/Suspicious.php
sbin/vobiscum			    ! Suspicious file ::rootkits/Suspicious.php
usr/sbin/jcd			    ! Suspicious file ::rootkits/Suspicious.php
usr/sbin/atd2			    ! Suspicious file ::rootkits/Suspicious.php
usr/bin/ishit               ! Suspicious file ::rootkits/Suspicious.php
usr/bin/.etc	            ! Suspicious file ::rootkits/Suspicious.php
usr/bin/xstat			    ! Suspicious file ::rootkits/Suspicious.php
var/run/.tmp			    ! Suspicious file ::rootkits/Suspicious.php
usr/man/man1/lib/.lib		! Suspicious file ::rootkits/Suspicious.php
usr/man/man2/.man8 		    ! Suspicious file ::rootkits/Suspicious.php
var/run/.pid			    ! Suspicious file ::rootkits/Suspicious.php
lib/.so				        ! Suspicious file ::rootkits/Suspicious.php
lib/.fx				        ! Suspicious file ::rootkits/Suspicious.php
lib/lblip.tk			    ! Suspicious file ::rootkits/Suspicious.php
usr/lib/.fx			        ! Suspicious file ::rootkits/Suspicious.php
var/local/.lpd			    ! Suspicious file ::rootkits/Suspicious.php
dev/rd/cdb			        ! Suspicious file ::rootkits/Suspicious.php
dev/.rd/			        ! Suspicious file ::rootkits/Suspicious.php
usr/lib/pt07			    ! Suspicious file ::rootkits/Suspicious.php
usr/bin/atm			        ! Suspicious file ::rootkits/Suspicious.php
tmp/.cheese			        ! Suspicious file ::rootkits/Suspicious.php
dev/.arctic			        ! Suspicious file ::rootkits/Suspicious.php
dev/.xman			        ! Suspicious file ::rootkits/Suspicious.php
dev/.golf			        ! Suspicious file ::rootkits/Suspicious.php
dev/srd0			        ! Suspicious file ::rootkits/Suspicious.php
dev/ptyzx			        ! Suspicious file ::rootkits/Suspicious.php
dev/ptyzg			        ! Suspicious file ::rootkits/Suspicious.php
dev/xdf1			        ! Suspicious file ::rootkits/Suspicious.php
dev/ttyop			        ! Suspicious file ::rootkits/Suspicious.php
dev/ttyof			        ! Suspicious file ::rootkits/Suspicious.php
dev/hd7				        ! Suspicious file ::rootkits/Suspicious.php
dev/hdx1			        ! Suspicious file ::rootkits/Suspicious.php
dev/hdx2			        ! Suspicious file ::rootkits/Suspicious.php
dev/xdf2			        ! Suspicious file ::rootkits/Suspicious.php
dev/ptyp			        ! Suspicious file ::rootkits/Suspicious.php
dev/ptyr			        ! Suspicious file ::rootkits/Suspicious.php
sbin/pback                  ! Suspicious file ::rootkits/Suspicious.php
usr/man/man3/psid           ! Suspicious file ::rootkits/Suspicious.php
proc/kset                   ! Suspicious file ::rootkits/Suspicious.php
usr/bin/gib                 ! Suspicious file ::rootkits/Suspicious.php
usr/bin/snick               ! Suspicious file ::rootkits/Suspicious.php
usr/bin/kfl                 ! Suspicious file ::rootkits/Suspicious.php
tmp/.dump                   ! Suspicious file ::rootkits/Suspicious.php
var/.x                      ! Suspicious file ::rootkits/Suspicious.php
var/.x/psotnic              ! Suspicious file ::rootkits/Suspicious.php
*/.log                      ! Suspicious file ::rootkits/Suspicious.php
*/ecmf                      ! Suspicious file ::rootkits/Suspicious.php
*/mirkforce                 ! Suspicious file ::rootkits/Suspicious.php
*/mfclean                   ! Suspicious file ::rootkits/Suspicious.php
!3859 win_audit_rcl.txt
# @(#) $Id: ./src/rootcheck/db/win_audit_rcl.txt, 2011/09/08 dcid Exp $

#
# OSSEC Windows Audit - (C) 2007 Daniel B. Cid - dcid@ossec.net
#
# Released under the same license as OSSEC.
# More details at the LICENSE file included with OSSEC or online
# at: http://www.ossec.net/en/licensing.html
#
# [Application name] [any or all] [reference]
# type:<entry name>;
#
# Type can be:
#             - f (for file or directory)
#             - r (registry entry)
#             - p (process running)
#
# Additional values:
# For the registry , use "->" to look for a specific entry and another
# "->" to look for the value.
# For files, use "->" to look for a specific value in the file.
#
# Values can be preceeded by: =: (for equal) - default
#                             r: (for ossec regexes)
#                             >: (for strcmp greater)
#                             <: (for strcmp  lower)
# Multiple patterns can be specified by using " && " between them.
# (All of them must match for it to return true).
 



# http://technet2.microsoft.com/windowsserver/en/library/486896ba-dfa1-4850-9875-13764f749bba1033.mspx?mfr=true
[Disabled Registry tools set] [any] []
r:HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System -> DisableRegistryTools -> 1; 
r:HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System -> DisableRegistryTools -> 1; 



# http://support.microsoft.com/kb/825750
[DCOM disabled] [any] []
r:HKEY_LOCAL_MACHINE\Software\Microsoft\OLE -> EnableDCOM -> N;



# http://web.mit.edu/is/topics/windows/server/winmitedu/security.html
[LM authentication allowed (weak passwords)] [any] []
r:HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\LSA -> LMCompatibilityLevel -> 0;
r:HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\LSA -> LMCompatibilityLevel -> 1;



# http://research.eeye.com/html/alerts/AL20060813.html
# Disabled by some Malwares (sometimes by McAfee and Symantec
# security center too).
[Firewall/Anti Virus notification disabled] [any] []
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Security Center -> FirewallDisableNotify -> !0;
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Security Center -> antivirusoverride -> !0;
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Security Center -> firewalldisablenotify -> !0;
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Security Center -> firewalldisableoverride -> !0;



# Checking for the microsoft firewall.
[Microsoft Firewall disabled] [all] []
r:HKEY_LOCAL_MACHINE\software\policies\microsoft\windowsfirewall\domainprofile -> enablefirewall -> 0;
r:HKEY_LOCAL_MACHINE\software\policies\microsoft\windowsfirewall\standardprofile -> enablefirewall -> 0;



#http://web.mit.edu/is/topics/windows/server/winmitedu/security.html
[Null sessions allowed] [any] []
r:HKLM\System\CurrentControlSet\Control\Lsa -> RestrictAnonymous -> 0;



[Error reporting disabled] [any] [http://windowsir.blogspot.com/2007/04/something-new-to-look-for.html]
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PCHealth\ErrorReporting -> DoReport -> 0;
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PCHealth\ErrorReporting -> IncludeKernelFaults -> 0;
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PCHealth\ErrorReporting -> IncludeMicrosoftApps -> 0;
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PCHealth\ErrorReporting -> IncludeWindowsApps -> 0;
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PCHealth\ErrorReporting -> IncludeShutdownErrs -> 0;
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\PCHealth\ErrorReporting -> ShowUI -> 0;



# http://support.microsoft.com/default.aspx?scid=315231
[Automatic Logon enabled] [any] [http://support.microsoft.com/default.aspx?scid=315231]
r:HKLM\SOFTWARE\Microsoft\WindowsNT\CurrentVersion\Winlogon -> DefaultPassword;
r:HKLM\SOFTWARE\Microsoft\WindowsNT\CurrentVersion\Winlogon -> AutoAdminLogon -> 1;


[Winpcap packet filter driver found] [any] []
f:%WINDIR%\System32\drivers\npf.sys;


# EOF #
!4682 win_applications_rcl.txt
# @(#) $Id: ./src/rootcheck/db/win_applications_rcl.txt, 2011/09/08 dcid Exp $

#
# OSSEC Application detection - (C) 2007 Daniel B. Cid - dcid@ossec.net
#
# Released under the same license as OSSEC.
# More details at the LICENSE file included with OSSEC or online
# at: http://www.ossec.net/en/licensing.html
# 
# [Application name] [any or all] [reference]
# type:<entry name>;
#
# Type can be:
#             - f (for file or directory)
#             - r (registry entry)
#             - p (process running)
#
# Additional values:
# For the registry , use "->" to look for a specific entry and another
# "->" to look for the value. 
# For files, use "->" to look for a specific value in the file.
# 
# Values can be preceeded by: =: (for equal) - default
#                             r: (for ossec regexes)
#                             >: (for strcmp greater)
#                             <: (for strcmp  lower)
# Multiple patterns can be specified by using " && " between them.
# (All of them must match for it to return true).



[Chat/IM/VoIP - Skype] [any] []
f:\Program Files\Skype\Phone;
f:\Documents and Settings\All Users\Documents\My Skype Pictures;
f:\Documents and Settings\Skype;
f:\Documents and Settings\All Users\Start Menu\Programs\Skype;
r:HKLM\SOFTWARE\Skype;
r:HKEY_LOCAL_MACHINE\Software\Policies\Skype;
p:r:Skype.exe;


[Chat/IM - Yahoo] [any] []
f:\Documents and Settings\All Users\Start Menu\Programs\Yahoo! Messenger;
r:HKLM\SOFTWARE\Yahoo;


[Chat/IM - ICQ] [any] []
r:HKEY_CURRENT_USER\Software\Mirabilis\ICQ;


[Chat/IM - AOL] [any] [http://www.aol.com]
r:HKEY_LOCAL_MACHINE\SOFTWARE\America Online\AOL Instant Messenger;
r:HKEY_CLASSES_ROOT\aim\shell\open\command;
r:HKEY_CLASSES_ROOT\AIM.Protocol;
r:HKEY_CLASSES_ROOT\MIME\Database\Content Type\application/x-aim;
f:\Program Files\AIM95;
p:r:aim.exe;


[Chat/IM - MSN] [any] [http://www.msn.com]
r:HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\MSNMessenger;
r:HKEY_CURRENT_USER\SOFTWARE\Microsoft\MSNMessenger;
f:\Program Files\MSN Messenger;
f:\Program Files\Messenger;
p:r:msnmsgr.exe;


[Chat/IM - ICQ] [any] [http://www.icq.com]
r:HKLM\SOFTWARE\Mirabilis\ICQ;


[P2P - UTorrent] [any] []
p:r:utorrent.exe;


[P2P - LimeWire] [any] []
r:HKEY_LOCAL_MACHINE\SOFTWARE\Limewire;
r:HKLM\software\microsoft\windows\currentversion\run -> limeshop;
f:\Program Files\limewire;
f:\Program Files\limeshop;


[P2P/Adware - Kazaa] [any] []
f:\Program Files\kazaa;
f:\Documents and Settings\All Users\Start Menu\Programs\kazaa;
f:\Documents and Settings\All Users\DESKTOP\Kazaa Media Desktop.lnk;
f:\Documents and Settings\All Users\DESKTOP\Kazaa Promotions.lnk;
f:%WINDIR%\System32\Cd_clint.dll;
r:HKEY_LOCAL_MACHINE\SOFTWARE\KAZAA;
r:HKEY_CURRENT_USER\SOFTWARE\KAZAA;
r:HKEY_LOCAL_MACHINE\SOFTWARE\MICROSOFT\WINDOWS\CURRENTVERSION\RUN\KAZAA;


# http://vil.nai.com/vil/content/v_135023.htm
[Adware - RxToolBar] [any] [http://vil.nai.com/vil/content/v_135023.htm]
r:HKEY_CURRENT_USER\Software\Infotechnics;
r:HKEY_CURRENT_USER\Software\Infotechnics\RX Toolbar;
r:HKEY_CURRENT_USER\Software\RX Toolbar;
r:HKEY_CLASSES_ROOT\BarInfoUrl.TBInfo;
r:HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\RX Toolbar;
f:\Program Files\RXToolBar;


# http://btfaq.com/serve/cache/18.html
[P2P - BitTorrent] [any] [http://btfaq.com/serve/cache/18.html]
f:\Program Files\BitTorrent;
r:HKEY_CLASSES_ROOT\.torrent;
r:HKEY_CLASSES_ROOT\MIME\Database\Content Type\application/x-bittorrent;
r:HKEY_CLASSES_ROOT\bittorrent;
r:HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\BitTorrent;


# http://www.gotomypc.com
[Remote Access - GoToMyPC] [any] []
f:\Program Files\Citrix\GoToMyPC;
f:\Program Files\Citrix\GoToMyPC\g2svc.exe;
f:\Program Files\Citrix\GoToMyPC\g2comm.exe;
f:\Program Files\expertcity\GoToMyPC;
r:HKLM\software\microsoft\windows\currentversion\run -> gotomypc;
r:HKEY_LOCAL_MACHINE\software\citrix\gotomypc;
r:HKEY_LOCAL_MACHINE\system\currentcontrolset\services\gotomypc;
p:r:g2svc.exe;
p:r:g2pre.exe;


[Spyware - Twain Tec Spyware] [any] []
r:HKEY_LOCAL_MACHINE\SOFTWARE\Classes\TwaintecDll.TwaintecDllObj.1;
r:HKEY_LOCAL_MACHINE\SOFTWARE\twaintech;
f:%WINDIR%\twaintec.dll;


# http://www.symantec.com/security_response/writeup.jsp?docid=2004-062611-4548-99&tabid=2
[Spyware - SpyBuddy] [any] []
f:\Program Files\ExploreAnywhere\SpyBuddy\sb32mon.exe;
f:\Program Files\ExploreAnywhere\SpyBuddy;
f:\Program Files\ExploreAnywhere;
f:%WINDIR%\System32\sysicept.dll;
r:HKEY_LOCAL_MACHINE\Software\ExploreAnywhere Software\SpyBuddy;


[Spyware - InternetOptimizer] [any] []
r:HKLM\SOFTWARE\Avenue Media;
r:HKEY_CLASSES_ROOT\\safesurfinghelper.iebho.1;
r:HKEY_CLASSES_ROOT\\safesurfinghelper.iebho;


# EOF #
!77 ar.conf
restart-ossec0 - restart-ossec.sh - 0
restart-ossec0 - restart-ossec.cmd - 0
!5193 rootkit_trojans.txt
# @(#) $Id: ./src/rootcheck/db/rootkit_trojans.txt, 2012/04/26 dcid Exp $

#
# rootkit_trojans.txt, (C) Daniel B. Cid
# Imported from the rootcheck project.
# Some entries taken from the chkrootkit project.
#
# Lines starting with '#' are not going to be read (comments).
# Blank lines are not going to be read too.
# 
# Each line must be in the following format:
# file_name !string_to_search!Description

# Commom binaries and public trojan entries
ls          !bash|^/bin/sh|dev/[^clu]|\.tmp/lsfile|duarawkz|/prof|/security|file\.h!
env			!bash|^/bin/sh|file\.h|proc\.h|/dev/|^/bin/.*sh!
echo		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^cl]|^/bin/.*sh!
chown		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^cl]|^/bin/.*sh!
chmod		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^cl]|^/bin/.*sh!
chgrp		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^cl]|^/bin/.*sh!
cat			!bash|^/bin/sh|file\.h|proc\.h|/dev/[^cl]|^/bin/.*sh!
bash		!proc\.h|/dev/[0-9]|/dev/[hijkz]!
sh			!proc\.h|/dev/[0-9]|/dev/[hijkz]!
uname		!bash|^/bin/sh|file\.h|proc\.h|^/bin/.*sh!
date		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^cln]|^/bin/.*sh!
du			!w0rm|/prof|file\.h!
df			!bash|^/bin/sh|file\.h|proc\.h|/dev/[^clurdv]|^/bin/.*sh!
login      	!elite|SucKIT|xlogin|vejeta|porcao|lets_log|sukasuk!
passwd		!bash|file\.h|proc\.h|/dev/ttyo|/dev/[A-Z]|/dev/[b-s,uvxz]!
mingetty	!bash|Dimensioni|pacchetto!
chfn		!bash|file\.h|proc\.h|/dev/ttyo|/dev/[A-Z]|/dev/[a-s,uvxz]!
chsh		!bash|file\.h|proc\.h|/dev/ttyo|/dev/[A-Z]|/dev/[a-s,uvxz]!
mail		!bash|file\.h|proc\.h|/dev/[^nu]!
su			!/dev/[d-s,abuvxz]|/dev/[A-D]|/dev/[F-Z]|/dev/[0-9]|satori|vejeta|conf\.inv!
sudo		!satori|vejeta|conf\.inv!
crond		!/dev/[^nt]|bash!
gpm			!bash|mingetty!
ifconfig	!bash|^/bin/sh|/dev/tux|session.null|/dev/[^cludisopt]!
diff		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^n]|^/bin/.*sh!
md5sum		!bash|^/bin/sh|file\.h|proc\.h|/dev/|^/bin/.*sh!
hdparm		!bash|/dev/ida!
ldd			!/dev/[^n]|proc\.h|libshow.so|libproc.a!


# Trojan entries for troubleshooting binaries

grep        !bash|givemer|/dev/!
egrep		!bash|^/bin/sh|file\.h|proc\.h|/dev/|^/bin/.*sh!
find		!bash|/dev/[^tnlcs]|/prof|/home/virus|file\.h!
lsof		!/prof|/dev/[^apcmnfk]|proc\.h|bash|^/bin/sh|/dev/ttyo|/dev/ttyp!
netstat		!bash|^/bin/sh|/dev/[^aik]|/prof|grep|addr\.h!
top			!/dev/[^npi3st%]|proc\.h|/prof/!
ps			!/dev/ttyo|\.1proc|proc\.h|bash|^/bin/sh!
tcpdump		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^bu]|^/bin/.*sh!
pidof		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^f]|^/bin/.*sh!
fuser		!bash|^/bin/sh|file\.h|proc\.h|/dev/[a-dtz]|^/bin/.*sh!
w			!uname -a|proc\.h|bash!


# Trojan entries for common daemons

sendmail	!bash|fuck!
named		!bash|blah|/dev/[0-9]|^/bin/sh!
inetd		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^un%]|^/bin/.*sh!
apachectl	!bash|^/bin/sh|file\.h|proc\.h|/dev/[^n]|^/bin/.*sh!
sshd		!check_global_passwd|panasonic|satori|vejeta|\.ark|/hash\.zk|bash|/dev[a-s]|/dev[A-Z]/!
syslogd		!bash|/usr/lib/pt07|/dev/[^cln]]|syslogs\.h|proc\.h!
xinetd		!bash|file\.h|proc\.h!
in.telnetd	!cterm100|vt350|VT100|ansi-term|bash|^/bin/sh|/dev[A-R]|/dev/[a-z]/!
in.fingerd	!bash|^/bin/sh|cterm100|/dev/!
identd		!bash|^/bin/sh|file\.h|proc\.h|/dev/[^n]|^/bin/.*sh!
init		!bash|/dev/h
tcpd		!bash|proc\.h|p1r0c4|hack|/dev/[^n]!
rlogin		!p1r0c4|r00t|bash|/dev/[^nt]!


# Kill trojan

killall		!/dev/[^t%]|proc\.h|bash|tmp!
kill		!/dev/[ab,d-k,m-z]|/dev/[F-Z]|/dev/[A-D]|/dev/[0-9]|proc\.h|bash|tmp!


# Rootkit entries
/etc/rc.d/rc.sysinit    !enyelkmHIDE! enye-sec Rootkit


# ZK rootkit (http://honeyblog.org/junkyard/reports/redhat-compromise2.pdf)
/etc/sysconfig/console/load.zk   !/bin/sh! ZK rootkit
/etc/sysconfig/console/load.zk   !usr/bin/run! ZK rootkit


# Modified /etc/hosts entries
# Idea taken from:
# http://blog.tenablesecurity.com/2006/12/detecting_compr.html
# http://www.sophos.com/security/analyses/trojbagledll.html
# http://www.f-secure.com/v-descs/fantibag_b.shtml
/etc/hosts  !^[^#]*avp.ch!Anti-virus site on the hosts file
/etc/hosts  !^[^#]*avp.ru!Anti-virus site on the hosts file
/etc/hosts  !^[^#]*awaps.net! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*ca.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*mcafee.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*microsoft.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*f-secure.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*sophos.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*symantec.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*my-etrust.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*nai.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*networkassociates.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*viruslist.ru! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*kaspersky! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*symantecliveupdate.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*grisoft.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*clamav.net! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*bitdefender.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*antivirus.com! Anti-virus site on the hosts file
/etc/hosts  !^[^#]*sans.org! Security site on the hosts file

# EOF #
!4929 win_malware_rcl.txt
# @(#) $Id: ./src/rootcheck/db/win_malware_rcl.txt, 2011/09/08 dcid Exp $

#
# OSSEC Windows Malware list - (C) 2007 Daniel B. Cid - dcid@ossec.net
#
# Released under the same license as OSSEC.
# More details at the LICENSE file included with OSSEC or online
# at: http://www.ossec.net/en/licensing.html
#
# [Malware name] [any or all] [reference]
# type:<entry name>;
#
# Type can be:
#             - f (for file or directory)
#             - r (registry entry)
#             - p (process running)
#
# Additional values:
# For the registry , use "->" to look for a specific entry and another
# "->" to look for the value. 
# For files, use "->" to look for a specific value in the file.
#
# # Values can be preceeded by: =: (for equal) - default
#                               r: (for ossec regexes)
#                               >: (for strcmp greater)
#                               <: (for strcmp  lower)
# Multiple patterns can be specified by using " && " between them.
# (All of them must match for it to return true).


# http://www.iss.net/threats/ginwui.html
[Ginwui Backdoor] [any] [http://www.iss.net/threats/ginwui.html]
f:%WINDIR%\System32\zsyhide.dll;
f:%WINDIR%\System32\zsydll.dll;
r:HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\Notify\zsydll;
r:HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows -> AppInit_DLLs -> r:zsyhide.dll;


# http://www.symantec.com/security_response/writeup.jsp?docid=2006-081312-3302-99&tabid=2
[Wargbot Backdoor] [any] []
f:%WINDIR%\System32\wgareg.exe;
r:HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\wgareg;


# http://www.f-prot.com/virusinfo/descriptions/sober_j.html
[Sober Worm] [any] []
f:%WINDIR%\System32\nonzipsr.noz;
f:%WINDIR%\System32\clonzips.ssc;
f:%WINDIR%\System32\clsobern.isc;
f:%WINDIR%\System32\sb2run.dii;
f:%WINDIR%\System32\winsend32.dal;
f:%WINDIR%\System32\winroot64.dal;
f:%WINDIR%\System32\zippedsr.piz;
f:%WINDIR%\System32\winexerun.dal;
f:%WINDIR%\System32\winmprot.dal;
f:%WINDIR%\System32\dgssxy.yoi;
f:%WINDIR%\System32\cvqaikxt.apk;
f:%WINDIR%\System32\sysmms32.lla;
f:%WINDIR%\System32\Odin-Anon.Ger;


# http://www.symantec.com/security_response/writeup.jsp?docid=2005-042611-0148-99&tabid=2
[Hotword Trojan] [any] []
f:%WINDIR%\System32\_;
f:%WINDIR%\System32\explore.exe;
f:%WINDIR%\System32\ svchost.exe;
f:%WINDIR%\System32\mmsystem.dlx;
f:%WINDIR%\System32\WINDLL-ObjectsWin*.DLX;
f:%WINDIR%\System32\CFXP.DRV;
f:%WINDIR%\System32\CHJO.DRV;
f:%WINDIR%\System32\MMSYSTEM.DLX;
f:%WINDIR%\System32\OLECLI.DL;


[Beagle worm] [any] []
f:%WINDIR%\System32\winxp.exe;
f:%WINDIR%\System32\winxp.exeopen;
f:%WINDIR%\System32\winxp.exeopenopen;
f:%WINDIR%\System32\winxp.exeopenopenopen;
f:%WINDIR%\System32\winxp.exeopenopenopenopen;


# http://symantec.com/security_response/writeup.jsp?docid=2007-071711-3132-99
[Gpcoder Trojan] [any] [http://symantec.com/security_response/writeup.jsp?docid=2007-071711-3132-99]
f:%WINDIR%\System32\ntos.exe;
f:%WINDIR%\System32\wsnpoem;
f:%WINDIR%\System32\wsnpoem\audio.dll;
f:%WINDIR%\System32\wsnpoem\video.dll;
r:HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run -> userinit -> r:ntos.exe;


# [http://www.symantec.com/security_response/writeup.jsp?docid=2006-112813-0222-99&tabid=2
[Looked.BK Worm] [any] []
f:%WINDIR%\uninstall\rundl132.exe;
f:%WINDIR%\Logo1_.exe;
f:%Windir%\RichDll.dll;
r:HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run -> load -> r:rundl132.exe;


[Possible Malware - Svchost running outside system32] [all] []
p:r:svchost.exe && !%WINDIR%\System32\svchost.exe;
f:!%WINDIR%\SysWOW64;


[Possible Malware - Inetinfo running outside system32\inetsrv] [all] []
p:r:inetinfo.exe && !%WINDIR%\System32\inetsrv\inetinfo.exe;
f:!%WINDIR%\SysWOW64;


[Possible Malware - Rbot/Sdbot detected] [any] []
f:%Windir%\System32\rdriv.sys;
f:%Windir%\lsass.exe;


[Possible Malware File] [any] []
f:%WINDIR%\utorrent.exe;
f:%WINDIR%\System32\utorrent.exe;
f:%WINDIR%\System32\Files32.vxd;


# Modified /etc/hosts entries
# Idea taken from:
# http://blog.tenablesecurity.com/2006/12/detecting_compr.html
# http://www.sophos.com/security/analyses/trojbagledll.html
# http://www.f-secure.com/v-descs/fantibag_b.shtml
[Anti-virus site on the hosts file] [any] []
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:avp.ch|avp.ru|nai.com;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:awaps.net|ca.com|mcafee.com;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:microsoft.com|f-secure.com;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:sophos.com|symantec.com;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:my-etrust.com|viruslist.ru;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:networkassociates.com;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:kaspersky|grisoft.com;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:symantecliveupdate.com;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:clamav.net|bitdefender.com;
f:%WINDIR%\System32\Drivers\etc\HOSTS -> r:antivirus.com|sans.org;


# EOF #
