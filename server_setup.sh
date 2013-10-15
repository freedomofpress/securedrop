#!/bin/bash
#
# Requirements:
# 1. 3 updated ubuntu 12.04 servers
# 2. The 'serverKeys.tar.gz' file from the viewingSetup.sh script
#
# Usage:
#  ./serverSetup.sh
#  Then follow the instructions
#
PUPPETRELEASEDEB="https://apt.puppetlabs.com/puppetlabs-release-precise.deb"
PUPPETDEBNAME="puppetlabs-release-precise.deb"i
PUPPETMASTERDEPENDENCIES="rubygems sqlite3 libsqlite3-ruby"
PUPPETMODULES='puppetlabs-apt puppetlabs-git puppetlabs-stdlib'
OSSECBINARYURL="https://pressfreedomfoundation.org/securedrop-files/ossec-binary.tgz"
OSSECBINARY="ossec-binary.tgz"

  # Check for root
  function rootCheck {
    if [[ $EUID -ne 0 ]]; then
      echo "This script must be run as root" 1>&2
      exit 1
    fi
  }

  # Download puppet ppa package
  function puppetDownload {
    if [ -f /etc/apt/sources.list.d/puppetlabs.list ]; then
      wget $PUPPETRELEASEDEB
      dpkg -i $PUPPETDEBNAME
      apt-get update -y
      rm $PUPPETDEBNAME
    else
      echo 'Puppet ppa is already installed'
    fi
  }

  # On puppet master install puppetmaster required packages
  function installPuppetMaster {
    apt-get install puppetmaster $PUPPETMASTERDEPENDENCIES -y
  }

  # On puppet master install puppet module tool
  function installPuppetModuleTool {
    if ! type -P puppet-module; then
      cd /etc/puppet/modules
      gem install puppet-module
    else
      echo "Puppet module tool already installed"
    fi
  }

  # On puppet master install rails
  function installRails {
    if [[ $(rails -v) != "Rails 2.2.2" ]]; then
      gem install rails -v 2.2.2 --no-ri --no-rdoc
    else
      echo "Rails already installed"
    fi
  }

  # On puppet master install puppet modules
  function installPuppetModules {
    DIR='/etc/puppet/modules'
    cd $DIR
    for PUPPETMODULE in $PUPPETMODULES
    do
      NAME=$(echo $PUPPETMODULE | awk -F "-" '{print $2}')
      if [ ! -d "/etc/puppet/modules/$NAME" ]; then
        echo "Installing $NAME"
        puppet module install $PUPPETMODULE
      else
        echo "$PUPPETMODULE already installed"
      fi
    done
  }

  #Enable puppet stored configs
  function enablePuppetStoredconfigs {
    if ! grep "thin_storeconfigs" /etc/puppet/puppet.conf; then
      echo "thin_storeconfigs = true" >> /etc/puppet/puppet.conf
    fi

    if ! grep "dbadpter" /etc/puppet/puppet.conf; then
      echo "dbadpter = sqlite3" >> /etc/puppet/puppet.conf
    fi
  }

  #Install deaddrop files
  function copyDeaddropFiles {
    cp -Rfp $CURRENTDIR/{manifests,modules} /etc/puppet/
  }

  #Download ossec binary
  function downloadOSSECBinary {
    cd $CURRENTDIR
    echo ''
    read -p "Download OSSEC binary from $OSSECBINARYURL? (y/n) " -e -i n DOWNLOADFROMINTERNET

    if [ $DOWNLOADFROMINTERNET == 'n' ]; then
      read -p 'Enter the full path to the OSSEC binary: ' -e -i ~/$OSSECBINARY OSSECBINARY
    else
      wget $OSSECBINARYURL
    fi
    mkdir -p /etc/puppet/modules/ossec/files/
    mv $OSSECBINARY /etc/puppet/modules/ossec/files/
  }

  #Downlaod webpy
  function downloadWebpy {
    cd $CURRENTDIR
    if [ ! -d '/etc/puppet/modules/deaddrop/files/webpy/web' ]; then
      echo ''
      read -p 'Download webpy from github? (y/n) ' -e -i n DOWNLOADFROMINTERNET

      if [ DOWNLOADFROMINTERNET == 'n' ]; then
        read -p 'Enter the full path to webpy directory: ' -e -i ~/webpy WEBPY
        mv $WEBPY /etc/puppet/deaddrop/files/
      else
        git clone git://github.com/webpy/webpy.git /etc/puppet/modules/deaddrop/files/webpy
      fi
    fi
  }

  # Enter Environment Variables
  function enterEnvironmentVariables {
    DIR="/etc/puppet/manifests"
    echo ''
    echo '##########################################################'
    echo 'You will need to provide the following environment'
    echo 'specific information.'
    echo "- The application's public gpg key"
    echo '- Monitor, Source and Document Server IP address and fully'
    echo '  qualified domain names'
    echo '- The IP address that the admin will be SSHing from'
    echo '- The IP address of the firewall'
    echo "- The application PGP key's fingerprint"
    echo '- The SMTP server for email alerts'
    echo '- The email address to send alerts to'
    echo '##########################################################'
    echo ''

    cd $CURRENTDIR
    read -p "Enter the full path to application's public gpg key: " -e -i ../SecureDrop.asc KEYFILE
    cp -p $KEYFILE /etc/puppet/modules/deaddrop/files
    app_gpg_pub_key=$(basename "$KEYFILE")
    cd $DIR
    awk -v value="'$app_gpg_pub_key'" '$1=="$app_gpg_pub_key"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the application PGP fingerprint generated on the viewing station: "
    read app_gpg_fingerprint
    awk -v value="'$app_gpg_fingerprint'" '$1=="$app_gpg_fingerprint"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the Monitor server's IP address: "
    read monitor_ip
    awk -v value="'$monitor_ip'" '$1=="$monitor_ip"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the Monitor server's fully qualified domain: "
    read monitor_fqdn
    sed -i "s/monitor_fqdn/$monitor_fqdn/" nodes.pp
    awk -v value="'$monitor_fqdn'" '$1=="$monitor_hostname"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp


    echo -n "Enter the Source server's IP address: "
    read source_ip
    awk -v value="'$source_ip'" '$1=="$source_ip"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the Source server's fully qualified domain: "
    read source_fqdn
    sed -i "s/source_fqdn/$source_fqdn/" nodes.pp
    awk -v value="'$source_fqdn'" '$1=="$source_hostname"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the Document server's IP address: "
    read journalist_ip
    awk -v value="'$journalist_ip'" '$1=="$journalist_ip"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the Document server's fully qualified domain: "
    read journalist_fqdn
    sed -i "s/journalist_fqdn/$journalist_fqdn/" nodes.pp
    awk -v value="'$journalist_fqdn'" '$1=="$journalist_hostname"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the IP address that you will be SSHing to the Monitor Server from (other IPs will get blocked):"
    read admin_ip
    awk -v value="'$admin_ip'" '$1=="$admin_ip"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the management IP address of the firewall (or 127.0.0.1 if you don't have one): "
    read intFWlogs_ip
    awk -v value="'$intFWlogs_ip'" '$1=="$intFWlogs_ip"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the SMTP server for email alerts to use:  "
    read mail_server
    awk -v value="'$mail_server'" '$1=="$mail_server"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Enter the email address to send alerts to:  "
    read ossec_email_to
    awk -v value="'$ossec_email_to'" '$1=="$ossec_email_to"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Using 'date | sha256sum' to generate hmac_secret"
    hmac_secret=`date | sha256sum | cut -d ' ' -f1`
    echo "Your hmac_secret is $hmac_secret"
    awk -v value="'$hmac_secret'" '$1=="$hmac_secret"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

    echo -n "Using python-bcrypt's bcrypt.gensalt to create bcrypt salt"
    apt-get install python-pip python-dev -y
    pip install python-bcrypt
    bcrypt_salt=`python $CURRENTDIR/gen_bcrypt_salt.py`
    echo $bcrypt_salt
    awk -v value="'$bcrypt_salt'" '$1=="$bcrypt_salt"{$3=value}1' nodes.pp > nodes.pp.tmp && mv nodes.pp.tmp nodes.pp

   echo ''
   echo '############################################################'
   echo '#Check the values entered                                  #'
   echo '############################################################'
   echo ''
   cat $DIR/nodes.pp
   echo ''
   echo -n 'Are these okay (y/n): '
   read answer
   case $answer in
     "y")
       main
       ;;
     "n")
       enterEnvironmentVariables
       ;;
     *)
       echo 'invalid entry'
       main
       ;;
   esac
  }

  # Install puppet on the source and jouranlist servers
  function installAgents {
    DIR='/etc/puppet/manifests'
    cd $DIR
    echo ''
    echo ''
    echo '########################################################'
    echo 'This will install and configure puppet on the source and'
    echo 'document servers using the IP addresses provided'
    echo '########################################################'
    echo ''
    SOURCE=$(awk '{if ($1=="$source_ip") print $3;}' nodes.pp | sed "s/'//g")
    JOURNALIST=$(awk '{if ($1=="$journalist_ip") print $3;}' nodes.pp | sed "s/'//g")
    MONITOR=$(awk '{if ($1=="$monitor_ip") print $3;}' nodes.pp | sed "s/'//g")
    SOURCE_HOSTNAME=$(awk '{if ($1=="$source_hostname") print $3;}' nodes.pp | sed "s/'//g")
    JOURNALIST_HOSTNAME=$(awk '{if ($1=="$journalist_hostname") print $3;}' nodes.pp | sed "s/'//g")
    MONITOR_HOSTNAME=$(awk '{if ($1=="$monitor_hostname") print $3;}' nodes.pp | sed "s/'//g")
    AGENTS="$SOURCE $JOURNALIST"


    echo "Congiguring /etc/hosts file on $MONITOR_HOSTNAME server..."
    awk '$1=="127.0.0.1"{$3="puppet"}1' /etc/hosts > /etc/hosts.tmp && mv /etc/hosts.tmp /etc/hosts
    if  ! grep -q "$SOURCE_HOSTNAME" /etc/hosts; then
      echo "$SOURCE $SOURCE_HOSTNAME" >> /etc/hosts
    fi

    if ! grep -q "$JOURNALIST_HOSTNAME" /etc/hosts; then
      echo "$JOURNALIST	$JOURNALIST_HOSTNAME" >> /etc/hosts
    fi

    if ! grep -q "$MONITOR_HOSTNAME" /etc/hosts; then
      echo "$MONITOR $MONITOR_HOSTNAME" >> /etc/hosts
    fi
    cat /etc/hosts

    echo -n 'What is your username on the Source and Document server? '
    read REMOTEUSER

    for agent in $AGENTS
    do
    echo ''
    echo '#######################################################'
    echo "ssh to $agent as $REMOTEUSER"
    echo '#######################################################'
    echo ''

    ssh -t -t $REMOTEUSER@$agent "sudo /bin/sh -c 'echo "$MONITOR $MONITOR_HOSTNAME puppet" >> /etc/hosts;echo "$SOURCE $SOURCE_HOSTNAME" >> /etc/hosts; echo "$JOURNALIST $JOURNALIST_HOSTNAME" >> /etc/hosts; wget "http://apt.puppetlabs.com/puppetlabs-release-precise.deb"; dpkg -i "puppetlabs-release-precise.deb"; apt-get update; apt-get install puppet -y; puppet agent -t'"
    done

    echo ''
    echo '#######################################################'
    echo 'Agents are installed sign the agent certs on the puppet'
    echo 'master'
    echo '#######################################################'
    echo ''
  }

  #Sign All Certs
  function signAllCerts {
    echo ''
    echo '########################################################'
    echo 'This will sign all the waiting agent certs on the puppet'
    echo 'master'
    echo '########################################################'
    puppetca --sign --all
  }

  #run puppet manifests in correct order
  function runPuppetManifests {
    DIR='/etc/puppet/manifests/'
    cd $DIR
    MONITOR=$(awk '{if ($1=="$monitor_ip") print $3;}' nodes.pp | sed "s/'//g")
    SOURCE=$(awk '{if ($1=="$source_ip") print $3;}' nodes.pp | sed "s/'//g")
    JOURNALIST=$(awk '{if ($1=="$journalist_ip") print $3;}' nodes.pp | sed "s/'//g")
    AGENTS="$SOURCE $JOURNALIST"
    echo ''
    echo '##########################################'
    echo 'Running puppet manifests on monitor server'
    echo '##########################################'
    echo ''
    service puppetmaster restart
    puppet agent -t
    echo -n 'What is your username on the Source and Document server? '
    read REMOTEUSER
    for agent in $AGENTS
    do
    echo "ssh to $agent as $REMOTEUSER"
    ssh -t -t $REMOTEUSER@$agent "sudo /bin/sh -c 'service puppet restart; puppet agent -t'"
    done
  }

  function ossecAuthd {
    cd /var/ossec
    if [ ! -f /var/ossec/etc/sslmanager.cert ]; then
      openssl ecparam -name prime256v1 -genkey -out /var/ossec/etc/sslmanager.key
      openssl req -new -x509 -key /var/ossec/etc/sslmanager.key -out /var/ossec/etc/sslmanager.cert -days 365
      chown root:ossec /var/ossec/etc/sslmanager.cert
    fi
    /var/ossec/bin/ossec-authd -p 1515 -i $journalist_ip $source_ip >/dev/null 2>&1 &
    ssh -t -t $REMOTEUSER@$SOURCE "sudo /bin/sh -c '/var/ossec/bin/agent-auth -m $MONITOR'"
    ssh -t -t $REMOTEUSER@$SOURCE "sudo /bin/sh -c '/var/ossec/bin/agent-auth -m $MONITOR'"
  }

  function displayTorURL {
  echo "The source server's Tor URL is: "
  ssh -t -t $REMOTEUSER@$SOURCE "sudo /bin/sh -c 'cat /var/lib/tor/hidden_service/hostname'"

  echo "The document server's Tor URL for the journalists are:"
  ssh -t -t $REMOTEUSER@$JOURNALIST "sudo /bin/sh -c 'cat /var/lib/tor/hidden_service/hostname'"
  }

  function cleanUp {
    sysctl -p
    apt-get purge rubygems puppetmaster puppet gcc make libncurses5-dev build-essential  kernel-package git-core g++ python-setuptools sqlite3 libsqlite3-ruby python-pip -y 
    apt-get autoremove -y
    rm -Rf /etc/puppet

    echo -n 'What is your username on the Source and Document server? '
    read REMOTEUSER

    ssh -t -t $REMOTEUSER@source "sudo /bin/sh -c 'apt-get purge puppet rubygems puppetmaster puppet gcc make libncurses5-dev build-essential  kernel-package git-core g++ python-setuptools sqlite3 libsqlite3-ruby python-pip -y; apt-get autoremove -y'"
    ssh -t -t $REMOTEUSER@journalist "sudo /bin/sh -c 'apt-get purge puppet rubygems puppetmaster puppet gcc make libncurses5-dev build-essential  kernel-package git-core g++ python-setuptools sqlite3 libsqlite3-ruby python-pip -y; apt-get autoremove -y'"
  }

  #Main
  function main {
    CURRENTDIR=`pwd`
    rootCheck

    echo ''
    echo '############################################################'
    echo 'This script expects ~/SecureDrop.asc to be the application PGP key'
    echo 'The remaining steps will install puppet run the manifests'
    echo '(1) Install puppetmaster'
    echo '(2) Enter environment information'
    echo '(3) Install puppet agent on source and document servers'
    echo '(4) Sign agent certs'
    echo '(5) Run puppet manifests'
    echo '(6) Clean up puppet and install files'
    echo '(7) Apply GRSECURITY lock (if you have grsec-patched kernel)'
    echo '(0) quit'
    echo '###########################################################'
    echo ''
    echo -n 'Enter your choice (0-7): '
    read option
    case $option in
      #Install puppetmaster
      "1")
        puppetDownload
        installPuppetMaster
        installPuppetModuleTool
        installRails
        installPuppetModules
        enablePuppetStoredconfigs
        copyDeaddropFiles
        downloadOSSECBinary
        downloadWebpy
        main
        ;;
      #Enter Environment Variables
      "2")
        enterEnvironmentVariables
        main
        ;;
      #Install puppet on agents
      "3")
        installAgents
        main
        ;;
      #Sign certs
      "4")
        signAllCerts
        main
        ;;
      #Run puppet manifests monitor -> source -> journalist
      "5")
        runPuppetManifests
        runPuppetManifests
        ossecAuthd
        displayTorURL
        main
        ;;
      #After installation confirmed successfull cleanup unneeded
      #programs and files
      "6")
        cleanUp
        ;;
      #Steps to apply grsec lock
      "7")
        ;;
      "0")
        exit
        ;;
      *) echo invalid options;;
    esac
  }
main

#end
exit 0
