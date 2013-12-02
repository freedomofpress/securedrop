#!/bin/bash

install_chroot() {
#Create chroot jails for source and document interfaces
echo "Creating chroot jails for source and document interfaces..."
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

  #Clean previous chroot jails
  clean_chroot_jail() {
    if [ -f "/var/chroot/$JAIL/var/lib/tor/hidden_service/client_keys" ]; then
      mkdir -p /tmp/tor-keys/$JAIL  
      catch_error $? "making /tmp/tor-key/$JAIL"
      cp -f /var/chroot/$JAIL/var/lib/tor/hidden_service/client_keys /tmp/tor-keys/$JAIL
      catch_error $? "copying client_keys for $JAIL"
    elif [ -f "/var/chroot/$JAIL/var/lib/tor/hidden_service/private_key" ]; then
      mkdir -p /tmp/tor-keys/$JAIL
      catch_error $? "making /tmp/tor-keys/$JAIL"
      cp -f /var/chroot/$JAIL/var/lib/tor/hidden_service/private_key /tmp/tor-keys/$JAIL
      catch_error $? "cp private_key of $JAIL"
    fi 

    schroot -c $JAIL -u root --directory /root service tor stop
    schroot -c $JAIL -u root --directory /root service apache2 stop
    MOUNTED_DIRS="/var/chroot/$JAIL/proc /var/chroot/$JAIL/var/www/securedrop/store /var/chroot/$JAIL/var/www/securedrop/keys"
    for MOUNTED_DIR in $MOUNTED_DIRS; do
      if mount | grep -q $MOUNTED_DIR; then
        echo "un mounting $MOUNTED_DIR"
        umount $MOUNTED_DIR | tee -a build.log
        catch_error $? "umounting $MOUNTED_DIR"
        echo "$MOUNTED_DIR un mounted"
      fi
    done

    if [ -d /var/chroot/$JAIL ]; then
      echo "secure-deleting /var/chroot/$JAIL..."
      rm -Rf /var/chroot/$JAIL | tee -a build.log
      catch_error $? "secure-deleting /var/chroot/$JAIL reboot and run --force-clean again"
      echo "/var/chroot/$JAIL secure-deleted"
    fi

    create_chroot_env

    if [ -d "/tmp/tor/keys/$JAIL" ]; then
      echo "copying tor keys to /var/chroot/$JAIL/root/tor-keys/$JAIL/..."
      cp -p -f /tmp/tor-keys/$JAIL/{client_keys,private_key} /var/chroot/$JAIL/root/tor-keys/$JAIL
      catch_error $? "copying tor-keys/$JAIL"
      echo "backed up'd tor keys are copied to /var/chroot/$JAIL/root/tor-keys/$JAIL/" 
      echo "secure-deleting /tmp/tor/keys/$JAIL..."
      srm -R /tmp/tor-keys/$JAIL | tee -a build.log
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

  #Creating needed directory structure and files for the chroot jail
  echo "Creating the needed directories and files for the $JAIL chroot jail..."
  mkdir -p /var/chroot/$JAIL/{proc,etc,var,root} | tee -a build.log
  catch_error $? "creating /var/chroot/$JAIL/{proc,etc,var}"
  mkdir -p /var/chroot/$JAIL/etc/{apt,tor} | tee -a build.log
  catch_error $? "creating /var/chroot/$JAIL/etc/{apt,tor}"
  mkdir -p /var/chroot/$JAIL/var/www/securedrop/{store,keys} | tee -a build.log
  catch_error $? "creating /var/chroot/$JAIL/var/www/securedrop/{store,keys}"
  mkdir -p /var/securedrop/{store,keys} | tee -a build.log
  catch_error $? "creating /var/securedrop/{store,keys}"
  mkdir -p /var/chroot/$JAIL/etc/apache2/sites-enabled/ | tee -a build.log
  catch_error $? "creating /var/chroot/$JAIL/etc/apache2/sites-enabled/"
  mkdir -p /var/chroot/$JAIL/etc/apache2/conf.d/ | tee -a build.log
  catch_error $? "creating apache2/conf.d in $JAIL"
  chown -R securedrop:securedrop /var/securedrop/ | tee -a build.log
  catch_error $? "chown'ing securedrop:securedrop /var/securedrop/"
  mount -o bind /proc /var/chroot/$JAIL/proc | tee -a build.log
  catch_error $? "mounting /proc"
  mount -o bind /var/securedrop/store /var/chroot/$JAIL/var/www/securedrop/store | tee -a build.log
  catch_error $? "mounting /var/securedrop/store"
  mount -o bind /var/securedrop/keys /var/chroot/$JAIL/var/www/securedrop/keys | tee -a build.log
  catch_error $? "mounting /var/securedrop/keys"

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
  #Generate the config.py file for the web interface
  cp -f $JAIL.config.py /var/chroot/$JAIL/var/www/securedrop/config.py
  catch_error $? "copying $JAIL.config.py template"
  if [ -d /var/chroot/document ]; then
    mkdir -p /var/chroot/document/var/www/securedrop/temp/
    catch_error $? "creating /var/chroot/document/var/www/securedrop/temp/"
  fi

  INT_REQS=$(grep -vE "^\s*#" $JAIL-requirements.txt  | tr "\n" " ")
  echo ""

  # If document server set passwords
  if [ $JAIL = 'document' ]; then
    echo "Creating mysql preseed file"
    mysql_root=$(head -c 20 /dev/urandom | python -c 'import sys, base64; print base64.b32encode(sys.stdin.read())')
    mysql_securedrop=$(head -c 20 /dev/urandom | python -c 'import sys, base64; print base64.b32encode(sys.stdin.read())')
    sed -i "s|MYSQL_USER_PASS|$mysql_securedrop|g" /var/chroot/$JAIL/var/www/securedrop/config.py
  fi

  #schroot into the jail and configure it
  echo ""
  echo "schrooting into $JAIL and configuring it"
  schroot -c $JAIL -u root --directory /root <<FOE
    echo "Updating chroot system for $JAIL..."

    #create the application user in the jail
    useradd $JAIL | tee -a build.log

    #chown the needed file for the application user in the chroot jail
    chown $JAIL:$JAIL /var/www/$APP_GPG_KEY | tee -a build.log
    chown -R $JAIL:$JAIL /var/www/securedrop | tee -a build.log
    chown -R $JAIL:$JAIL /var/www/securedrop/{keys,store} | tee -a build.log

    if [ ! "$1" = "--no-updates" ]; then
      #add the tor signing key and install interface dependencies
      apt-key add /root/tor.asc | tee -a build.log
      apt-get -y update | tee -a build.log
      apt-get -y upgrade | tee -a build.log

      #For the document interface create preseed file for mysql install
      if [ $JAIL = "document" ]; then
        # no password prompt to install mysql-server
        echo "Creating mysql preseed file"
        debconf-set-selections <<EOF
        mysql-server-5.5 mysql-server/root_password password $mysql_root
        mysql-server-5.5 mysql-server/root_password_again password $mysql_root
EOF
      fi

      # Install interface specific requirements
      apt-get install -y $INT_REQS | tee -a build.log
      echo "the $JAIL interface's dependencies are installed"


      #Install tor repo, keyring and tor
      echo ""
      echo "Installing tor for $JAIL..."
      apt-key add /root/tor.asc | tee -a build.log
      apt-get install -y -q deb.torproject.org-keyring tor | tee -a build.log
      service tor stop | tee -a build.log
      echo "Tor installed for $JAIL"

      echo 'Installing pip dependencies for $JAIL...'
      pip install --upgrade setuptools | tee -a build.log
      pip install -r /var/www/securedrop/$JAIL-requirements.txt | tee -a build.log
      echo 'pip dependencies installed for $JAIL'
      # If document chroot setup mysql databases
      if [ $JAIL = "document" ]; then
        # initialize production database                                              
        # Also, MySQL-Python won't install (which breaks this script) unless mysql is installed.
        echo "Creating database..."                                             
        mysql -u root -p"$mysql_root" -e "create database securedrop; GRANT ALL PRIVILEGES ON securedrop.* TO 'document_mysql'@'localhost' IDENTIFIED BY '$mysql_securedrop';" | tee -a build.log
        echo "Creating database tables..."                                             
        cd /var/www/securedrop/
        python -c 'import os; import db; db.create_tables()' | tee -a build.log
      fi
    fi

    echo "Lock tor user..."
    passwd -l debian-tor | tee -a build.log
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
    echo "default-ssl site disabled"

    if [ -f /var/www/index.html ]; then
      rm /var/www/index.html
    fi

    if [ -f /etc/apache2/sites-available/default-ssl ]; then
      rm /etc/apache2/sites-available/default-ssl
    fi

    if [ -f /etc/apache2/sites-enabled/default-ssl ]; then
      rm /etc/apache2/sites-enabled/default-ssl
    fi

    if [ -f /etc/apache2/sites-available/000-default ]; then
      rm /etc/apache2/sites-available/000-default
    fi

    if [ -f /etc/apache2/sites-enabled/000-default ]; then
      rm /etc/apache2/sites-enabled/000-default
    fi

    echo 'default apache sites removed for $JAIL'

    service apache2 stop
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


  ONION_ADDRESS="$(echo /var/chroot/$JAIL/var/lib/tor/hidden_service/hostname)"
  sed -i "s|ONION_ADDRESS|$ONION_ADDRESS|g" /var/chroot/$JAIL/etc/apache2/sites-enabled/$JAIL

  if grep -q "APP_GPG_KEY_FINGERPRINT" /var/chroot/$JAIL/var/www/securedrop/config.py; then
    echo "Copying GPG Fingerprint to $JAIL/var/www/securedrop/config.py"
    sed -i -e "s|APP_GPG_KEY_FINGERPRINT|$APP_GPG_KEY_FINGERPRINT|g" /var/chroot/$JAIL/var/www/securedrop/config.py
    catch_error $? "copying APP_GPG_KEY_FINGERPRINT to /var/chroot/$JAIL/var/www/securedrop/config.py"
  fi

  if grep -q "BCRYPT_ID_SALT_VALUE" /var/chroot/$JAIL/var/www/securedrop/config.py; then
    echo "Generating BCRYPT ID SALT for $JAIL"
    sed -i -e "s|BCRYPT_ID_SALT_VALUE|${BCRYPT_ID_SALT}|g" /var/chroot/$JAIL/var/www/securedrop/config.py
    catch_error $? "generating $BCRYPT_ID_SALT in config.py for $JAIL"
  fi

  if grep -q "BCRYPT_GPG_SALT_VALUE" /var/chroot/$JAIL/var/www/securedrop/config.py; then
    echo "Generating BCRYPT GPG SALT for $JAIL"
    sed -i -e "s|BCRYPT_GPG_SALT_VALUE|${BCRYPT_GPG_SALT}|g" /var/chroot/$JAIL/var/www/securedrop/config.py
    catch_error $? "generating $BCRYPT_GPG_SALT in config.py for $JAIL"
  fi

  if grep -q "SECRET_KEY_VALUE" /var/chroot/$JAIL/var/www/securedrop/config.py; then
    echo "Generating SECRET_KEY for $JAIL"
    sed -i -e "s|SECRET_KEY_VALUE|${SECRET_KEY}|g" /var/chroot/$JAIL/var/www/securedrop/config.py
    catch_error $? "generating $SECRET_KEY in config.py for $JAIL"
  fi

done
}
