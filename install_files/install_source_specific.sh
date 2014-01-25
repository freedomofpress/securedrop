#!/bin/bash

install_source_specific() {
#Configure the source interface specific settings
echo ""
echo "Configuring the source interface specific settings..."
for SOURCE_SCRIPT in $SOURCE_SCRIPTS; do
  cp $SOURCE_SCRIPT /var/chroot/source/root/ | tee -a build.log
done

schroot -c source -u root --directory /root << FOE
  rm -R /var/www/securedrop/{COPYING,journalist_templates,journalist.py,document-requirements.txt,db.py,example*,*.md,test*} | tee -a build.log

  if [ -d "/root/tor-keys/source" ]; then
    cp -p /root/tor-keys/source/private_key /var/lib/tor/hidden_service/ | tee -a build.log
    srm -R /root/tor-keys/source | tee -a build.log
  fi

  #Run additional scripts specific for interface
  for SOURCE_SCRIPT in $SOURCE_SCRIPTS; do
    echo "Running $SOURCE_SCRIPT in $JAIL"
    bash /root/$SOURCE_SCRIPT | tee -a build.log
  done

  #Set min permissions on app code
  chown -R source:source /var/www/securedrop | tee -a build.log
  chmod -R 400 /var/www/securedrop/* | tee -a build.log
  chmod 500 /var/www/securedrop/dictionaries /var/www/securedrop/source_templates /var/www/securedrop/static | tee -a build.log
  chmod 700 /var/www/securedrop/keys /var/www/securedrop/store | tee -a build.log
  chmod 700 /var/www/securedrop/static/{css,i,js,libs,} | tee -a build.log
  chmod 700 /var/www/securedrop/static/i/tipbox | tee -a build.log
  chmod 700 /var/www/securedrop/static/js/libs | tee -a build.log
  chmod 700 /var/www/securedrop/static/libs/gritter | tee -a build.log
  chmod 700 /var/www/securedrop/static/libs/gritter/{css,images,js} | tee -a build.log
  
FOE
echo "Done setting up the source interface specific settings"
}
