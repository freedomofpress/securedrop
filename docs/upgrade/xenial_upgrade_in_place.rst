Ubuntu 16.04 LTS (Xenial) - upgrading in place
==============================================

If some instance downtime during the Xenial upgrade is acceptable, or if no backup hardware is available to allow for the no-downtime backup->install->restore upgrade procedure, it is possible to upgrade your SecureDrop instance in place. The upgrade-in place procedure requires no additional hardware, and is described below. 


Communicating with users before the change
------------------------------------------

The process of upgrading in place will result in downtime for your instance. Our testing indicates that the upgrade may take up to 8 hours, assuming no issues. As a result, we recommend that you plan for 2 days work, during which the instance will be unavailable. You should also consider having a communications plan in place both for journalist and sources.

 - You should coordinate the timing of the upgrade with the people responsible for checking for submissions. If they have ongoing conversations with sources, or are expecting submissions, it may be necessary to reschedule the upgrade.
 - You should also consider communicating the downtime downtime and reason for it on your instance's landing page.
 

Preparatory steps
-----------------

 - take a backup of the instance using usual methods
 - make sure Admin Stick is updated to 0.12.0 (or later)
 - make sure that your instance is also upgraded to 0.12.0+ (ED: needed for changes in postints to iptables etc - probably best to check deployed deb versions via ssh commands)

Upgrade and validate the Monitor Server 
---------------------------------------

First, open a terminal by selecting **Applications > Favorites > Terminal**. Then connect to the Monitor Server with the command ``ssh mon``.

Before running the ``do-release-upgrade`` command, you must edit the ``/etc/update-manager/release-upgrades``, changing `Prompt=never` to `Prompt=lts`. ED - this won't be necessary when #4104 lands

The OS upgrade process for the Monitor Server will take from 30-60 minutes based on your server specifications and available bandwidth, and should not be interrupted once begun. To begin  the process, run the command below and then supply the answers listed below to the prompts that follow:


.. code:: sh

  sudo do-release-upgrade

.. note:: The prompt answers below have been tested on the recommended hardware for SecureDrop. If your instance uses non-standard hardware, you may be see different or additional prompts. In general, when responding to these prompts you should preserve existing configuration files whenever possible.
    
- Run ``sudo do-release-upgrade`` to start the upgrade process
- Press Enter after the "Some third party entries..." message
- Type 'y' and press Enter to continue after the "Installing the upgrade..." message
- Type 'y' and press Enter to continue after the "Fetching and installing..." message

.. note:: The ``do-release-upgrade`` script displays some dialogs using ``ncurses``, a library for rendering GUI elements in text-only displays. It may display incorrectly within your terminal window. To force a redraw, adjust the terminal's size to approximately 150 columns by 40 rows. If it still does not display correctly, make small adjustments to the terminal size to force successive redraws.
  
- Choose OK to close the *Postfix* information dialog
- Choose **No Configuration** and **OK** on the *General type of mail configuration* dialog
- Choose **Yes** on the *Configuring libssl.0.0:amd64* dialog - when you do so, the ``sshd`` and ``tor`` daemons will restart, breaking your connection to the Monitor Server
- Close the terminal window, open a new one, and reconnect with the command ``ssh mon``
- Choose **No** to overriding local changes, on the *PAM configuration* dialog
- Choose the default action (keep local version)  when prompted about ``blacklist.conf`` changes
- Choose **Keep the local version currently installed** on the `Configuring grub-efi-amd64` dialog
- Choose default (keep current version) when prompted about ``/etc/ssh/moduli`` changes
- Choose default (keep current version) when prompted about ``/etc/ssh/ssh_config`` changes
- Choose default (keep current version) when prompted about ``/etc/pam.d/sshd`` changes
- Choose **keep local version currently installed** and **OK** on the *Configuring unattended-upgrades* dialog
- Type 'y' and press Enter to remove obsolete packages when prompted
- Type 'y' and press Enter to restart the system and complete the update

The Monitor Server will now reboot - this may take several minutes. In order to reconnect via ``ssh mon``, you must stop and restart the Admin Workstation's Internet connection,  using the upper-righthand control in the Tails menubar. 

To confirm that the upgrade succeeded, connect from a terminal using the command ``ssh mon`` and run the following command to display the installed OS version:

.. code:: sh
  
  sudo lsb_release -a

Exit the SSH session to the Monitor server. Next, you will upgrade the Application Server using a a similar procedure

Upgrade and validate the Application Server
-------------------------------------------

First, open a terminal by selecting **Applications > Favorites > Terminal**. Then connect to the Application Server with the command ``ssh app``.

Before running the ``do-release-upgrade`` command, you must edit the ``/etc/update-manager/release-upgrades``, changing `Prompt=never` to `Prompt=lts`. ED - this won't be necessary when #4104 lands

The OS upgrade process for the Application Server will take from 30-60 minutes based on your server specifications and available bandwidth, and should not be interrupted once begun. To begin  the process, run the command below and then supply the answers listed below to the prompts that follow:


.. code:: sh

  sudo do-release-upgrade

.. note:: The prompt answers below have been tested on the recommended hardware for SecureDrop. If your instance uses non-standard hardware, you may be see different or additional prompts. In general, when responding to these prompts you should preserve existing configuration files whenever possible.
    
- Run ``sudo do-release-upgrade`` to start the upgrade process
- Press Enter after the "Some third party entries..." message
- Type 'y' and press Enter to continue after the "Installing the upgrade..." message
- Type 'y' and press Enter to continue after the "Fetching and installing..." message

.. note:: The ``do-release-upgrade`` script displays some dialogs using ``ncurses``, a library for rendering GUI elements in text-only displays. It may display incorrectly within your terminal window. To force a redraw, adjust the terminal's size to approximately 150 columns by 40 rows. If it still does not display correctly, make small adjustments to the terminal size to force successive redraws.
  
- Choose OK to close the *Postfix* information dialog
- Choose **No Configuration** and **OK** on the *General type of mail configuration* dialog
- Choose **Yes** on the *Configuring libssl.0.0:amd64* dialog - when you do so, the ``sshd`` and ``tor`` daemons will restart, breaking your connection to the Application Server
- Close the terminal window, open a new one, and reconnect with the command ``ssh app``
- Choose **No** to overriding local changes, on the *PAM configuration* dialog
- Choose the default action (keep local version)  when prompted about ``blacklist.conf`` changes
- Choose **Keep the local version currently installed** on the `Configuring grub-efi-amd64` dialog
- Choose default (keep current version) when prompted about ``/etc/ssh/moduli`` changes
- Choose default (keep current version) when prompted about ``/etc/ssh/ssh_config`` changes
- Choose default (keep current version) when prompted about ``/etc/pam.d/sshd`` changes
- Choose **keep local version currently installed** and **OK** on the *Configuring unattended-upgrades* dialog
- Type 'y' and press Enter to remove obsolete packages when prompted
- Type 'y' and press Enter to restart the system and complete the update

The Application Server will now reboot - this may take several minutes. In order to reconnect via ``ssh app``, you must stop and restart the Admin Workstation's Internet connection,  using the upper-righthand control in the Tails menubar. 

To confirm that the upgrade succeeded, connect from a terminal using the command ``ssh app`` and run the following command to display the installed OS version:

.. code:: sh
  
  sudo lsb_release -a

Disconnect the SSH session to the Application Server. You are now ready to move on to the next step: updating to the Xenial version of the application code and config using ``./securedrop-admin install``

Reinstall the SecureDrop application
------------------------------------

Open a new Terminal, and run the following commands to set up the SecureDrop admin environment:

.. code:: sh

  cd ~/Persistent/securedrop
  ./securedrop-admin setup

Next, verify that the SecureDrop configuration matches expected values, by stepping through the configuration using:

.. code:: sh

  ./securedrop-admin sdconfig

Finally, install the Xenial version of the server application code and config:

.. code:: sh

  ./securedrop-admin sdconfig
  
You will be prompted for the admin user's password on the servers. Type it in and press Enter.

Test the instance after upgrading
---------------------------------

[ TBD - either a bunch of shell commands that check installed versions and stuff like grsec and Apparmor, or a single script provided with the release to do basic server tests ]

[ Also a checklist for basic functionality - connectivity to the 4 services, and a run through the submission-to-decryption workflow ]

[ Anything else? ]

