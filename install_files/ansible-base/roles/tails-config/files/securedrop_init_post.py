#!/usr/bin/python3

import grp
import os
import pwd
import sys
import subprocess


# check for root
if os.geteuid() != 0:
    sys.exit('You need to run this as root')

# paths
path_persistent_desktop = '/lib/live/mount/persistence/TailsData_unlocked/dotfiles/Desktop/'  # noqa: E501
path_securedrop_root = '/home/amnesia/Persistent/securedrop'
path_gui_updater = os.path.join(path_securedrop_root,
                                'journalist_gui/SecureDropUpdater')
path_securedrop_admin_venv = os.path.join(path_securedrop_root,
                                          'admin/.venv3/bin/python')
path_securedrop_admin_init = os.path.join(path_securedrop_root,
                                          'admin/securedrop_admin/__init__.py')

# notify the user
success_message = 'You can now access the Journalist Interface.\nIf you are an admin, you can now SSH to the servers.'  # noqa: E501
subprocess.call(['tails-notify-user',
                 'SecureDrop successfully auto-configured!',
                 success_message])

# As the amnesia user, check for SecureDrop workstation updates.
amnesia_gid = grp.getgrnam('amnesia').gr_gid
amnesia_uid = pwd.getpwnam('amnesia').pw_uid
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
