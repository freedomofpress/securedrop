#!/bin/bash

# stop setup script if any command fails
set -e
# uncomment to print debugging information
#set -x

usage() {
  cat <<EOS
Usage: setup_ubuntu.sh [-uh] [-r SECUREDROP_ROOT]

   -r SECUREDROP_ROOT  # specify a root driectory for docs, keys etc.
   -u                  # unaided execution of this script (useful for Vagrant)
   -h                  # This help message.

EOS
}

SOURCE_ROOT=$(dirname $0)

securedrop_root=$(pwd)/.securedrop
DEPENDENCIES=$(grep -vE "^\s*#" $SOURCE_ROOT/install_files/document-requirements.txt  | tr "\n" " ")


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

if [ "$UNAIDED_INSTALL" -ne true ]; then
    bold=$(tput bold)
    blue=$(tput setaf 4)
    red=$(tput setaf 1)
    normalcolor=$(tput sgr 0)
fi

# no password prompt to install mysql-server
mysql_root=$(random 20)
mysql_securedrop=$(random 20)
sudo debconf-set-selections <<EOF
mysql-server-5.5 mysql-server/root_password password $mysql_root
mysql-server-5.5 mysql-server/root_password_again password $mysql_root
EOF

echo "Welcome to the SecureDrop setup script for Debian/Ubuntu."

echo "Installing dependencies: "$DEPENDENCIES
sudo apt-get update
sudo apt-get -y install $DEPENDENCIES

sudo /etc/init.d/mysql stop

sudo mysqld --skip-grant-tables &

sleep 2 && sudo mysql <<EOF
UPDATE mysql.user SET Password=PASSWORD('$mysql_root') WHERE User='root';
FLUSH PRIVILEGES;
EOF

sudo /etc/init.d/mysql stop && sudo /etc/init.d/mysql start

echo "Setting up MySQL database..."
mysql -u root -p"$mysql_root" -e "create database if not exists securedrop; GRANT ALL PRIVILEGES ON securedrop.* TO 'securedrop'@'localhost' IDENTIFIED BY '$mysql_securedrop';"

echo "Setting up the virtual environment..."
virtualenv env
source env/bin/activate
pip install --upgrade distribute
pip install -r source-requirements.txt
pip install -r document-requirements.txt
pip install -r test-requirements.txt

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

# initialize development database
# Securedrop will use sqlite by default, but we've set up a mysql database as
# part of this installation so it is very easy to switch to it.
# Also, MySQL-Python won't install (which breaks this script) unless mysql is installed.
sed -i "s@^# DATABASE_PASSWORD.*@# DATABASE_PASSWORD='$mysql_securedrop'@" config/development.py
echo "Creating database tables..."
SECUREDROP_ENV=development python -c 'import db; db.create_tables()'

if [ "$UNAIDED_INSTALL" -ne true ]; then
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
