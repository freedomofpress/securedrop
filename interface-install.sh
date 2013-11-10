#!/bin/bash

#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

#apt-get update -y
#apt-get upgrade -y
#apt-get -y install dchroot debootstrap python-dev python-pip gcc git -y
#pip install python-bcrypt

JAILS="source journalist"
BCRYPT_SALT=`python gen_bcrypt_salt.py`
SECRET_KEY=`python gen_secret_key.py`
TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"
DEPENDENCIES='secure-delete gnupg2 haveged libpam-google-authenticator apparmor-profiles apparmor-utils python-software-properties apache2-mpm-worker libapache2-mod-wsgi python-pip python-dev'
DISABLE_MODS='auth_basic authn_file autoindex cgid env setenvif status'
ENABLE_MODS='wsgi'

read -p "Location of application pub gpg key? " -e -i SecureDrop.asc APP_GPG_KEY
read -p "What is the application's pub gpg key fingerprint? " APP_GPG_KEY_FINGERPRINT
git clone git://github.com/webpy/webpy.git /tmp/webpy

for JAIL in $JAILS; do
echo "FOE for $JAIL"

  cat << EOF > /etc/schroot/chroot.d/$JAIL.conf
[$JAIL]
description=Ubuntu Precise
directory=/var/chroot/$JAIL
users=$JAIL
groups=securedrop
EOF

#  debootstrap --variant=buildd --arch amd64 precise /var/chroot/$JAIL http://us.archive.ubuntu.com/ubuntu
  useradd securedrop
  mkdir -p /var/chroot/$JAIL/{proc,etc,var}
  mkdir -p /var/chroot/$JAIL/etc/apt
  mkdir -p /var/chroot/$JAIL/var/www/deaddrop/{store,keys}
  mkdir -p /opt/deaddrop/{store,keys}
  chown -R securedrop:securedrop /opt/deaddrop/
  mount -o bind /proc /var/chroot/$JAIL/proc
  mount -o bind /opt/deaddrop/store /var/chroot/$JAIL/var/www/deaddrop/store
  mount -o bind /opt/deaddrop/keys /var/chroot/$JAIL/var/www/deaddrop/keys
  cp /etc/resolv.conf /var/chroot/$JAIL/etc/resolv.conf
  cp /etc/apt/sources.list /var/chroot/$JAIL/etc/apt/
  cp -R deaddrop /var/chroot/$JAIL/var/www/
  cp -R /tmp/webpy /var/chroot/$JAIL/var/www/deaddrop/
  ln -s /var/chroot/$JAIL/var/www/deaddrop/webpy/web /var/chroot/$JAIL/var/www/deaddrop/web
  cp $APP_GPG_KEY /var/chroot/$JAIL/var/www/
  schroot -c $JAIL -u root<<FOE
useradd $JAIL
groupadd $JAIL
echo "Updating chroot system for $JAIL..."

catch_error() {
  if [ !$1 = "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
}
  chown $JAIL:$JAIL /var/www/$APP_GPG_KEY
  chown -R $JAIL:$JAIL /var/www/deaddrop
  chown -R $JAIL:$JAIL /var/www/deaddrop/{keys,store}

#apt-get -y update
#apt-get -y upgrade
#apt-get -y install ubuntu-minimal

#Install dependencies
echo ""
echo "Installing dependencies for $JAIL..."

echo ""
echo ""
#apt-get -y install python-software-properties
echo ""
echo ""

#apt-get -y install $DEPENDENCIES
catch_error $? "installing dependencies"
echo "Dependencies installed"

#Install tor repo, keyring and tor
echo ""
echo "Installing tor for $JAIL..."
#add-apt-repository -y "$TOR_REPO"
#gpg --keyserver keys.gnupg.net --recv $TOR_KEY_ID
#gpg --output tor.asc --armor --export $TOR_KEY_FINGERPRINT
#apt-key add tor.asc
#apt-get -y update
#apt-get -y install deb.torproject.org-keyring tor
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
#pip install -r requirements.txt | tee -a build.log
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

cat << EOF > /var/www/deaddrop/config.py
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

echo "inside chroot for $JAIL"
FOE
echo "FOE done for $JAIL"
done

echo "outside chroot"

schroot -c source -u root << FOE
rm -R /var/www/deaddrop/{journalist_templates,example*,*.md,test*}

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
  WSGIScriptAlias / /var/www/deaddrop/source.py/
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

echo "Done setting up $JAIL"
FOE

schroot -c journalist -u root << FOE
echo "Starting to configure apache for $JAIL"
rm -R /var/www/deaddrop/{source_templates,example*,*.md,test*} | tee -a build.log

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
echo "Done configuring apache for $JAIL"

echo "Importing application gpg public key on $JAIL"
su -c "gpg2 --homedir /var/www/deaddrop/keys --import /var/www/$APP_GPG_KEY" $JAIL
FOE

sleep 10
echo "Source onion url is: "
echo `cat /var/chroot/source/var/lib/tor/hidden_service/hostname`

echo "Journalist onion url and auth values are: "
echo `cat /var/chroot/journalist/var/lib/tor/hidden_service/hostname`

exit 0
