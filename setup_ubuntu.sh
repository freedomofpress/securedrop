#! /bin/bash

# define colored output for some statements
bold=$(tput bold)
blue=$(tput setaf 4)

DEPENDENCIES='gnupg2 secure-delete haveged python-pip python-virtualenv'

echo "Welcome to the SecureDrop setup script for Debian/Ubuntu."
echo "If you've already cloned the repo, run this script in the folder containing the repo. (That is, one level out.)"
echo "Are you sure you want to proceed? [Y/N]"
read goahead

if [[ $goahead = 'n' || $goahead = 'N' ]]; then
    echo "Exiting the installer."
    exit 1
fi

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

echo "Installing dependencies: "$DEPENDENCIES
sudo apt-get install $DEPENDENCIES

echo "Setting up the virtual environment..."
virtualenv securedrop/venv
source securedrop/venv/bin/activate
cd securedrop/deaddrop
pip install -r requirements.txt

echo "Setting up configurations..."
cp example_config.py config.py
mkdir -p ./tmp/deaddrop/{store,keys}
mkdir ./tmp/deaddrop_test
storepath=$(pwd)/tmp/store
keypath=$(pwd)/tmp/keys
testpath=$(pwd)/tmp/deaddrop_test
sed -i "s@^STORE_DIR.*@STORE_DIR=\'$storepath\'@" config.py
sed -i "s@^GPG_KEY_DIR.*@GPG_KEY_DIR=\'$keypath\'@" config.py
# TODO: replace below line so that indents are not hard-coded
sed -i "s@    TEST_DIR.*@    TEST_DIR=\'$testpath\'@" config.py

echo "" >> .gitignore
echo "# tmp directory containing keys" >> .gitignore
echo $(pwd)/tmp/ >> .gitignore

echo ""
echo "You will need a jouranlist key for development."
echo "Would you like to generate one or use the key included?"
echo "If you're not familiar with gpg2, you ought to import the key."
echo "Type 'g' and push ENTER to generate, otherwise leave blank and push ENTER."
read genkey

if [[ $genkey != "" ]]; then
    echo "Generating new key."
    gpg2 --homedir ./tmp/deaddrop/keys --gen-key
else
    echo "Importing key included in the repo."
    gpg2 --homedir ./tmp/deaddrop/keys --import test_journalist_key.*    
fi

echo "$bold$blue Once you've generated the dev key, copy the key fingerprint to the JOURNALIST_KEY field of config.py. You can find the key fingerprint by running:"
echo "gpg2 --homedir /tmp/deaddrop/keys --fingerprint"
tput sgr 0

echo ""
echo "Running unit tests... these should all pass!"
python test.py

echo ""
echo "And you're done!"
echo "To make sure everything works, try running the app in the virtual environment:"
echo "python source.py"
echo "python journalist.py"