.. include:: ../includes/trusty-warning.txt

Ubuntu 16.04 LTS (Xenial) -  Back Up, Install, Restore
======================================================

One way to upgrade your instance to Ubuntu 16.04 (Xenial) is to create a backup
of your existing Ubuntu 14.04 (Trusty) instance, install a new instance based on
Xenial, and restore the data from the backup to the Xenial-based installation.

You can follow this procedure on your existing hardware (causing significant
downtime), or you can install using redundant hardware and perform a cut-over
once you have validated that the new installation is working (minimizing
downtime).

.. note ::
  This procedure requires physical access to the servers and firewall
  to complete the installation. If you do not have physical access to the
  hardware, consider using the method documented in :doc:`xenial_upgrade_in_place`,
  which can be completed from the *Admin Workstation* over Tor.


Before you begin
----------------

Before you get started, make sure that you have completed the :doc:`preparatory
steps for the Xenial upgrade <xenial_prep>`. You will need physical access to
the servers and firewall, and you will need a monitor and keyboard to connect to
the servers during the OS installation.

If you are planning to install the Xenial instance on new hardware, make sure
that you have all the necessary hardware on hand and configured. This guide
assumes that you are either using the existing hardware firewall, or a new
firewall configured with the same settings as your existing one.

Although downtime should be minimal, you should coordinate the timing of the
upgrade with the people responsible for checking for submissions. If they have
ongoing conversations with sources, or are expecting submissions, it may be
necessary to reschedule the upgrade. Consider communicating the planned downtime
and the reason for it on your instance's *Landing Page*.

Step 1: Back up your instance
-----------------------------

Start up the *Admin Workstation* with persistence enabled and an administration
password set. Then, once you are connected to the Tor network, open a terminal
and run the following commands:

.. code:: sh

 cd ~/Persistent/securedrop
 ./securedrop-admin setup
 ./securedrop-admin backup

This will create a backup named ``sd-backup-<date>.tar.gz`` in the
``~/Persistent/securedrop/install_files/ansible-base`` directory. Make a note of
the exact name, as you'll need it later.

.. note:: 
 The backup files are not encrypted by default. If you copy them to a USB stick
 or other media you should ensure that the device uses encrypted storage, or
 that you encrypt the backup files themselves using a strong encryption method. 

You should also make a copy of the configuration files that allow the *Admin
Workstation* to connect to the hidden services on the *Application Server*. To
do so, run the following commands from the terminal:

.. code:: sh

  cd ~/Persistent/
  mkdir app_service
  cp securedrop/install_files/ansible-base/app-*ths app_service/
  cp securedrop/install_files/ansible-base/group_vars/all/site-specific app_service/

Once you have completed the backup process, you may shut down the *Admin
Workstation* and move to the next step: installing a Xenial-based instance.

.. include:: ../includes/backup-warning.txt

Step 2: Install Xenial
----------------------

Assuming that you are using your existing firewall, or that you've already set
up your new firewall following the instructions in :doc:`../network_firewall`,
the next step is to connect your candidate *Application* and *Monitor* servers
to it and install the Xenial base OS.

.. caution::
 If you're reusing your existing servers, their storage will be wiped by this
 step, so make sure your backups are available!

With the servers connected to the firewall, follow the instructions in
:doc:`../servers` to install Xenial, overwriting the existing Trusty
installation. You should use the same network settings and administrator shell
account name as for your previous installation.

.. note::

 If you do not have the network settings (including your server IP addresses) or
 shell username recorded, you'll find them listed in the
 ``~/Persistent/app_service/site-specific`` file on the *Admin Workstation*.

Step 3: Set up SSH access to the servers
----------------------------------------

Once you have installed Xenial on the servers, you'll need to configure
key-based SSH access to the servers from the *Admin Workstation*.

First, connect the *Admin Workstation* directly to the firewall via Ethernet,
and start up the *Admin Workstation* with persistence enabled and an
administration password set. You may need to update the network settings in
Tails to use the static IP that was set up during the firewall configuration for
the *Admin Workstation*.

Then, remove the previous instance's connection configuration from the *Admin
Workstation*, by opening a terminal and running the following commands:

.. code:: sh

 rm ~/.ssh/{config,known_hosts}
 rm ~/Persistent/securedrop/install_files/ansible-base/app-source-ths
 rm ~/Persistent/securedrop/install_files/ansible-base/app-*-aths
 rm ~/Persistent/securedrop/install_files/ansible-base/mon-*-aths

Next, copy the *Admin Workstation*'s SSH public key to the new servers. To do
so, you will need the IP addresses of the servers, and the username and password
of the administrator account created during the OS installation. The commands
below use the default values, but make sure to substitute your own:

.. code:: sh

 # copy key to app
 ssh-copy-id sdadmin@10.20.2.2

 # copy key to mon
 ssh-copy-id sdadmin@10.20.3.2

You will be prompted by both commands for the shell account password.

To confirm that key-based SSH access is working, run the following commands:

.. code:: sh

  ssh sdadmin@10.20.2.2 hostname
  ssh sdadmin@10.20.3.2 hostname

In both cases, the commands should return the hostname of the remote server,
without requiring a password.


Step 4: Install SecureDrop
--------------------------

Once you have set up SSH access, it's time to install SecureDrop. As most of the
application settings are preserved on the *Admin Workstation* from your previous
instance, this process will be simpler than your first installation.

First, you'll need make sure your *Admin Workstation*'s SecureDrop application
code is up-to-date and validated. From a terminal, run the following commands:

.. code:: sh

 cd ~/Persistent/securedrop
 git fetch --tags
 git tag -v 0.12.2

You should see ``Good signature from "SecureDrop Release Signing Key"`` in the
output of that last command, along with the fingerprint ``"2224 5C81 E3BA EB41
38B3 6061 310F 5612 00F4 AD77"``

.. caution::

 If you do not, signature verification has failed and you should not proceed
 with the installation. If this happens, please contact us at
 securedrop@freedom.press.

If the command above returns the expected value, you may proceed with the installation.

First, check out the release tag that you validated above:

.. code:: sh
 
 git checkout 0.12.2

Next, run the following command to set up the SecureDrop administration environment:

.. code:: sh

  ./securedrop-admin setup

This command may take several minutes to complete and may fail due to Tor
network timeouts. If it does fail, try running it again. If it fails repeatedly,
:ref:`contact us. <bir_contact_us>`

Next, step through the SecureDrop application settings to verify that their
values are correct. You should not need to change anything - run the following
command and press Enter when prompted with the current values:

.. code:: sh

 ./securedrop-admin sdconfig

If the configuration values are correct, you may proceed with the installation
using the following command:

.. code:: sh

 ./securedrop-admin install

This command will take several minutes to complete, and will reboot the
*Application* and *Monitor* servers as part of the process.

.. include:: ../includes/rerun-install-is-safe.txt

When the server installation completes successfully, you should set up the
*Admin Workstation* to connect to the new servers over Tor. To do so, run the
following command:

.. code:: sh

 ./securedrop-admin tailsconfig

This will update desktop shortcuts and SSH configuration files on the *Admin
Workstation*. Once it is complete, you may move on to the next step: restoring
the old instance configuration and data from the backup.

Step 5: Restore your instance data and configuration from backup
----------------------------------------------------------------

Before beginning the restore procedure, you should stop and start the Tails
network connection using the panel widget in the upper-right corner of the
screen. This will force the Tails Tor proxy to load the config changes made by
the ``./securedrop-admin tailsconfig`` command. Once Tor has reconnected, you're
ready to restore the backup.

To restore from backup, run the following commands in a terminal, substituting
the name of the backup file that you created earlier for
`sd-backup-<date>.tar.gz`:

.. code:: sh

 cd ~/Persistent/securedrop
 ./securedrop-admin restore sd-backup-<date>.tar.gz

Once the restore process is complete, the previous instance's *Application
Server* ATHS and THS files should be copied into place on the *Admin
Workstation*. From a terminal, run the following commands:

.. code:: sh

 cd ~/Persistent
 cp app_service/app*ths securedrop/install_files/ansible-base/

Finally, run the ``tailsconfig`` command again to update the *Admin
Workstation*'s SSH configuration and desktop shortcuts:

.. code:: sh

 cd ~/Persistent/securedrop
 ./securedrop-admin tailsconfig

Once the command completes, stop and restart the network connection again to
force the Tails Tor proxy to pick up on the configuration changes.

Step 6: Cut over to the new instance
------------------------------------

If you used your existing instance's hardware for the Xenial installation, your
new instance is now available, with unchanged Onion URLs. If you installed onto
new hardware, you should now power down your old instance hardware and reboot
your new instance's servers. Once the reboot is complete, move on to Step 7.

Step 7: Test the instance connectivity
--------------------------------------

Your Xenial-based instance should now be up and running, with the *Journalist*
and *Source* interfaces available under their original Onion URLs. To confirm
this, use the desktop shortcuts on the *Admin Workstation* to connect to each
interface, and log into the *Journalist Interface* using your existing
credentials. You should also verify SSH connectivity to the *Application* and
*Monitor* servers from a terminal, using the commands ``ssh app`` and ``ssh
mon`` respectively.

.. _bir_contact_us:

Contact us
----------

If you have questions or comments regarding this process, or if you
encounter any issues, you can always contact us by the following means:

- via our `Support Portal <https://support.freedom.press>`_, if you are a member
  (membership is approved on a case-by-case basis);
- via securedrop@freedom.press
  (`GPG encrypted <https://securedrop.org/sites/default/files/fpf-email.asc>`__)
  for sensitive security issues (please use judiciously);
- via our `community forums <https://forum.securedrop.org>`_.

If you encounter problems that are not security-sensitive, we also encourage you
to `file an issue <https://github.com/freedomofpress/securedrop/issues/new/>`_
in our public GitHub repository.

.. caution:: 

 If you include log snippets or error output in any communications via the 
 methods described above, make sure to first redact sensitive data, such as
 Onion URLs or authentication information.
