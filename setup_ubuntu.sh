#! /bin/bash

# stop setup script if any command fails
set -e

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

DEPENDENCIES='gnupg2 secure-delete haveged python-dev python-pip python-virtualenv libimage-exiftool-perl'

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

echo "Setting up the virtual environment..."
virtualenv securedrop/venv
source securedrop/venv/bin/activate
cd securedrop/deaddrop
pip install -r requirements.txt

echo "Setting up configurations..."
# create directories for keys and store
# and add them to their respective environment variables in config.py
cp example_config.py config.py
mkdir -p ./tmp/deaddrop/{store,keys,tmp}
storepath=$(pwd)/tmp/deaddrop/store
keypath=$(pwd)/tmp/deaddrop/keys
temppath=$(pwd)/tmp/deaddrop/tmp
testpath=$(pwd)/tmp/deaddrop_test
sed -i "s@^STORE_DIR.*@STORE_DIR=\'$storepath\'@" config.py
sed -i "s@^GPG_KEY_DIR.*@GPG_KEY_DIR=\'$keypath\'@" config.py
sed -i "s@^TEMP_DIR.*@TEMP_DIR=\'$temppath\'@" config.py
# TODO: replace below line so that indents are not hard-coded :/
sed -i "s@    TEST_DIR.*@    TEST_DIR=\'$testpath\'@" config.py

echo "" >> .gitignore
echo "# containing keys and storage for development application" >> .gitignore
echo $(pwd)/tmp/ >> .gitignore

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

# avoid the "unsafe permissions on GPG homedir" warning
chmod 700 $keypath

# get journalist key fingerpint from gpg2, remove spaces, and put into config file
journalistkey=$(gpg2 --homedir $keypath --fingerprint | grep fingerprint | cut -d"=" -f 2 | sed 's/ //g')
sed -i "s@^JOURNALIST_KEY.*@JOURNALIST_KEY=\'$journalistkey\'@" config.py

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
echo "python source.py"
echo "python journalist.py"
