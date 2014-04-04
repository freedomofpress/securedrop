#!/bin/bash

# check for root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

# install deps and compile
sudo apt-get update
sudo apt-get install build-essential
gcc -o /home/amnesia/Persistent/update_torrc update_torrc.c

# prepare .torrc.additions
cp .torrc.additions /home/amnesia/Persistent 
gedit /home/amnesia/Persistent/.torrc.additions

# set permissions
chown root:root /home/amnesia/Persistent/update_torrc
chmod 755 /home/amnesia/Persistent/update_torrc
chmod +s /home/amnesia/Persistent/update_torrc 
chown root:root /home/amnesia/Persistent/.torrc.additions
chmod 444 /home/amnesia/Persistent/.torrc.additions

