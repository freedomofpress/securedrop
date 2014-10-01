#!/bin/bash

# stop setup script if any command fails
set -e
# uncomment to print debugging information
#set -x

usage() {
  cat <<EOS
Usage: setup_dev.sh [-uh] [-r securedrop_data_root]

   -r securedrop_data_root  # specify a root driectory for docs, keys etc.
   -u                  # unaided execution of this script (useful for Vagrant)
   -h                  # This help message.

EOS
}

SOURCE_ROOT=$(dirname $0)

securedrop_data_root=/var/securedrop
DEPENDENCIES="gnupg2 secure-delete haveged python-dev python-pip sqlite python-distutils-extra xvfb firefox gdb"

while getopts "r:uh" OPTION; do
    case $OPTION in
        r)
            securedrop_data_root=$OPTARG
            ;;
        u)
            UNAIDED_INSTALL=true
            ;;
        h)
            usage
            exit 0
    esac
done

cd $SOURCE_ROOT/securedrop

random() {
  head -c $1 /dev/urandom | base64
}

#check platform and distro
opsys=`uname`

if [[ $opsys != 'Linux' ]]; then
    echo "This setup script only works for Linux platforms. Exiting script."
    exit 1
fi

distro=$(cat /etc/*-release | grep DISTRIB_ID | cut -d"=" -f 2)
if [[ -z $distro && -f "/etc/debian_version" ]]; then
    distro="Debian"
fi

if [[ $distro != "Ubuntu" && $distro != "Debian" ]]; then
    echo "This setup script only works for Ubuntu/Debian systems. Exiting script."
    exit 1
fi

if [ "$UNAIDED_INSTALL" != true ]; then
    bold=$(tput bold)
    blue=$(tput setaf 4)
    red=$(tput setaf 1)
    normalcolor=$(tput sgr 0)
fi

echo "Welcome to the SecureDrop setup script for Debian/Ubuntu."

# We need to set the locale in order to print ASCII QR codes.
# See http://stackoverflow.com/questions/23941875/setting-utf-8-locale-for-python-in-ubuntu-12-04
sudo sh -c "echo 'LC_ALL=\"en_US.UTF-8\"'  >  /etc/default/locale"

echo "Installing dependencies: "$DEPENDENCIES
sudo apt-get update
sudo apt-get -y install $DEPENDENCIES

sudo pip install --upgrade distribute
sudo pip install -r requirements/source-requirements.txt
sudo pip install -r requirements/document-requirements.txt
sudo pip install -r requirements/test-requirements.txt

echo "Setting up configurations..."

sudo mkdir -p $securedrop_data_root/{store,keys}
me=$(whoami)
sudo chown -R $me:$me $securedrop_data_root
keypath=$securedrop_data_root/keys

# avoid the "unsafe permissions on GPG homedir" warning
chmod 700 $keypath

# generate and store random values required by config.py
source_secret_key=$(random 32)
journalist_secret_key=$(random 32)k
scrypt_id_pepper=$(random 32)
scrypt_gpg_pepper=$(random 32)

# copy the config template to config.py
cp config.py.example config.py

# fill in the instance-specific configuration
# Use | instead of / for sed's delimiters, since some of the environment
# variables are paths and contain /'s, which confuses sed.
sed -i "s|{{ securedrop_data_root }}|$securedrop_data_root|" config.py
sed -i "s|{{ source_secret_key }}|$source_secret_key|" config.py
sed -i "s|{{ journalist_secret_key }}|$journalist_secret_key|" config.py
sed -i "s|{{ scrypt_id_pepper }}|$scrypt_id_pepper|" config.py
sed -i "s|{{ scrypt_gpg_pepper }}|$scrypt_gpg_pepper|" config.py

if [ "$UNAIDED_INSTALL" != true ]; then
    echo ""
    echo "You will need a journalist key for development."
    echo "Would you like to generate one or use the key included?"
    echo "If you're not familiar with gpg2, you ought to import the key."
    echo "$bold$blue Use these keys for development and testing only, NEVER production."
    echo $normalcolor
    echo "Type 'g' and push ENTER to generate, otherwise leave blank and push ENTER."
    read genkey
fi

if [[ "$genkey" != "" ]]; then
    echo "Generating new key."
    gpg2 --homedir $keypath --gen-key
else
    echo "Importing key included in the repo."
    gpg2 --homedir $keypath --import test_journalist_key.*
fi

# get journalist key fingerpint from gpg2, remove spaces, and put into config file
journalist_key=$(gpg2 --homedir $keypath --fingerprint | grep fingerprint | cut -d"=" -f 2 | sed 's/ //g' | head -n 1)
sed -i "s|{{ journalist_key }}|$journalist_key|" config.py
echo "Using journalist key with fingerprint $journalist_key"

echo "Creating database tables..."
SECUREDROP_ENV=dev python -c 'import db; db.init_db()'

# xvfb is needed to run the functional tests headlessly
echo "Configuring xvfb..."
sudo tee /etc/init.d/xvfb <<EOF
XVFB=/usr/bin/Xvfb
XVFBARGS=":1 -screen 0 1024x768x24 -ac +extension GLX +render -noreset"
PIDFILE=/var/run/xvfb.pid
case "\$1" in
  start)
    echo -n "Starting virtual X frame buffer: Xvfb"
    start-stop-daemon --start --quiet --pidfile \$PIDFILE --make-pidfile --background --exec \$XVFB -- \$XVFBARGS
    echo "."
    ;;
  stop)
    echo -n "Stopping virtual X frame buffer: Xvfb"
    start-stop-daemon --stop --quiet --pidfile \$PIDFILE
    echo "."
    ;;
  restart)
    \$0 stop
    \$0 start
    ;;
  *)
        echo "Usage: /etc/init.d/xvfb {start|stop|restart}"
        exit 1
esac

exit 0
EOF

sudo chmod +x /etc/init.d/xvfb
sudo update-rc.d xvfb defaults
sudo service xvfb start
sudo sh -c 'echo "export DISPLAY=:1" >> /etc/environment'
export DISPLAY=:1

echo ""
echo "Running unit tests... these should all pass!"
set +e # turn flag off so we can check if the tests failed
./manage.py test

TEST_RC=$?

if [[ $TEST_RC != 0 ]]; then
    echo "$bold$red It looks like something went wrong in your dev setup."
    echo "Please let us know by opening an issue on Github: https://github.com/freedomofpress/securedrop/issues/new"
    echo $normalcolor
    # Exit with the non-zero return code to trigger build failure on Travis CI
    exit $TEST_RC
fi

echo $bold$blue
echo "And you're done!"
echo $normalcolor
echo "To make sure everything works, try running the app:"
echo ""
echo "$ vagrant ssh"
echo "$ cd /vagrant/securedrop"
echo "$ ./manage.py start"
echo ""
echo "Now you can visit the site at 127.0.0.1:{8080,8081} in your browser."
echo ""
echo "To re-run tests:"
echo "cd /vagrant/securedrop"
echo "$ ./manage.py test"

