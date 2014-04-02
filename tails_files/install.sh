#!/bin/bash

# check for root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi

# copy and edit files
cp update_torrc /home/amnesia/Persistent
cp .torrc.additions /home/amnesia/Persistent 
gedit /home/amnesia/Persistent/.torrc.additions

# set permissions
chown root:root /home/amnesia/Persistent/update_torrc
chmod 755 /home/amnesia/Persistent/update_torrc
chmod +s /home/amnesia/Persistent/update_torrc 
chown root:root /home/amnesia/Persistent/.torrc.additions
chmod 444 /home/amnesia/Persistent/.torrc.additions

