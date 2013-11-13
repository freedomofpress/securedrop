#!/bin/bash
#
#
DEPENDENCIES='secure-delete gnupg2 haveged syslog-ng ntp libpam-google-authenticator rng-tools unattended-upgrades inotify-tools sysstat iptables apparmor-profiles apparmor-utils python-software-properties' 

TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"


#Error handling function
catch_error() {
  if [ $1 -ne "0" ]; then
  echo "ERROR encountered $2"
  exit 1
fi
}


#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi


#Check release
if [ -f /etc/redhat-release ]; then
  DISTRO="fedora"
# Debian/Ubuntu
elif [ -r /lib/lsb/init-functions ]; then
  if [ "$( lsb_release -is )" == "Debian" ]; then
    DISTRO="debian"
    DISTRO_VERSION="$( lsb_release -c )"
  else
    DISTRO="ubuntu"
    DISTRO_VERSION="$( lsb_release -c | cut -f 2 )"
  fi
fi


echo "Performing installation on $DISTRO - $DISTRO_VERSION"

if [ $DISTRO != 'ubuntu' ]; then
  echo ""
  echo "You are installing SecurerDrop on an unsupported system."
  echo "Do you wish to continue at your own risk [Y|N]? "
  read ANS
  if [ $ANS = y -o $ANS = Y ]
  then
    echo "Use at your own risk"
  else
    echo "Use ubuntu precise x64"
    exit 1
  fi
fi


#Update and upgrade system
echo ""
echo "Updating system..."
apt-get update -y | tee build.log && apt-get upgrade -y | tee -a build.log
catch_error $? "updating system"
echo "System updated"


#Install dependencies
echo ""
echo "Installing dependencies..."
apt-get install $DEPENDENCIES -y | tee -a build.log
catch_error $? "installing dependencies"
echo "Dependencies installed"


#Disable swap
echo ""
echo "Disabling swap..."
swapoff -a
catch_error $? "disabling swap"
echo "Swap disabled"


#Enable sysstat collection
echo ""
echo "Enabling sysstat..."
if [ -f /etc/default/sysstat ]; then
  sed -i "s/ENABLED=\"false\"/ENABLED=\"true\"/" /etc/default/sysstat
  catch_error $? "enabling sysstat"
fi
echo "Sysstat enabled"


#Enable unattended-upgrades
echo ""
echo "Enabling unattended-upgrades..."
cat << EOF > /etc/apt/apt.conf.d/20auto-upgrades
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
catch_error $? "creating /etc/apt/apt.conf.d/20auto-upgrades"

sed -i "s/\/\/Unattended-Upgrade::Remove-Unused-Dependencies \"false\"/Unattended-Upgrade::Remove-Unused-Dependencies \"true\"/" /etc/apt/apt.conf.d/50unattended-upgrades

sed -i "s/\/\/Unattended-Upgrade::Automatic-Reboot \"false\"/Unattended-Upgrade::Automatic-Reboot \"true\"/" /etc/apt/apt.conf.d/50unattended-upgrades

catch_error $? "enabling unattended-upgrades"
echo "Unattended-upgrades enabled"


#Restrict who can run cron jobs
echo ""
echo "Resticitng users who can run cron jobs to the root user..."
cat << EOF > /etc/cron.allow
root
EOF
if [ -f /etc/cron.deny ]; then
  rm /etc/cron.deny
  catch_error $? "restricting users who can run cron jobs to the root user"
fi
echo "Only the root user can run cron jobs"


#sysctl.conf tweeks
echo ""
echo "Configuring sysctl.conf..."
cat << EOF > /etc/sysctl.conf
# Following 11 lines added by CISecurity Benchmark sec 5.1
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_syncookies=1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.icmp_echo_ignore_broadcasts = 1
#
# Following 3 lines added by CISecurity Benchmark sec 5.2
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
#
# Following 3 lines were added to disable IPv6 per CIS Debian
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
#
# Grsecurity Kernel related configs
#kernel.grsecurity.grsec.lock = 1
EOF
sysctl -p /etc/sysctl.conf | tee -a build.log
catch_error $? "configuring sysctl.conf"
echo "Sysctl.conf configured"


#Install tor repo, keyring and tor
echo ""
echo "Installing tor..."
add-apt-repository -y "$TOR_REPO" | tee -a build.log
gpg --keyserver keys.gnupg.net --recv $TOR_KEY_ID | tee -a build.log
gpg --export $TOR_KEY_FINGERPRINT | sudo apt-key add - | tee -a build.log
apt-get update -y | tee -a build.log
apt-get install deb.torproject.org-keyring tor -y | tee -a build.log
catch_error $? "installing tor"
passwd -l debian-tor | tee -a build.log
echo "Tor installed"


#Configure authenticated tor hidden service for ssh access
echo ""
echo "Configuing authenticated to hidden service for ssh access..."
cat << EOF > /etc/tor/torrc
SafeLogging 1
RunAsDaemon 1
HiddenServiceDir /var/lib/tor/hidden_service/
HiddenServicePort 22 127.0.0.1:22
HiddenServiceAuthorizeClient stealth admin1,admin2
EOF
catch_error $? "configuring authenticated tor hidden service for ssh access"
echo "Authenticated tor hidden service for ssh access created"

echo ""
echo "Restarting tor..."
service tor restart | tee -a build.log
catch_error $? "restating tor"
sleep 10
echo "Tor restarted, the hidden servive url is: "
cat /var/lib/tor/hidden_service/hostname


#Generate google 2 step auth
generate_2_step_code() {
echo -n "Enter the username to create a google authenticator value for: "
read SSH_USER

if id -u "$SSH_USER" >/dev/null 2>&1; then
  echo "Creating google authenticator code for $SSH_USER in their home directory"
  su $SSH_USER -c google-authenticator
  catch_error $? "generating google-authenticator code for $SSH_USER"
  echo ""
  echo -n "Do you want to create another google authenticator code for another user? (Y|N): "
  read ANS
  if [ $ANS = y -o $ANS = Y ]; then
    generate_2_step_code
  fi
else
  echo "$SSH_USER user does not exist."
  echo -n "Do you want to enter another username? (Y|N): "
  read ANS
  if [ $ANS = y -o $ANS = Y ]; then
    generate_2_step_code
  fi
fi
catch_error $? "generating google authenticator code"
}

echo ""
echo -n "Do you want to generate a google authenticator code now? (Y|N): "
read ANS
if [ $ANS = y -o $ANS = Y ]; then
  generate_2_step_code
fi


#Configure Iptables
echo ""
echo "Configuring iptables..."
echo -n "What is the ip address of the other server (source/monitor)? "
read OTHER_IP
if [ ! -d /etc/iptables ]; then
  mkdir /etc/iptables
  catch_error $? "creating /etc/iptables directory"
fi
cat << EOF > /etc/iptables/rules_v4
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:LOGNDROP - [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A INPUT -s 127.0.0.1/32 -d 127.0.0.1/32 -p tcp -m tcp -j ACCEPT
-A INPUT -s $OTHER_IP -p udp --dport 1514 -j ACCEPT
-A INPUT -j LOGNDROP
-A LOGNDROP -p tcp -m limit --limit 5/min -j LOG --log-prefix "Denied_TCP " --log-level 4
-A LOGNDROP -p udp -m limit --limit 5/min -j LOG --log-prefix "Denied_UDP " --log-level 4
-A LOGNDROP -p icmp -m limit --limit 5/min -j LOG --log-prefix "Denied_ICMP " --log-level 4 
-A LOGNDROP -j DROP
COMMIT
EOF
catch_error $? "creating iptables rules file /etc/iptables/rules_v4"
echo "The /etc/iptables/rules_v4 file created"

cat << EOF > /etc/network/if-up.d/load_iptables
#!/bin/sh
iptables-restore < /etc/iptables/rules_v4
exit 0
EOF
catch_error $? "creating iptables load script"
chmod +x /etc/network/if-up.d/load_iptables
echo "The /etc/network/if-up.d/load_iptables script created"

cat << EOF > /etc/network/if-down.d/save_iptables
#!/bin/sh
iptables-save -c > /etc/iptables/rules_v4
if [ -f /etc/iptables/down_rules ]; then
   iptables-restore < /etc/iptables/down_rules
fi
exit 0
EOF
catch_error $? "creating iptables save script"
chmod +x /etc/network/if-down.d/save_iptables
echo "The /etc/iptables/save_iptables script is created"

echo ""
echo "Applying iptables rules from /etc/iptables/rules_v4"
iptables-restore < /etc/iptables/rules_v4
catch_error $? "applying iptable rules from /etc/iptables/rules_v4"
echo "iptables rules applied"


#Configure tcp wrappers
echo ""
echo "Configuring tcp wrappers for sshd"
cat << EOF > /etc/hosts.allow
sshd: 127.0.0.1
EOF
catch_error $? "configuring tcp wrappers for sshd /etc/hosts.allow"

cat << EOF > /etc/hosts.deny
ALL: ALL
EOF
catch_error $? "configuring tcp wrappers for sshd /etc/hosts.deny"


#ssh_config tweeks
echo ""
echo "Configuring ssh_config..."
cat << EOF > /etc/ssh/ssh_config
Host *
Port 22
Protocol 2
    SendEnv LANG LC_*
    HashKnownHosts yes
    GSSAPIAuthentication yes
    GSSAPIDelegateCredentials no
EOF
catch_error $? "configuring ssh_config"
echo "ssh_config configured"


#sshd_config tweeks
echo ""
echo "Configuring sshd_config..."
cat << EOF > /etc/ssh/sshd_config
# Package generated configuration file
# See the sshd_config(5) manpage for details

# What ports, IPs and protocols we listen for
Port 22
# Use these options to restrict which interfaces/protocols sshd will bind to
#ListenAddress ::
ListenAddress 127.0.0.1
Protocol 2
# HostKeys for protocol version 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_dsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
#Privilege Separation is turned on for security
UsePrivilegeSeparation yes

# Lifetime and size of ephemeral version 1 server key
KeyRegenerationInterval 3600
ServerKeyBits 768

# Logging
SyslogFacility AUTH
LogLevel INFO

# Authentication:
LoginGraceTime 120
PermitRootLogin no
StrictModes yes

RSAAuthentication yes
PubkeyAuthentication yes
#AuthorizedKeysFile        %h/.ssh/authorized_keys

# Don't read the user's ~/.rhosts and ~/.shosts files
IgnoreRhosts yes
# For this to work you will also need host keys in /etc/ssh_known_hosts
RhostsRSAAuthentication no
# similar for protocol version 2
HostbasedAuthentication no
# Uncomment if you don't trust ~/.ssh/known_hosts for RhostsRSAAuthentication
#IgnoreUserKnownHosts yes

# To enable empty passwords, change to yes (NOT RECOMMENDED)
PermitEmptyPasswords no

# Change to yes to enable challenge-response passwords (beware issues with
# some PAM modules and threads)
ChallengeResponseAuthentication yes

# Change to no to disable tunnelled clear text passwords
#PasswordAuthentication yes

# Kerberos options
#KerberosAuthentication no
#KerberosGetAFSToken no
#KerberosOrLocalPasswd yes
#KerberosTicketCleanup yes

# GSSAPI options
#GSSAPIAuthentication no
#GSSAPICleanupCredentials yes

X11Forwarding yes
X11DisplayOffset 10
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes
#UseLogin no

#MaxStartups 10:30:60
#Banner /etc/issue.net

# Allow client to pass locale environment variables
AcceptEnv LANG LC_*

Subsystem sftp /usr/lib/openssh/sftp-server

# Set this to 'yes' to enable PAM authentication, account processing,
# and session processing. If this is enabled, PAM authentication will
# be allowed through the ChallengeResponseAuthentication and
# PasswordAuthentication.  Depending on your PAM configuration,
# PAM authentication via ChallengeResponseAuthentication may bypass
# the setting of "PermitRootLogin without-password".
# If you just want the PAM account and session checks to run without
# PAM authentication, then enable this but set PasswordAuthentication
# and ChallengeResponseAuthentication to 'no'.
UsePAM yes
EOF
catch_error $? "configuring sshd_config"
echo "sshd_config configured"


#Configure /etc/pam.d/common-auth
echo ""
echo "Configuring /etc/pam.d/common-auth..."
cat << EOF > /etc/pam.d/common-auth

s file is included from other service-specific PAM config files,
# and should contain a list of the authentication modules that define
# the central authentication scheme for use on the system
# (e.g., /etc/shadow, LDAP, Kerberos, etc.).  The default is to use the
# traditional Unix authentication mechanisms.
#
# As of pam 1.0.1-6, this file is managed by pam-auth-update by default.
# To take advantage of this, it is recommended that you configure any
# local modules either before or after the default block, and use
# pam-auth-update to manage selection of other modules.  See
# pam-auth-update(8) for details.

# here are the per-package modules (the "Primary" block)
auth required pam_google_authenticator.so
auth    [success=1 default=ignore]      pam_unix.so nullok_secure
# here's the fallback if no module succeeds
auth    requisite                       pam_deny.so
# prime the stack with a positive return value if there isn't one already;
# this avoids us returning an error just because nothing sets a success code
# since the modules above will each just jump around
auth    required                        pam_permit.so
# and here are more per-package modules (the "Additional" block)
auth    optional        pam_ecryptfs.so unwrap
# end of pam-auth-update config

exit 0
EOF
catch_error $? "configuring /etc/pam.d/common-auth"
echo "/etc/pam.d/common-auth configured"


echo ""
echo "The tor hidden service for ssh is: "
cat /var/lib/tor/hidden_service/hostname

exit 0
