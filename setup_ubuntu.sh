#! /bin/bash

DEPENDENCIES='gnupg2 secure-delete haveged python-pip python-virtualenv'

echo "Welcome to the SecureDrop setup script for Debian/Ubuntu."
echo "If you've already cloned the repo, run this script inside the \
folder containing the repo."
echo "Are you sure you want to proceed? [Y/N]"
read goahead

if [ $goahead = 'n' -o $goahead = 'N' ]; then
	echo "Exiting the installer."
	exit 1
fi

echo "Do you need to clone the SecureDrop repo? [Y/N]"
read gitans
if [ $gitans = 'y' -o $gitans = 'Y' ]; then

	echo "Type the path of where you would like to clone it, and then \
	push ENTER."
	read sdpath
	cd $sdpath

	echo "If you are cloning from your own fork, type your \
	Github username and push ENTER. If not, leave it blank and push ENTER."
	read gitusername
	if [ $gitusername != "" ]; then
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

echo "You will need a jouranlist key for development."
echo "Would you like to generate one or use the key included?"
echo "If you're not familiar with gpg2, you ought to import the key."
echo "Type 'g' and push ENTER to generate, otherwise leave blank \
and push ENTER."
read genkey

if [ $genkey != "" ]; then
	echo "Generating new key."
	gpg2 --home /tmp/deaddrop/keys --gen-key
else
	echo "Importing key included in the repo."
	gpg2 --homedir /tmp/deaddrop/keys --import test_journalist_key.*	
fi

echo "Running unit tests... these should all pass!"
python tests.py

echo "And you're done!"