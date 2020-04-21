#!/usr/bin/python3

import grp
import os
import io
import pwd
import sys
import subprocess

from shutil import copyfile


# check for root
if os.geteuid() != 0:
    sys.exit('You need to run this as root')

# paths
path_torrc_additions = '/home/amnesia/Persistent/.securedrop/torrc_additions'
path_torrc_backup = '/etc/tor/torrc.bak'
path_torrc = '/etc/tor/torrc'
path_desktop = '/home/amnesia/Desktop/'
path_persistent_desktop = '/lib/live/mount/persistence/TailsData_unlocked/dotfiles/Desktop/'  # noqa: E501
path_securedrop_root = '/home/amnesia/Persistent/securedrop'
path_securedrop_admin_venv = os.path.join(path_securedrop_root,
                                          'admin/.venv3/bin/python')
path_securedrop_admin_init = os.path.join(path_securedrop_root,
                                          'admin/securedrop_admin/__init__.py')
path_gui_updater = os.path.join(path_securedrop_root,
                                'journalist_gui/SecureDropUpdater')

paths_v3_authfiles = {
        "app-journalist": os.path.join(path_securedrop_root,
                                       'install_files/ansible-base/app-journalist.auth_private'),
        "app-ssh": os.path.join(path_securedrop_root,
                                'install_files/ansible-base/app-ssh.auth_private'),
        "mon-ssh": os.path.join(path_securedrop_root,
                                'install_files/ansible-base/mon-ssh.auth_private')
}
path_onion_auth_dir = '/var/lib/tor/onion_auth'

# load torrc_additions
if os.path.isfile(path_torrc_additions):
    with io.open(path_torrc_additions) as f:
        torrc_additions = f.read()
else:
    sys.exit('Error opening {0} for reading'.format(path_torrc_additions))

# load torrc
if os.path.isfile(path_torrc_backup):
    with io.open(path_torrc_backup) as f:
        torrc = f.read()
else:
    if os.path.isfile(path_torrc):
        with io.open(path_torrc) as f:
            torrc = f.read()
    else:
        sys.exit('Error opening {0} for reading'.format(path_torrc))

    # save a backup
    with io.open(path_torrc_backup, 'w') as f:
        f.write(torrc)

# append the additions
with io.open(path_torrc, 'w') as f:
    f.write(torrc + torrc_additions)

# check for v3 aths files
v3_authfiles_present = False
for f in paths_v3_authfiles.values():
    if os.path.isfile(f):
        v3_authfiles_present = True

# if there are v3 authfiles, make dir and copy them into place
debian_tor_uid = pwd.getpwnam("debian-tor").pw_uid
debian_tor_gid = grp.getgrnam("debian-tor").gr_gid

if not os.path.isdir(path_onion_auth_dir):
    os.mkdir(path_onion_auth_dir)

os.chmod(path_onion_auth_dir, 0o700)
os.chown(path_onion_auth_dir, debian_tor_uid, debian_tor_gid)

for key, f in paths_v3_authfiles.items():
    if os.path.isfile(f):
        filename = os.path.basename(f)
        new_f = os.path.join(path_onion_auth_dir, filename)
        copyfile(f, new_f)
        os.chmod(new_f, 0o400)
        os.chown(new_f, debian_tor_uid, debian_tor_gid)

# restart tor
try:
    subprocess.check_call(['systemctl', 'restart', 'tor@default.service'])
except subprocess.CalledProcessError:
    sys.exit('Error restarting Tor')

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
env['XDG_CURRENT_DESKTOP'] = 'GNOME'
env['DESKTOP_SESSION'] = 'default'
env['DISPLAY'] = ':1'
env['XDG_RUNTIME_DIR'] = '/run/user/{}'.format(amnesia_uid)
env['XDG_DATA_DIR'] = '/usr/share/gnome:/usr/local/share/:/usr/share/'
env['HOME'] = '/home/amnesia'
env['LOGNAME'] = 'amnesia'
env['DBUS_SESSION_BUS_ADDRESS'] = 'unix:path=/run/user/{}/bus'.format(
        amnesia_uid)

# remove existing shortcut, recreate symlink and change metadata attribute
# to trust .desktop
for shortcut in ['source.desktop', 'journalist.desktop']:
    subprocess.call(['rm', path_desktop + shortcut], env=env)
    subprocess.call(['ln', '-s', path_persistent_desktop + shortcut,
                     path_desktop + shortcut], env=env)
    subprocess.call(['gio', 'set', path_desktop + shortcut,
                     'metadata::trusted', 'true'], env=env)

# in Tails 4, reload gnome-shell desktop icons extension to update with changes above
cmd = ["lsb_release", "--id", "--short"]
p = subprocess.check_output(cmd)
distro_id = p.rstrip()
if distro_id == 'Debian' and os.uname()[1] == 'amnesia':
    subprocess.call(['gnome-shell-extension-tool', '-r', 'desktop-icons@csoriano'], env=env)

# reacquire uid0 and notify the user
os.setresuid(0, 0, -1)
os.setresgid(0, 0, -1)
success_message = 'You can now access the Journalist Interface.\nIf you are an admin, you can now SSH to the servers.'  # noqa: E501
subprocess.call(['tails-notify-user',
                 'SecureDrop successfully auto-configured!',
                 success_message])

# As the amnesia user, check for SecureDrop workstation updates.
os.setresgid(amnesia_gid, amnesia_gid, -1)
os.setresuid(amnesia_uid, amnesia_uid, -1)
output = subprocess.check_output([path_securedrop_admin_venv,
                                  path_securedrop_admin_init,
                                  '--root', path_securedrop_root,
                                  'check_for_updates'], env=env)

flag_location = "/home/amnesia/Persistent/.securedrop/securedrop_update.flag"
if b'Update needed' in output or os.path.exists(flag_location):
    # Start the SecureDrop updater GUI.
    subprocess.Popen(['python3', path_gui_updater], env=env)
