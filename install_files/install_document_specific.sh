#!/bin/bash

install_document_specific() {

  #Configure the document interface specific settings
  echo ""
  echo "Configuring the document interface specific settings"

  for DOCUMENT_SCRIPT in $DOCUMENT_SCRIPTS; do
    cp $DOCUMENT_SCRIPT /var/chroot/document/root/ | tee -a build.log
  done

  #comma separate usernames for torrc file
  JOURNALIST_USERS_COMMA="$(echo "$JOURNALIST_USERS" | sed "s/\s/,/g")"
  echo "Creating stealth hidden service onion addresses for: $JOURNALIST_USERS_COMMA"
  sed -i "s/JOURNALIST_USERS_HERE/$JOURNALIST_USERS_COMMA/g" /var/chroot/document/etc/tor/torrc | tee -a build.log

  schroot -c document -u root --directory /root << FOE
    echo "Starting to configure apache for document "
    rm -R /var/www/securedrop/{COPYING,source_templates,source.py,example*,*.md,test*} | tee -a build.log

    #Set min permissions on app code
    chown -R document:document /var/www/securedrop | tee -a build.log
    chmod -R 400 /var/www/securedrop/* | tee -a build.log
    chmod 500 /var/www/securedrop/dictionaries /var/www/securedrop/journalist_templates /var/www/securedrop/static | tee -a build.log
    chmod 700 /var/www/securedrop/keys /var/www/securedrop/store | tee -a build.log
    chmod -R 600 /var/www/securedrop/store/* | tee -a build.log
    chmod 700 /var/www/securedrop/static/{css,i,js,libs,} | tee -a build.log
    chmod 700 /var/www/securedrop/static/i/tipbox | tee -a build.log
    chmod 700 /var/www/securedrop/static/js/libs | tee -a build.log
    chmod 700 /var/www/securedrop/static/libs/gritter | tee -a build.log
    chmod 700 /var/www/securedrop/static/libs/gritter/{css,images,js} | tee -a build.log
    chmod 600 /var/www/securedrop/db.sqlite | tee -a build.log
    #Create and import the applications gpg keypair
    echo "Importing application gpg public key on document interface "
    su -c "gpg2 --homedir /var/www/securedrop/keys --import /var/www/$APP_GPG_KEY" document | tee -a build.log

    #Run additional scripts specific for interface
    for DOCUMENT_SCRIPT in $DOCUMENT_SCRIPTS; do
      echo "Running $DOCUMENT_SCRIPT in "
      bash /root/$DOCUMENT_SCRIPT | tee -a build.log
    done
FOE
}
