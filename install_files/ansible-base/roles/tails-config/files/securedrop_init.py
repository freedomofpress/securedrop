#!/usr/bin/python

import grp
import os
import pwd
import sys
import subprocess


# check for root
if os.geteuid() != 0:
    sys.exit('You need to run this as root')

# paths
path_torrc_additions = '/home/amnesia/Persistent/.securedrop/torrc_additions'
path_torrc_backup = '/etc/tor/torrc.bak'
path_torrc = '/etc/tor/torrc'
path_desktop = '/home/amnesia/Desktop/'
path_persistent_desktop = '/lib/live/mount/persistence/TailsData_unlocked/dotfiles/Desktop/'

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
try:
    subprocess.check_call(['systemctl', 'reload', 'tor@default.service'])
except subprocess.CalledProcessError:
    sys.exit('Error reloading Tor')

# Turn off "automatic-decompression" in Nautilus to ensure the original
# submission filename is restored (see
# https://github.com/freedomofpress/securedrop/issues/1862#issuecomment-311519750).
subprocess.call(['/usr/bin/dconf', 'write',
                 '/org/gnome/nautilus/preferences/automatic-decompression',
                 'false'])

# Set journalist.desktop and source.desktop links as trusted with Nautilus (see
# https://github.com/freedomofpress/securedrop/issues/2586)
# set euid and env variables to amnesia user
amnesia_gid = grp.getgrnam('amnesia').gr_gid
amnesia_uid = pwd.getpwnam('amnesia').pw_uid
os.setresgid(amnesia_gid, amnesia_gid, -1)
os.setresuid(amnesia_uid, amnesia_uid, -1)
env = os.environ.copy()
env['XDG_RUNTIME_DIR'] = '/run/user/{}'.format(amnesia_uid)
env['XDG_DATA_DIR'] = '/usr/share/gnome:/usr/local/share/:/usr/share/'
env['HOME'] = '/home/amnesia'
env['LOGNAME'] = 'amnesia'
env['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=/run/user/{}/bus'.format(amnesia_uid)

# remove existing shortcut, recreate symlink and change metadata attribute to trust .desktop
for shortcut in ['source.desktop', 'journalist.desktop']:
    subprocess.call(['rm', path_desktop + shortcut], env=env)
    subprocess.call(['ln', '-s', path_persistent_desktop + shortcut, path_desktop + shortcut], env=env)
    subprocess.call(['gio', 'set', path_desktop + shortcut, 'metadata::trusted', 'yes'], env=env)

# reacquire uid0 and notify the user
os.setresuid(0,0,-1)
os.setresgid(0,0,-1)
subprocess.call(['tails-notify-user',
                 'SecureDrop successfully auto-configured!',
                 'You can now access the Journalist Interface.\nIf you are an admin, you can now SSH to the servers.'])
