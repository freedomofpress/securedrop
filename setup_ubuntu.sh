#! /bin/bash

# stop setup script if any command fails
set -e
# uncomment to print debugging information
#set -x

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

# define colored output for some statements
bold=$(tput bold)
blue=$(tput setaf 4)
red=$(tput setaf 1)
normalcolor=$(tput sgr 0)

DEPENDENCIES='gnupg2 secure-delete haveged python-dev python-pip python-virtualenv mysql-server-5.5 libmysqlclient-dev'

# no password prompt to install mysql-server
mysql_root=$(head -c 20 /dev/urandom | python -c 'import sys, base64; print base64.b32encode(sys.stdin.read())')
mysql_securedrop=$(head -c 20 /dev/urandom | python -c 'import sys, base64; print base64.b32encode(sys.stdin.read())')
sudo debconf-set-selections <<EOF
mysql-server-5.5 mysql-server/root_password password $mysql_root
mysql-server-5.5 mysql-server/root_password_again password $mysql_root
EOF

echo "Welcome to the SecureDrop setup script for Debian/Ubuntu."

# Since this script lives in the top level of the securedrop repository, it is
# natural to expect that users will have cloned the repo, cd'ed into it, and
# are now running ./setup_ubuntu.sh. We will check that this is the case, and
# if so can skip some later steps.
if [[ -d ".git" && -n `grep "securedrop" .git/config` ]]; then
    cd .. # run this script in the directory *containing* the securedrop git repo
else
    echo "You are not running this script inside the Securedrop repo."
    echo "Do you need to clone the SecureDrop repo? [Y/N]"
    read gitans
    if [[ $gitans = 'y' || $gitans = 'Y' ]]; then

        echo "Type the path of where you would like to clone it, and then push ENTER."
        read sdpath
        cd $sdpath

        echo "If you are cloning from your own fork, type your Github username and push ENTER. If not, leave it blank and push ENTER."
        read gitusername
        if [[ $gitusername != "" ]]; then
            echo "Cloning the repo from "$gitusername "..."
            git clone https://github.com/$gitusername/securedrop.git
        else
            echo "Cloning the repo..."
            git clone https://github.com/freedomofpress/securedrop.git
        fi
    fi
fi

if [ ! -d "securedrop" ]; then
    echo "Couldn't find the securedrop repo... exiting!"
    exit 1
fi

echo "Installing dependencies: "$DEPENDENCIES
sudo apt-get -y install $DEPENDENCIES

echo "Setting up MySQL database..."
mysql -u root -p"$mysql_root" -e "create database securedrop; GRANT ALL PRIVILEGES ON securedrop.* TO 'securedrop'@'localhost' IDENTIFIED BY '$mysql_securedrop';"

# continue working in the application directory
cd securedrop/securedrop

echo "Setting up the virtual environment..."
virtualenv env
source env/bin/activate
pip install --upgrade distribute
pip install -r requirements.txt

echo "Setting up configurations..."
# set up the securedrop root directory
cp example_config.py config.py
securedrop_root=$(pwd)/.securedrop
sed -i "s@    SECUREDROP_ROOT='/tmp/securedrop'@    SECUREDROP_ROOT='$securedrop_root'@" config.py
mkdir -p $securedrop_root/{store,keys,tmp}
keypath=$securedrop_root/keys

# avoid the "unsafe permissions on GPG homedir" warning
chmod 700 $keypath

# initialize development database
# config.py will use sqlite by default, but we've set up a mysql database as
# part of this installation so it is very easy to switch to it.
# Also, MySQL-Python won't install (which breaks this script) unless mysql is installed.
sed -i "s@^# DATABASE_PASSWORD.*@# DATABASE_PASSWORD=\'$mysql_securedrop\'@" config.py
echo "Creating database tables..."
python -c 'import db; db.create_tables()'

# generate and store random values required by config.py
secret_key=$(python -c 'import os; print os.urandom(32).__repr__().replace("\\","\\\\")')
bcrypt_id_salt=$(python -c 'import bcrypt; print bcrypt.gensalt()')
bcrypt_gpg_salt=$(python -c 'import bcrypt; print bcrypt.gensalt()')
sed -i "s@    SECRET_KEY.*@    SECRET_KEY=$secret_key@" config.py
sed -i "s@^BCRYPT_ID_SALT.*@BCRYPT_ID_SALT='$bcrypt_id_salt'@" config.py
sed -i "s@^BCRYPT_GPG_SALT.*@BCRYPT_GPG_SALT='$bcrypt_gpg_salt'@" config.py

echo ""
echo "You will need a journalist key for development."
echo "Would you like to generate one or use the key included?"
echo "If you're not familiar with gpg2, you ought to import the key."
echo "$bold$blue Use these keys for development and testing only, NEVER production."
echo $normalcolor
echo "Type 'g' and push ENTER to generate, otherwise leave blank and push ENTER."
read genkey

if [[ $genkey != "" ]]; then
    echo "Generating new key."
    gpg2 --homedir $keypath --gen-key
else
    echo "Importing key included in the repo."
    gpg2 --homedir $keypath --import test_journalist_key.*
fi

# get journalist key fingerpint from gpg2, remove spaces, and put into config file
journalistkey=$(gpg2 --homedir $keypath --fingerprint | grep fingerprint | cut -d"=" -f 2 | sed 's/ //g' | head -n 1)
echo "Using journalist key with fingerprint $journalistkey"
sed -i "s@^JOURNALIST_KEY.*@JOURNALIST_KEY='$journalistkey'@" config.py

echo ""
echo "Running unit tests... these should all pass!"
set +e # turn this flag off so we can checks if the tests failed
python test.py

if [[ $? != 0 ]]; then
    echo "$bold$red It looks like something went wrong in your dev setup."
    echo "Feel free to open an issue on Github: https://github.com/freedomofpress/securedrop/issues/new"
    echo $normalcolor
fi

echo $bold$blue
echo "And you're done!"
echo $normalcolor
echo "To make sure everything works, try running the app in the development environment:"
echo "cd securedrop"
echo ". env/bin/activate"
echo "python source.py"
echo "python journalist.py"
