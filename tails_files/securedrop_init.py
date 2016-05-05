#!/usr/bin/python

import os
import sys
import subprocess


# check for root
if os.geteuid() != 0:
    sys.exit('You need to run this as root')

# paths
path_torrc_additions = '/home/amnesia/Persistent/.securedrop/torrc_additions'
path_torrc_backup = '/etc/tor/torrc.bak'
path_torrc = '/etc/tor/torrc'

# load torrc_additions
if os.path.isfile(path_torrc_additions):
    torrc_additions = open(path_torrc_additions).read()
else:
    sys.exit('Error opening {0} for reading'.format(path_torrc_additions))

# load torrc
if os.path.isfile(path_torrc_backup):
    torrc = open(path_torrc_backup).read()
else:
    if os.path.isfile(path_torrc):
        torrc = open(path_torrc).read()
    else:
        sys.exit('Error opening {0} for reading'.format(path_torrc))

    # save a backup
    open(path_torrc_backup, 'w').write(torrc)

# append the additions
open(path_torrc, 'w').write(torrc + torrc_additions)

# reload tor
subprocess.call(['systemctl', 'reload', 'tor@default.service'])

# success
subprocess.call(['/usr/bin/sudo',
                 '-u',
                 'amnesia',
                 '/usr/bin/notify-send',
                 '-i',
                 '/home/amnesia/Persistent/.securedrop/securedrop_icon.png',
                 'Updated torrc!',
                 'You can now connect to your SecureDrop\ndocument interface.'])
