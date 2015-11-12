Configure the Admin Workstation Post-Install
============================================

.. _auto-connect ATHS:

Auto-connect to the Authenticated Tor Hidden Services
-----------------------------------------------------

The SecureDrop installation process adds multiple layers of authentication to 
protect access to the most sensitive assets in the SecureDrop system:

#. The Document Interface, because it provides access to submissions (although 
   they are encrypted to an offline key), and some metadata about sources and 
   submissions.
#. SSH on the Application Server
#. SSH on the Monitor Server

The installation process blocks direct access to each of these assets, and sets 
up `Authenticated Tor Hidden Services`_ (ATHS) to provide authenticated access 
instead. Authenticated Tor Hidden Services share the benefits of Tor Hidden 
Services, but are only accessible to users who possess a shared secret 
(``auth-cookie`` in the Tor documentation) that is generated during the hidden 
service setup process.

In order to access an ATHS, you need to add one or more "auth-cookie" values 
to your Tor configuration file (``torrc``) and restart Tor. Doing this manually 
is annoying and error-prone, so SecureDrop includes a set of scripts in 
``securedrop/tails_files`` that can set up a Tails instance to automatically 
configure Tor to access a set of ATHS. In order to persist these changes across 
reboots, the Tails instance must have persistence enabled (specifically, the 
"dotfiles persistence").

To install the auto-connect configuration, start by navigating to the directory 
with these scripts, and run the install script:

.. code:: sh

    cd ~/Persistent/securedrop/tails_files/
    sudo ./install.sh

Type the Administration Password that you selected when starting Tails and hit 
enter. The install script will download some additional software, which may 
take a few minutes.

This script installs a Network Manager hook that runs every time you connect to 
Tor. It automatically adds the HidServAuth values from ``torrc_additions`` to 
the ``torrc`` and restarts Tor.

In addition, it creates desktop and main menu shortcuts for both interfaces, 
updates your Ansible inventory file to install playbooks over Tor in the 
future, directs Tails to install Ansible at the beginning of every session, and
sets up SSH host aliases for the servers.

.. note:: The only thing you need to remember to do is enable
          persistence when you boot the Admin Workstation. If you are
          using the Admin Workstation and are unable to connect to any
          of the authenticated hidden services, restart Tails and make
          sure to enable persistence.

.. _Authenticated Tor Hidden Services: https://www.torproject.org/docs/tor-manual.html.en#HiddenServiceAuthorizeClient

.. _SSH Host Aliases:

SSH Host Aliases
----------------

The installation script in ``tails_files`` also sets up SSH host aliases for the 
admin. These can be found in ``~/.ssh/config``.

You can simply use ``ssh app`` and ``ssh mon`` to connect to each server. This 
configuration will be persisted across reboots thanks to Tails' SSH client 
persistence.

Set up two-factor authentication for the Admin
----------------------------------------------

.. todo:: Do we still want to recommend/require this? Should it be
          optional?

As part of the SecureDrop installation process, you will need to set up 
two-factor authentication on the App Server and Monitor Server using the Google 
Authenticator mobile app.

After your torrc has been updated with the HidServAuth values, connect to the 
App Server using ``ssh`` and run ``google-authenticator``. Follow the 
instructions in :doc:`our Google Authenticator guide <google_authenticator>` to 
set up the app on your Android or iOS device.

To disconnect enter the command ``exit``. Now do the same thing on the Monitor 
Server. You'll end up with an account for each server in the Google 
Authenticator app that generates two-factor codes needed for logging in.
