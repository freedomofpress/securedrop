#!/bin/bash

# stop setup script if any command fails
set -e
# uncomment to print debugging information
#set -x

usage() {
  cat <<EOS
Usage: setup_dev.sh [-uh] [-r SECUREDROP_ROOT]

   -r SECUREDROP_ROOT  # specify a root driectory for docs, keys etc.
   -u                  # unaided execution of this script (useful for Vagrant)
   -h                  # This help message.

EOS
}

SOURCE_ROOT=$(dirname $0)

securedrop_root=$(pwd)/.securedrop
DEPENDENCIES="gnupg2 secure-delete haveged python-dev python-pip sqlite python-distutils-extra"


while getopts "r:uh" OPTION; do
    case $OPTION in
        r)
            securedrop_root=$OPTARG
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

echo "Installing dependencies: "$DEPENDENCIES
sudo apt-get update
sudo apt-get -y install $DEPENDENCIES
sudo pip install --upgrade distribute
sudo pip install -r source-requirements.txt
sudo pip install -r document-requirements.txt
sudo pip install -r test-requirements.txt

echo "Setting up configurations..."
# set up the securedrop root directory
cp config/base.py.example config/base.py
cp config/test.py.example config/test.py
cp config/development.py.example config/development.py

sed -i "s@^SECUREDROP_ROOT.*@SECUREDROP_ROOT = '$securedrop_root'@" config/development.py

mkdir -p $securedrop_root/{store,keys,tmp}
keypath=$securedrop_root/keys

# avoid the "unsafe permissions on GPG homedir" warning
chmod 700 $keypath

# generate and store random values required by config.py
secret_key=$(random 32)
scrypt_id_pepper=$(random 32)
scrypt_gpg_pepper=$(random 32)
sed -i "s@    SECRET_KEY.*@    SECRET_KEY='$secret_key'@" config/base.py
sed -i "s@^SCRYPT_ID_PEPPER.*@SCRYPT_ID_PEPPER='$scrypt_id_pepper'@" config/base.py
sed -i "s@^SCRYPT_GPG_PEPPER.*@SCRYPT_GPG_PEPPER='$scrypt_gpg_pepper'@" config/base.py

# initialize development database (development uses sqlite by default)
echo "Creating database tables..."
SECUREDROP_ENV=development python -c 'import db; db.create_tables()'

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
journalistkey=$(gpg2 --homedir $keypath --fingerprint | grep fingerprint | cut -d"=" -f 2 | sed 's/ //g' | head -n 1)
echo "Using journalist key with fingerprint $journalistkey"
sed -i "s@^JOURNALIST_KEY.*@JOURNALIST_KEY='$journalistkey'@" config/development.py

# We encountered issues using PhantomJS 1.9.6 (from the repos) with Selenium.
# Using 1.9.2 until the bugs in the repo release are fixed.
echo ""
echo "Installing PhantomJS"
PHANTOMJS_URL='https://phantomjs.googlecode.com/files/phantomjs-1.9.2-linux-x86_64.tar.bz2'
PHANTOMJS_PATH_IN_ARCHIVE='phantomjs-1.9.2-linux-x86_64/bin/phantomjs'
PHANTOMJS_BINARY_PATH='/usr/local/bin/phantomjs'
# Use -nv because wget's progress bar doesn't work on a non-tty, and it prints
# a bunch of garbage to the screen.
wget -nv -O- $PHANTOMJS_URL | sudo sh -c "tar -O -jxf - $PHANTOMJS_PATH_IN_ARCHIVE > $PHANTOMJS_BINARY_PATH"
sudo chown vagrant:vagrant $PHANTOMJS_BINARY_PATH
chmod +x $PHANTOMJS_BINARY_PATH

echo ""
echo "Running unit tests... these should all pass!"
set +e # turn flag off so we can check if the tests failed
./test.sh

if [[ $? != 0 ]]; then
    echo "$bold$red It looks like something went wrong in your dev setup."
    echo "Please let us know by opening an issue on Github: https://github.com/freedomofpress/securedrop/issues/new"
    echo $normalcolor
fi

echo $bold$blue
echo "And you're done!"
echo $normalcolor
echo "To make sure everything works, try running the app:"
echo ""
echo "$ vagrant ssh"
echo "$ cd /vagrant/securedrop"
echo "$ python source.py &"
echo "$ python journalist.py &"
echo ""
echo "Now you can visit the site at 127.0.0.1:{8080,8081} in your browser."
echo ""
echo "To re-run tests:"
echo "cd /vagrant/securedrop"
echo "./test.sh"

