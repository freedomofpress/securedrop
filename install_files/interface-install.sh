#!/bin/bash
#
# Usage: ./install-scripts
# Reads requirements.txt for python requirements
# Reads source-requirements.txt for ubuntu dependencies on source interface
# Reads journalist-requirements.txt for ubuntu packages on doc interface
# --no-updates to run script without apt-get or pip install commands
# --force-clean to delete chroot jails. backup tor private keys prior
#
#
JAILS="source journalist"
TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"
HOST_DEPENDENCIES="haveged secure-delete dchroot debootstrap python-dev python-pip gcc git python-software-properties"
HOST_PYTHON_DEPENDENCIES="python-bcrypt"
DISABLE_MODS='auth_basic authn_file autoindex cgid env setenvif status'
ENABLE_MODS='wsgi'
BCRYPT_SALT=""
SECRET_KEY=""
APP_GPG_KEY=""
APP_GPG_KEY_FINGERPRINT=""
CWD="$(dirname $0)"
PARENT_DIR="$(dirname "$CWD")"
APP_FILES="$PARENT_DIR/securedrop"

#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

#Catch error
catch_error() {
  if [ !"$1" = "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
}


#CD into the directory containing the interface-install.sh script
cd $CWD


#User Inputs the applications public gpg key and verifies fingerprint
read -p "Location of application pub gpg key? " -e -i SecureDrop.asc KEY
APP_GPG_KEY=$( basename "$KEY" )

if [ -f APP_GPG_KEY ]; then
 cp $KEY $CWD
 catch_error $? "moving $APP_GPG_KEY to current directory"
fi

APP_GPG_KEY_FINGERPRINT=$( gpg --with-colons --with-fingerprint $APP_GPG_KEY | awk -F: '$1=="fpr" {print $10;}' )
echo "Verify GPG fingerpint:"
echo $APP_GPG_KEY_FINGERPRINT
read -p "Is this information correct? (Y|N): " -e -i Y ANS
if [ $ANS = N -o $ANS = n ]; then
  exit 1
fi


#Update system and install dependencies to generate bcyrpt salt
if [ ! "$1" = "--no-updates" ]; then
  apt-get update -y | tee -a build.log
  apt-get upgrade -y | tee -a build.log

  apt-get -y install $HOST_DEPENDENCIES | tee -a build.log
  catch_error $? "installing host dependencies"

  pip install $HOST_PYTHON_DEPENDENCIES | tee -a build.log
  catch_error $? "installing host python dependencies"
fi

#Generate bcyrpt salt and secret key that will be used in hashing codenames and signing cookies
BCRYPT_SALT=$( python gen_bcrypt_salt.py )
SECRET_KEY=$( python gen_secret_key.py )


#Install tor repo, keyring and tor 
#save tor key to disk to be copied to chroot jails later
echo ""
echo "Installing tor on host system..."
add-apt-repository -y "$TOR_REPO" | tee -a build.log

if [ -f tor.asc ]; then
  rm tor.asc
fi

gpg --keyserver keys.gnupg.net --recv $TOR_KEY_ID | tee -a build.log
catch_error $?
gpg --output tor.asc --armor --export $TOR_KEY_FINGERPRINT | tee -a build.log

if [ ! "$1" = "--no-updates" ]; then
  apt-key add tor.asc | tee -a build.log
  apt-get -y update | tee -a build.log
  apt-get -y install deb.torproject.org-keyring tor | tee -a build.log
  catch_error $? "installing tor"
  echo "tor installed on host system"
fi


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
groups=$JAIL
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

  #Clean previous chroot jails
  clean_chroot_jail() {
    if [ -f "/var/chroot/$JAIL/var/lib/tor/hidden_service/client_keys" ]; then
      mkdir -p /tmp/tor-keys/$JAIL  
      cp -f /var/chroot/$JAIL/var/lib/tor/hidden_service/client_keys /tmp/tor-keys/$JAIL
    elif [ -f "/var/chroot/$JAIL/var/lib/tor/hidden_service/private_key" ]; then
      mkdir -p /tmp/tor-keys/$JAIL
      cp -f /var/chroot/$JAIL/var/lib/tor/hidden_service/private_key /tmp/tor-keys/$JAIL
    fi 
    
    echo "Stoping apache service in chroot jail $JAIL..."
    if schroot -c $JAIL -u root "pgrep apache2"; then
      schroot -c $JAIL -u root service apache2 stop --directory /
      echo "apache service stopped for chroot jail $JAIL"
    fi

    if schroot -c $JAIL -u root "pgrep tor"; then
      echo "Stopping tor service in chroot jail $JAIL..."
      schroot -c $JAIL -u root service tor stop --directory /
      echo "tor service stopped for chroot jail $JAIL"
    fi

    lsof | grep $JAIL | perl -ane 'kill 9,$F[1]'
    MOUNTED_DIRS="/var/chroot/$JAIL/var/www/securedrop/store /var/chroot/$JAIL/var/www/securedrop/keys /var/chroot/$JAIL/proc"
    for MOUNTED_DIR in $MOUNTED_DIRS; do
      if [ -d $MOUNTED_DIR ]; then
        echo "un mounting $MOUNTED_DIR"
        umount $MOUNTED_DIR
        catch_error $? "umounting $MOUNTED_DIR"
        echo "$MOUNTED_DIR un mounted"
      fi
    done
      
    if [ -d /var/chroot/$JAIL ]; then
      echo "secure-deleting /var/chroot/$JAIL..."
      rm -Rf /var/chroot/$JAIL
      catch_error $? "secure-deleting /var/chroot/$JAIL"
      echo "/var/chroot/$JAIL secure-deleted"
    fi

    create_chroot_env

    if [ -d "/tmp/tor/keys/$JAIL" ]; then
      echo "copying tor keys to /var/chroot/$JAIL/root/tor-keys/$JAIL/..."
      cp -p -f /tmp/tor-keys/$JAIL/{client_keys,private_key} /var/chroot/$JAIL/root/tor-keys/$JAIL
      echo "backed up'd tor keys are copied to /var/chroot/$JAIL/root/tor-keys/$JAIL/" 
      echo "secure-deleting /tmp/tor/keys/$JAIL..."
      srm -R /tmp/tor-keys/$JAIL
      catch_error $? "removing tmp keys"
      echo "/tmp/tor/keys/$JAIL/ secure-deleted"
    fi
  }

  if [ ! -d "/var/chroot/$JAIL" ]; then
    create_chroot_env
    echo "debootstrap for $JAIL done"
  fi

  if [ "$1" = "--force-clean" ]; then
    clean_chroot_jail
  fi

  #Create the interfaces application user in the chroot jail
  echo "Creating the $JAIL application user in the chroot jail..."
  useradd securedrop | tee -a build.log
  catch_error $? "creating the $JAIL application user in the chroot jail"
  echo "The $JAIL application user created"

  #Creating needed directory structure and files for the chroot jail
  echo "Creating the needed directories and files for the $JAIL chroot jail..."
  mkdir -p /var/chroot/$JAIL/{proc,etc,var} | tee -a build.log
  mkdir -p /var/chroot/$JAIL/etc/{apt,tor} | tee -a build.log
  mkdir -p /var/chroot/$JAIL/var/www/securedrop/{store,keys} | tee -a build.log
  mkdir -p /var/securedrop/{store,keys} | tee -a build.log
  mkdir -p /var/chroot/$JAIL/etc/apache2/sites-enabled/ | tee -a build.log
  chown -R securedrop:securedrop /var/securedrop/ | tee -a build.log
  mount -o bind /proc /var/chroot/$JAIL/proc | tee -a build.log
  mount -o bind /var/securedrop/store /var/chroot/$JAIL/var/www/securedrop/store | tee -a build.log
  mount -o bind /var/securedrop/keys /var/chroot/$JAIL/var/www/securedrop/keys | tee -a build.log

  cp -f /etc/apt/sources.list /var/chroot/$JAIL/etc/apt/ | tee -a build.log
  catch_error $? "copying source.list to chroot jail $JAIL"
  cp -f tor.asc /var/chroot/$JAIL/root/ | tee -a build.log
  catch_error $? "copying tor.asc to chroot jail $JAIL"
  cp -f /etc/resolv.conf /var/chroot/$JAIL/etc/resolv.conf | tee -a build.log
  catch_error $? "copying resolv.conf to chroot jail $JAIL"
  cp $APP_GPG_KEY /var/chroot/$JAIL/var/www/ | tee -a build.log
  catch_error $? "copying $APP_GPG_KEY to chroot jail $JAIL"
  cp -R -f $APP_FILES /var/chroot/$JAIL/var/www/ | tee -a build.log
  catch_error $? "copying $APP_FILES to chroot jail $JAIL"
  ls /var/chroot/$JAIL/var/www/securedrop
  if [ -d /var/chroot/journalist ]; then
    mkdir -p /var/chroot/journalist/var/www/securedrop/temp/
  fi
 
  #schroot into the jail and configure it
  echo ""
  echo "schrooting into $JAIL and configuring it"
  schroot -c $JAIL -u root --directory /root <<FOE
    echo "Updating chroot system for $JAIL..."
    #create the application user in the jail
    useradd $JAIL

    catch_error() {
      if [ !"$1" = "0" ]; then
        echo "ERROR encountered $2"
        exit 1
      fi
    }

    #chown the needed file for the application user in the chroot jail
    chown $JAIL:$JAIL /var/www/$APP_GPG_KEY
    chown -R $JAIL:$JAIL /var/www/securedrop
    chown -R $JAIL:$JAIL /var/www/securedrop/{keys,store}

    #add the tor signing key and install interface dependencies

    if [ ! "$1" = "--no-updates" ]; then
      apt-key add /root/tor.asc
      apt-get -y update
      apt-get -y upgrade
      apt-get install $(grep -vE "^\s*#" $JAIL-requirements.txt  | tr "\n" " ")  | tee -a build.log
      catch_error $? "installing app dependencies"
      echo $(grep -vE "^\s*#" $JAIL-requirements.txt  | tr "\n" " ")

      #Install tor repo, keyring and tor
      echo ""
      echo "Installing tor for $JAIL..."
      apt-key add /root/tor.asc | tee -a build.log
      apt-get -y install deb.torproject.org-keyring tor
      catch_error $? "installing tor"
      echo "Tor installed for $JAIL"
    
      echo 'Installing pip dependencies for $JAIL...'
      pip install -r /var/www/securedrop/requirements.txt | tee -a build.log
      echo 'pip dependencies installed for $JAIL'
      echo "$(grep -vE "^\s*#" /var/www/securedrop/requirements.txt  | tr "\n" " ")"
    fi

    echo "Lock tor user..."
    passwd -l debian-tor
    echo "tor user locked"

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
      rm /etc/apache2/sites-available/*default*
      rm /etc/apache2/sites-enabled/*default*
    fi

    echo 'default apache sites removed for $JAIL'


    service apache2 stop
    catch_error $? "stopping apache"
FOE

  cp -f $JAIL.apache2.conf /var/chroot/$JAIL/etc/apache2/apache2.conf | tee -a build.log
  catch_error $? "copying $JAIL.apache2.conf"
  cp -f $JAIL.ports.conf /var/chroot/$JAIL/etc/apache2/ports.conf | tee -a build.log
  catch_error $? "copying $JAIL.ports.conf"
  cp -f $JAIL.wsgi /var/chroot/$JAIL/var/www/securedrop/$JAIL.wsgi | tee -a build.log
  catch_error $? "copying $JAIL.wsgi"
  cp -f $JAIL.security /var/chroot/$JAIL/etc/apache2/conf.d/security | tee -a build.log
  catch_error $? "copying $JAIL.security"
  cp -f $JAIL.site /var/chroot/$JAIL/etc/apache2/sites-enabled/$JAIL | tee -a build.log
  catch_error $? "copying $JAIL.site"
  cp -f $JAIL.torrc /var/chroot/$JAIL/etc/tor/torrc | tee -a build.log
  catch_error $? "copying $JAIL.torrc"
  #Generate the config.py file for the web interface
  cp -f $JAIL.config.py /var/chroot/$JAIL/var/www/securedrop/config.py
  catch_error $? "copying $JAIL.config.py template"
 
  cat /var/chroot/$JAIL/var/www/securedrop/config.py 
  echo "Generating config.py values"
  perl -pi -e "s/APP_GPG_KEY_FINGERPRINT/${APP_GPG_KEY_FINGERPRINT}/" /var/chroot/$JAIL/var/www/securedrop/config.py
  echo "Generating BCRYPT SALT"
  echo "BCRYPT_SALT='$BCRYPT_SALT'" >> /var/chroot/$JAIL/var/www/securedrop/config.py

  if ! grep -q SECRET_KEY* /var/chroot/$JAIL/var/www/securedrop/config.py; then
    echo "SECRET_KEY='$SECRET_KEY'" >> /var/chroot/$JAIL/var/www/securedrop/config.py
  fi 
  echo "Generating SECRET_KEY"
  perl -pi -e "s/SECRET_KEY_VALUE/${SECRET_KEYi}/" /var/chroot/$JAIL/var/www/securedrop/config.py
  cat  /var/chroot/$JAIL/var/www/securedrop/config.py
done

#Configure the source interface specific settings
echo ""
echo "Configuring the source interface specific settings..."
schroot -c source -u root --directory /root << FOE
  rm -R /var/www/securedrop/{journalist_templates,journalist.py,example*,*.md,test*}

  if [ -d "/root/tor-keys/$JAIL" ]; then
    cp -p /root/tor-keys/$JAIL/{client_keys,private_key} /var/lib/tor/hidden_service/
    srm -R /root/tor-keys/$JAIL
    catch_error $? "removing tmp keys"
  fi

  service apache2 restart
  service tor restart
  echo "Done setting up $JAIL"
FOE
echo "Done setting up the source interface specific settings"

#Cofnigure the journalist interface specific settings
echo ""
echo "Configuring the journalist interface specific settings"
schroot -c journalist -u root --directory /root << FOE
  echo "Starting to configure apache for journalist"
  rm -R /var/www/securedrop/{source_templates,source.py,example*,*.md,test*} | tee -a build.log

  echo "Importing application gpg public key on $JAIL"
  su -c "gpg2 --homedir /var/www/securedrop/keys --import /var/www/$APP_GPG_KEY" $JAIL
  service apache2 restart
  service tor restart
FOE

cat <<EOF > /etc/rc.local
#commands to be run after reboot for securedrop
mount -o bind /proc /var/chroot/source/proc
mount -o bind /proc /var/chroot/journalist/proc
mount -o bind /var/securedrop/store /var/chroot/journalist/var/www/securedrop/store
mount -o bind /var/securedrop/store /var/chroot/source/var/www/securedrop/store
mount -o bind /var/securedrop/keys /var/chroot/source/var/www/securedrop/keys
mount -o bind /var/securedrop/keys /var/chroot/journalist/var/www/securedrop/keys
schroot -u root -a service apache2 restart --directory /root
schroot -u root -a service tor restart --directory /root
EOF

#Wait 10 seconds for tor keys to be configured and print tor onion urls
sleep 10
echo "Source onion url is: "
echo `cat /var/chroot/source/var/lib/tor/hidden_service/hostname`

echo "You will need to append ':8080' to the end of the journalist onion url"
echo "The document interface's onion url and auth values:"
echo `cat /var/chroot/journalist/var/lib/tor/hidden_service/hostname`
exit 0
