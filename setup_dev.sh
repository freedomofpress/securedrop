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
DEPENDENCIES="gnupg2 secure-delete haveged python-dev python-pip sqlite python-distutils-extra python-poppler xvfb firefox"

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
cat > config/test.py <<EOF
JOURNALIST_KEY='65A1B5FF195B56353CC63DFFCC40EF1228271441' # test_journalist_key.pub
SECUREDROP_ROOT='/tmp/securedrop_test'

FLASK_TESTING = True
FLASK_CSRF_ENABLED = False

DATABASE_ENGINE = 'sqlite'
DATABASE_FILE='/tmp/securedrop_test/db.sqlite'
EOF

mkdir -p $securedrop_root/{store,keys,tmp}
keypath=$securedrop_root/keys

# avoid the "unsafe permissions on GPG homedir" warning
chmod 700 $keypath

# generate and store random values required by config.py
secret_key=$(random 32)
scrypt_id_pepper=$(random 32)
scrypt_gpg_pepper=$(random 32)

# setup base configurations
cat > config/flask_defaults.py <<EOF
#### Flask Default Configuration

FLASK_DEBUG = False
FLASK_TESTING = False
FLASK_CSRF_ENABLED = True
FLASK_SECRET_KEY = '$secret_key'
EOF

cat > config/base.py <<EOF
#### Application Configuration

SOURCE_TEMPLATES_DIR = './source_templates'
JOURNALIST_TEMPLATES_DIR = './journalist_templates'
WORD_LIST = './wordlist'
NOUNS = './dictionaries/nouns.txt'
ADJECTIVES = './dictionaries/adjectives.txt'

SCRYPT_ID_PEPPER = '$scrypt_id_pepper' # os.urandom(32); for constructing public ID from source codename
SCRYPT_GPG_PEPPER = '$scrypt_gpg_pepper' # os.urandom(32); for stretching source codename into GPG passphrase
SCRYPT_PARAMS = dict(N=2**14, r=8, p=1)
EOF

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

# setup development environment
cat > config/development.py <<EOF
#### Development Configurations

JOURNALIST_KEY='$journalistkey' # fingerprint of the public key for encrypting submissions
SECUREDROP_ROOT='$securedrop_root'

FLASK_DEBUG = True

### Database Configuration

# Securedrop will use sqlite by default, but we've set up a mysql database as
# part of this installation so it is very easy to switch to it.
# Also, MySQL-Python won't install (which breaks this script) unless
# mysql is installed.
DATABASE_ENGINE = 'sqlite'
DATABASE_FILE='$securedrop_root/db.sqlite'

# Uncomment to use mysql (or any other database backend supported by
# SQLAlchemy). Make sure you have the necessary dependencies installed, and run
# 'python -c "import db; db.init_db()"' to initialize the database

# DATABASE_ENGINE = 'mysql'
# DATABASE_HOST = 'localhost'
# DATABASE_NAME = 'securedrop'
# DATABASE_USERNAME = 'securedrop'
# DATABASE_PASSWORD = '$mysql_securedrop'
EOF

echo "Creating database tables..."
SECUREDROP_ENV=development python -c 'import db; db.init_db()'

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
sudo service xvfb start
sudo sh -c 'echo "export DISPLAY=:1" >> /etc/profile'
source /etc/profile # source immediatly for travis

echo ""
echo "Running unit tests... these should all pass!"
set +e # turn flag off so we can check if the tests failed
./test.sh

TEST_RC=$?

if [[ $TEST_RC != 0 ]]; then
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

exit $TEST_RC
