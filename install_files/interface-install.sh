#!/bin/bash
#
# Usage: ./install-scripts
# It reads requirements.txt for python requirements
# It reads source-requirements.txt for ubuntu dependencies on source interface
# It reads journalist-requirements.txt for ubuntu packages on doc interface
# Any environment installation/configuration scripts that need to be run
# should be put in:
# /scripts/source_interface/
# /scripts/document_interface/
# and it will be copied into the respective chroot jail and run as root
#
JAILS="source journalist"
TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"
HOST_DEPENDENCIES="secure-delete dchroot debootstrap python-dev python-pip gcc git python-software-properties"
HOST_PYTHON_DEPENDENCIES="python-bcrypt"
APP_DEPENDENCIES='secure-delete gnupg2 haveged apparmor-profiles apparmor-utils apache2-mpm-worker libapache2-mod-wsgi python-pip python-dev'
DISABLE_MODS='auth_basic authn_file autoindex cgid env setenvif status'
ENABLE_MODS='wsgi'
BCRYPT_SALT=""
SECRET_KEY=""
APP_GPG_KEY=""
APP_GPG_KEY_FINGERPRINT=""
APP_FILES=$(basename -- "$(dirname $0)" )
#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi


#Catch error
catch_error() {
  if [ !$1 = "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
}

#CD into the directory containing the interface-install.sh script
cd $(dirname $0)

#Update system and install dependencies to generate bcyrpt salt
apt-get update -y | tee -a build.log
apt-get upgrade -y | tee -a build.log

apt-get -y install $HOST_DEPENDENCIES | tee -a build.log
catch_error $? "installing host dependencies"

pip install $HOST_PYTHON_DEPENDENCIES | tee -a build.log
catch_error $? "installing host python dependencies"

#Generate bcyrpt salt and secret key that will be used in hashing codenames and signing cookies
BCRYPT_SALT=$( python gen_bcrypt_salt.py )
SECRET_KEY=$( python gen_secret_key.py )


#User Inputs the applications public gpg key and verifies fingerprint
read -p "Location of application pub gpg key? " -e -i SecureDrop.asc KEY
cp $KEY $CWD
APP_GPG_KEY=$( basename "$KEY" )
APP_GPG_KEY_FINGERPRINT=$(gpg --with-fingerprint $APP_GPG_KEY) 
echo "Verify GPG fingerpint:"
echo $APP_GPG_KEY_FINGERPRINT
read -p "Is this information correct? (Y|N): " -e -i Y ANS
if [ $ANS = N -o $ANS = n ]; then
  exit 1
fi

#Install tor repo, keyring and tor 
#save tor key to disk to be copied to chroot jails later
echo ""
echo "Installing tor on host system..."
add-apt-repository -y "$TOR_REPO" | tee -a build.log
gpg --keyserver keys.gnupg.net --recv $TOR_KEY_ID | tee -a build.log
gpg --output tor.asc --armor --export $TOR_KEY_FINGERPRINT | tee -a build.log
apt-key add tor.asc | tee -a build.log
apt-get -y update | tee -a build.log
apt-get -y install deb.torproject.org-keyring tor | tee -a build.log
echo "tor installed on host system"
catch_error $? "installing tor"


#Lock the tor user account
echo "Locking the tor user account..."
passwd -l debian-tor | tee -a build.log
catch_error $? "locking tor user account"
echo "tor user account locked"


#Create chroot jails for source and journalist interfaces
echo "Creating chroot jails for source and journalist interfaces..."
for JAIL in $JAILS; do
echo "Setting up chroot jail for $JAIL interface..."

  #Add schroot config for each interface is it doesn't exist yet
  echo "Checking for chroot jail config for $JAIL..."
  if [ ! -e /etc/schroot/chroot.d/$JAIL.conf ]; then 
    cat << EOF > /etc/schroot/chroot.d/$JAIL.conf
[$JAIL]
description=Ubuntu Precise
directory=/var/chroot/$JAIL
users=$JAIL
groups=securedrop
EOF
    echo "chroot jail config for $JAIL created"
  else
    echo "chroot config file /etc/schroot/chroot.d/$JAIL.conf already exists"
  fi

  #Use debootstrap to setup chroot jail
  create_chroot_env() {
    echo "Configuring debootstrap for $JAIL..."
    debootstrap --variant=buildd --arch amd64 precise /var/chroot/$JAIL http://us.archive.ubuntu.com/ubuntu | tee -a build.log
    catch_error $? "configuring debootstrap for $JAIL"
    echo "debootstrap for $JAIL configured"
  }

  if [ ! -d "/var/chroot/$JAIL" ]; then
    create_chroot_env
  else
    read -p "chroot jail for $JAIL already exisits overwrite? (Y|N): " -e -i Y ANS
    if [ $ANS = Y -o $ANS = y ]; then
      mkdir -p /tmp/tor/keys/  
      cp /var/chroot/$JAIL/var/lib/tor/hidden_service/{client_keys,private_key} /tmp/tor/keys 
      lsof | grep $JAIL | perl -ane 'kill 9,$F[1]'
      umount /var/chroot/$JAIL/var/www/deaddrop/store
      umount /var/chroot/$JAIL/var/www/deaddrop/keys
      umount /var/chroot/$JAIL/proc
      rm -Rf /var/chroot/$JAIL
      create_chroot_env
      cp /tmp/tor/keys/{client_keys,private_key} /var/chroot/$JAIL/var/lib/tor/hidden_service/
      srm -R /tmp/tor/keys
    fi
  fi

  echo "debootstrap for $JAIL done"

  #Create the interfaces application user in the chroot jail
  echo "Creating the $JAIL application user in the chroot jail..."
  useradd securedrop | tee -a build.log
  catch_error $? "creating the $JAIL application user in the chroot jail"
  echo "The $JAIL application user created"

  #Creating needed directory structure and files for the chroot jail
  echo "Creating the needed directories and files for the $JAIL chroot jail..."
  mkdir -p /var/chroot/$JAIL/{proc,etc,var} | tee -a build.log
  mkdir -p /var/chroot/$JAIL/etc/apt | tee -a build.log
  mkdir -p /var/chroot/$JAIL/var/www/deaddrop/{store,keys} | tee -a build.log
  mkdir -p /opt/deaddrop/{store,keys} | tee -a build.log
  chown -R securedrop:securedrop /opt/deaddrop/ | tee -a build.log
  mount -o bind /proc /var/chroot/$JAIL/proc | tee -a build.log
  mount -o bind /opt/deaddrop/store /var/chroot/$JAIL/var/www/deaddrop/store | tee -a build.log
  mount -o bind /opt/deaddrop/keys /var/chroot/$JAIL/var/www/deaddrop/keys | tee -a build.log
  cp tor.asc /var/chroot/$JAIL/root/ | tee -a build.log
  cp /etc/resolv.conf /var/chroot/$JAIL/etc/resolv.conf | tee -a build.log
  cp /etc/apt/sources.list /var/chroot/$JAIL/etc/apt/ | tee -a build.log
  cp -R $APP_FILES /var/chroot/$JAIL/var/www/ | tee -a build.log
  cp $APP_GPG_KEY /var/chroot/$JAIL/var/www/ | tee -a build.log

  #Generate the config.py file for the web interface
  cat << EOF > /var/chroot/$JAIL/var/www/deaddrop/config.py
# data directories - should be on secure media
STORE_DIR='/var/www/deaddrop/store'
GPG_KEY_DIR='/var/www/deaddrop/keys'

# fingerprint of the GPG key to encrypt submissions to
JOURNALIST_KEY='$APP_GPG_KEY_FINGERPRINT'

SOURCE_TEMPLATES_DIR='/var/www/deaddrop/source_templates'
JOURNALIST_TEMPLATES_DIR='/var/www/deaddrop/journalist_templates'
WORD_LIST='/var/www/deaddrop/wordlist'

BCRYPT_SALT='$BCRYPT_SALT' # bcrypt.gensalt()
SECRET_KEY='$SECRET_KEY' # import os; os.urandom(24)
EOF


  #schroot into the jail and configure it
  echo ""
  echo "schrooting into $JAIL and configuring it"
  schroot -c $JAIL -u root --directory /root <<FOE
echo "Updating chroot system for $JAIL..."
#create the application user in the jail
useradd $JAIL

catch_error() {
  if [ !$1 = "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
}

#chown the needed file for the application user in the chroot jail
chown $JAIL:$JAIL /var/www/$APP_GPG_KEY
chown -R $JAIL:$JAIL /var/www/deaddrop
chown -R $JAIL:$JAIL /var/www/deaddrop/{keys,store}

#add the tor signing key and install ubuntu-minimal
apt-key add /root/tor.asc
apt-get -y update
apt-get -y upgrade
apt-get -y install ubuntu-minimal $( cat $JAIL-requirements.txt )  | tee -a build.log

#Install dependencies
echo ""
echo "Installing dependencies for $JAIL..."
apt-get -y install $APP_DEPENDENCIES
catch_error $? "installing app dependencies"
echo "Dependencies installed"

#Install tor repo, keyring and tor
echo ""
echo "Installing tor for $JAIL..."
apt-key add /root/tor.asc | tee -a build.log
apt-get -y install deb.torproject.org-keyring tor
catch_error $? "installing tor"
passwd -l debian-tor
echo "Tor installed for $JAIL"

cat << EOF > /etc/tor/torrc
RunAsDaemon 1
HiddenServiceDir /var/lib/tor/hidden_service/
SafeLogging 1
SocksPort 0
EOF

echo ""
echo "Restarting tor for $JAIL..."
service tor restart
catch_error $? "restarting tor"


#Install pip dependendcies
echo 'Installing pip dependencies for $JAIL...'
pip install -r /var/www/deaddrop/requirements.txt | tee -a build.log
echo 'pip dependencies installed for $JAIL'


#Disable unneeded apache modules
echo 'Disabling apache modules for $JAIL...'
a2dismod $DISABLE_MODS | tee -a build.log
echo 'Apache modules disabled for $JAIL'


#Enabling apache modules
echo 'Enabling apache modules for $JAIL...'
a2enmod $ENABLE_MODS | tee -a build.log
echo 'Apache modules enabled for $JAIL'


#removing default apache sites
echo 'Removing default apache sites for $JAIL...'
a2dissite default default-ssl | tee -a build.log
if [ -f /var/www/index.html ]; then
  rm /var/www/index.html
fi

if [ -f /etc/apache2/sites-available/default-ssl ]; then
  rm /etc/apache2/sites-available/default-ssl
fi

if [ -f /etc/apache2/sites-available/default ]; then
  rm /etc/apache2/sites-available/default
fi
echo 'default apache sites removed for $JAIL'

#Configuring ports.conf
echo 'Configuring /etc/apache2/ports.conf for $JAIL'
cat << EOF > /etc/apache2/ports.conf
Listen 127.0.0.1:80
EOF
catch_error $? 'configuring ports.conf'
echo '/etc/apache2/ports.conf configured'

#Configuring apache2.conf
echo 'Configuring /etc/apache2/apache2.conf for $JAIL'
cat << EOF > /etc/apache2/apache2.conf
LockFile $,,{APACHE_LOCK_DIR}/accept.lock
PidFile $,,{APACHE_PID_FILE}
Timeout 300
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 5
<IfModule mpm_worker_module>
    StartServers          2
    MinSpareThreads      25
    MaxSpareThreads      75
    ThreadLimit          64
    ThreadsPerChild      25
    MaxClients          150
    MaxRequestsPerChild   0
</IfModule>
User $JAIL
Group $JAIL

AccessFileName .htaccess
<Files ~ \"^\.ht\">
    Order allow,deny
    Deny from all
    Satisfy all
</Files>
DefaultType None
HostnameLookups Off
ErrorLog /dev/null
LogLevel crit
Include mods-enabled/*.load
Include mods-enabled/*.conf
Include httpd.conf
Include ports.conf
Include conf.d/
Include sites-enabled/
EOF
#need to fix this so to create the file outside the jail then cp it in
#and change variables
sed -i 's/,,//' /etc/apache2/apache2.conf
catch_error $? 'configuring /etc/apache2/apache2.conf'

echo '/etc/apache2/apache2.conf configured for $JAIL'


#Configure /etc/apache2/security
echo 'Configuring /etc/apache2/security for $JAIL...'
cat << EOF > /etc/apache2/security
ServerTokens Prod
ServerSignature Off
TraceEnable Off
EOF
catch_error $? 'configuring /etc/apache2/security'
echo '/etc/apache2/security configured for $JAIL'
service apache2 stop
FOE
echo "FOE done for $JAIL"
done

echo "outside chroot"

#Configure the source interface specific settings
echo ""
echo "Configuring the source interface specific settings..."
schroot -c source -u root --directory /root << FOE
rm -R /var/www/deaddrop/{journalist_templates,journalist.py,example*,*.md,test*}

echo 'HiddenServicePort 80 127.0.0.1:80' >> /etc/tor/torrc
service tor restart | tee -a build.log
cat << EOF > /etc/apache2/sites-enabled/source
NameVirtualHost 127.0.0.1:80
<VirtualHost 127.0.0.1:80>
  ServerName 127.0.0.1
  DocumentRoot /var/www/deaddrop/static
  Alias /static /var/www/deaddrop/static
  WSGIDaemonProcess source  processes=2 threads=30 display-name=%{GROUP} python-path=/var/www/deaddrop
  WSGIProcessGroup source
  WSGIScriptAlias / /var/www/deaddrop/source.wsgi/
  AddType text/html .py

  <Directory />
    Options None
    AllowOverride None
    Order deny,allow
    Deny from all
  </Directory>
  <Directory /var/www/deaddrop>
    Order allow,deny
    allow from all
  </Directory>
  <Directory /var/www/deaddrop/static>
    Options None
    AllowOverride None
    Order allow,deny
    allow from all
  </Directory>
  ErrorLog /dev/null
  LogLevel crit
  ServerSignature Off
</VirtualHost>
EOF

service apache2 restart
service tor restart
echo "Done setting up $JAIL"
FOE
echo "Done setting up the source interface specific settings"

#Cofnigure the journalist interface specific settings
echo ""
echo "Configuring the journalist interface specific settings"
schroot -c journalist -u root --directory /root << FOE
echo "Starting to configure apache for $JAIL"
rm -R /var/www/deaddrop/{source_templates,source.py,example*,*.md,test*} | tee -a build.log

cat << EOF >> /etc/tor/torrc
HiddenServicePort 8080 127.0.0.1:8080
HiddenServiceAuthorizeClient stealth journalist1,journalist2
EOF

service tor restart | tee -a build.log
echo 'Listen 127.0.0.1:8080' > /etc/apache2/ports.conf


cat << EOF > /etc/apache2/sites-enabled/journalist
NameVirtualHost 127.0.0.1:8080
<VirtualHost 127.0.0.1:8080>
  ServerName 127.0.0.1
  DocumentRoot /var/www/deaddrop/static
  Alias /static /var/www/deaddrop/static
  WSGIDaemonProcess journalist  processes=2 threads=30 display-name=%{GROUP} python-path=/var/www/deaddrop
  WSGIProcessGroup journalist
  WSGIScriptAlias / /var/www/deaddrop/journalist.wsgi/
  AddType text/html .py

  <Directory />
    Options None
    AllowOverride None
    Order deny,allow
    Deny from all
  </Directory>
  <Directory /var/www/deaddrop>
    Order allow,deny
    allow from all
  </Directory>
  <Directory /var/www/deaddrop/static>
    Options None
    AllowOverride None
    Order allow,deny
    allow from all
  </Directory>
  ErrorLog /var/log/apache2/error.log
  CustomLog /var/log/apache2/access.log combined
  LogLevel info
  ServerSignature Off
</VirtualHost>
EOF
echo "Done configuring apache for $JAIL"

echo "Importing application gpg public key on $JAIL"
su -c "gpg2 --homedir /var/www/deaddrop/keys --import /var/www/$APP_GPG_KEY" $JAIL
service apache2 restart
service tor restart
FOE

cat <<EOF > /etc/rc.local
#commands to be run after reboot for securedrop
mount -o bind /proc /var/chroot/source/proc
mount -o bind /proc /var/chroot/journalist/proc
mount -o bind /opt/deaddrop/store /var/chroot/journalist/var/www/deaddrop/store
mount -o bind /opt/deaddrop/store /var/chroot/source/var/www/deaddrop/store
mount -o bind /opt/deaddrop/keys /var/chroot/source/var/www/deaddrop/keys
mount -o bind /opt/deaddrop/keys /var/chroot/journalist/var/www/deaddrop/keys
schroot -u root -a service apache2 restart --directory /root
schroot -u root -a service tor restart --directory /root
EOF

#Wait 10 seconds for tor keys to be configured and print tor onion urls
sleep 10
echo "Source onion url is: "
echo `cat /var/chroot/source/var/lib/tor/hidden_service/hostname`

echo "Journalist onion url and auth values are you will need to append ':8080' to the end of the journalist onion url"
echo `cat /var/chroot/journalist/var/lib/tor/hidden_service/hostname`

exit 0
