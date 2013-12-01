#!/bin/bash

install_source_specific() {
#Configure the source interface specific settings
echo ""
echo "Configuring the source interface specific settings..."
for SOURCE_SCRIPT in $SOURCE_SCRIPTS; do
  cp $SOURCE_SCRIPT /var/chroot/source/root/ | tee -a build.log
done

schroot -c source -u root --directory /root << FOE
  rm -R /var/www/securedrop/{journalist_templates,journalist.py,example*,*.md,test*}

  if [ -d "/root/tor-keys/source" ]; then
    cp -p /root/tor-keys/source/private_key /var/lib/tor/hidden_service/
    srm -R /root/tor-keys/source
  fi

  #Run additional scripts specific for interface
  for SOURCE_SCRIPT in $SOURCE_SCRIPTS; do
    echo "Running $SOURCE_SCRIPT in $JAIL"
    bash /root/$SOURCE_SCRIPT | tee -a build.log
  done
FOE
echo "Done setting up the source interface specific settings"
}
