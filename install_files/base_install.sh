#!/bin/bash
#
# Usage: ./base_install.sh
# --no-updates to run script without apt-get or pip install commands
#securedrop.git                                       (repo base)
#securedrop/securedrop/                               (web app code)
#securedrop/securedrop/requirements.txt               (pip requirements)
#securedrop/install_files/                            (config files and install scripts)
#securedrop/install_files/SecureDrop.asc              (the app pub gpg key)
#securedrop/install_files/source_requirements.txt     (source chroot jail package dependencies)
#securedrop/install_files/journalist_requirements.txt (journalist interface chroot package dependencies)
BASE_DEPENDENCIES="secure-delete gnupg2 haveged syslog-ng ntp libpam-google-authenticator rng-tools unattended-upgrades inotify-tools sysstat iptables apparmor-profiles apparmor-utils python-software-properties"
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
if [ ! "$1" = "--no-updates" ]; then
  echo "Updating system..."
  apt-get update -y && apt-get upgrade -y | tee -a build.log
  catch_error $? "updating system"
  echo "System updated"
fi

#Install dependencies
echo ""
echo "Installing dependencies..."
apt-get install -y $BASE_DEPENDENCIES | tee -a build.log
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
cp sysctl.conf /etc/sysctl.conf
catch_error $? "copying sysctl.conf"
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
cp base.torrc /etc/tor/torrc
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
echo "Create a google authenticator value for admin users requiring ssh access"
echo "These will be the only users able to ssh into the system."
echo -n "Enter first username: "
read SSH_USER

groupadd ssh

if id -u "$SSH_USER" >/dev/null 2>&1; then
  if [ ! $(groups $SSH_USER | awk -F ": " "{print $2}" | grep -q "ssh") ]; then
    echo "Adding $SSH_USER to ssh group"
    usermod -a -G ssh $SSH_USER
    catch_error $? "adding $SSH_USER to the ssh group"
  fi

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
sed -i -e "s/OTHER_IP/$OTHER_IP/g" base.rules_v4
catch_error $? "replacing $OTHER_IP in base.rules_v4"
cp base.rules_v4 /etc/iptables/rules_v4
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
cp base.ssh_config /etc/ssh/ssh_config
catch_error $? "configuring ssh_config"
echo "ssh_config configured"


#sshd_config tweeks
echo ""
echo "Configuring sshd_config..."
cp base.sshd_config /etc/ssh/sshd_config
catch_error $? "configuring sshd_config"
echo "sshd_config configured"


#Configure /etc/pam.d/common-auth
echo ""
echo "Configuring /etc/pam.d/common-auth..."
cp base.common-auth /etc/pam.d/common-auth
catch_error $? "configuring /etc/pam.d/common-auth"
echo "/etc/pam.d/common-auth configured"


echo ""
echo "The tor hidden service for ssh is: "
cat /var/lib/tor/hidden_service/hostname

exit 0
