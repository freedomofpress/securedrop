#!/bin/bash

#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

apt-get update -y
apt-get upgrade -y
apt-get -y install dchroot debootstrap python-dev python-pip gcc -y
pip install python-bcrypt

JAILS="source"
BCRYPT_SALT=`python gen_bcrypt_salt.py`
SECRET_KEY=`python gen_secret_key.py`
TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"
DEPENDENCIES='secure-delete gnupg2 haveged libpam-google-authenticator apparmor-profiles apparmor-utils python-software-properties apache2-mpm-worker libapache2-mod-wsgi python-pip python-dev'
DISABLE_MODS='auth_basic authn_file autoindex cgid env setenvif status'
ENABLE_MODS='wsgi'

read -p "Location of application pub gpg key? " -e -i SecureDrop.asc APP_GPG_KEY
read -p "What is the application's pub gpg key fingerprint? " -e -i fingerprint APP_GPG_KEY_FINGERPRINT


for JAIL in $JAILS; do
echo "FOE for $JAIL"

  cat << EOF > /etc/schroot/chroot.d/$JAIL.conf
[$JAIL]
description=Ubuntu Precise
directory=/var/chroot/$JAIL
users=source
groups=source
EOF

#  debootstrap --variant=buildd --arch amd64 precise /var/chroot/$JAIL http://us.archive.ubuntu.com/ubuntu
  mkdir -p /var/chroot/$JAIL/{proc,etc}
  mkdir -p /var/chroot/$JAIL/etc/apt
  mkdir -p /opt/deaddrop/{store,keys}
  mkdir -p /var/chroot/$JAIL/var/www/deaddrop
  mount -o bind /proc /var/chroot/$JAIL/proc
  mount -o bind /opt/deaddrop/store /var/chroot/$JAIL/deaddrop/store
  mount -o bind /opt/deaddrop/keys /var/chroot/$JAIL/deaddrop/keys
  cp /etc/resolv.conf /var/chroot/$JAIL/etc/resolv.conf
  cp /etc/apt/sources.list /var/chroot/$JAIL/etc/apt/
  cp /home/ubuntu/requirements.txt /var/chroot/$JAIL/root/
  cp $APP_GPG_KEY /var/chroot/$JAIL/root/

  schroot -c $JAIL -u root<<FOE
useradd $JAIL
echo "Updating chroot system..."

catch_error() {
  if [ !$1 = "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
}

apt-get -y update
apt-get -y upgrade
apt-get -y install ubuntu-minimal

#Install dependencies
echo ""
echo $DEPENDENCIES
echo "Installing dependencies..."

echo ""
echo ""
apt-get -y install python-software-properties
echo ""
echo ""

apt-get -y install $DEPENDENCIES
catch_error $? "installing dependencies"
echo "Dependencies installed"

#Install tor repo, keyring and tor
echo ""
echo "Installing tor..."
add-apt-repository -y "$TOR_REPO"
gpg --keyserver keys.gnupg.net --recv $TOR_KEY_ID
gpg --output tor.asc --armor --export $TOR_KEY_FINGERPRINT
apt-key add tor.asc
apt-get -y update
apt-get -y install deb.torproject.org-keyring tor
catch_error $? "installing tor"
passwd -l debian-tor
echo "Tor installed"

cat << EOF > /etc/tor/torrc
RunAsDaemon 1
HiddenServiceDir /var/lib/tor/hidden_service/
SafeLogging 1
SocksPort 0
EOF

echo ""
echo "Restarting tor..."
service tor restart
catch_error $? "restarting tor"


#Install pip dependendcies
echo 'Installing pip dependencies...'
pip install -r requirements.txt | tee -a build.log
echo 'pip dependencies installed'


#Disable unneeded apache modules
echo 'Disabling apache modules...'
a2dismod $DISABLE_MODS | tee -a build.log
echo 'Apache modules disabled'


#Enabling apache modules
echo 'Enabling apache modules...'
a2enmod $ENABLE_MODS | tee -a build.log
echo 'Apache modules enabled'


#removing default apache sites
echo 'Removing default apache sites...'
if [ -f /var/www/index.html ]; then
  rm /var/www/index.html
fi

if [ -f /etc/apache2/sites-available/default-ssl ]; then
  rm /etc/apache2/sites-available/default-ssl
fi

if [ -f /etc/apache2/sites-available/default ]; then
  rm /etc/apache2/sites-available/default
fi

a2dissite default default-ssl | tee -a build.log
echo 'default apache sites removed'

#Configuring ports.conf
echo 'Configuring /etc/apache2/ports.conf'
cat << EOF > /etc/apache2/ports.conf
Listen 127.0.0.1:80
EOF
catch_error $? 'configuring ports.conf'
echo '/etc/apache2/ports.conf configured'

#Configuring apache2.conf
echo 'Configuring /etc/apache2/apache2.conf'
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
sed -i 's/,,//' /etc/apache2/apache2.conf
catch_error $? 'configuring /etc/apache2/apache2.conf'

echo '/etc/apache2/apache2.conf configured'
#Configure /etc/apache2/security
echo 'Configuring /etc/apache2/security...'
cat << EOF > /etc/apache2/security
ServerTokens Prod
ServerSignature Off
TraceEnable Off
EOF
catch_error $? 'configuring /etc/apache2/security'
echo '/etc/apache2/security configured'

cat << EOF > /var/www/deaddrop/config.py
# data directories - should be on secure media
STORE_DIR='/var/www/deaddrop/store'
GPG_KEY_DIR='/var/www/deaddrop/keys'

# fingerprint of the GPG key to encrypt submissions to
JOURNALIST_KEY='$APP_GPG_KEY_FINGERPRINT'

SOURCE_TEMPLATES_DIR='/var/www/deaddrop/source_templates'
JOURNALIST_TEMPLATES_DIR='/var/www/deaddrop/journalist_templates'
WORD_LIST='./wordlist'

BCRYPT_SALT='$BCRYPT_SALT' # bcrypt.gensalt()
SECRET_KEY='$SECRET_KEY' # import os; os.urandom(24)

echo "inside chroot"
FOE
echo "FOE done"
done

echo "outside chroot"

schroot -c source -u root << FOE
rm -R /var/www/deaddrop/{journalist_templates,example*,*.md,test*}

echo 'HiddenServicePort 80 127.0.0.1:80' >> /etc/tor/torrc

FOE

for JOURNALIST_INTERFACE in $JOURNALIST_INTERFACES; do
schroot -c $JOURNALIST_INTERFACE -u root << FOE

rm -R /var/www/deaddrop/{source_templates,example*,*.md,test*}

cat << EOF >> /etc/tor/torrc
HiddenServicePort 8080 127.0.0.1:8080
HiddenServiceAuthorizeClient stealth journalist1,journalist2
EOF

echo 'Listen 127.0.0.1:8080' > /etc/apache2/ports.conf
cat << EOF > /etc/apache2/sites-enabled/journalist
NameVirtualHost 127.0.0.1:8080
<VirtualHost 127.0.0.1:8080>
  ServerName 127.0.0.1
  DocumentRoot /var/www/deaddrop/static
  Alias /static /var/www/deaddrop/static
  WSGIDaemonProcess journalist  processes=2 threads=30 display-name=%{GROUP} python-path=/var/www/deaddrop
  WSGIProcessGroup journalist
  WSGIScriptAlias / /var/www/deaddrop/journalist.py/
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

FOE
done
exit 0
