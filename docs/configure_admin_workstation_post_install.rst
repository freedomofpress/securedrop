Configure the Admin Workstation Post-Install and Create Backups
===============================================================

.. _auto-connect ATHS:

Auto-connect to the Authenticated Onion Services
------------------------------------------------

The SecureDrop installation process adds multiple layers of authentication to
protect access to the most sensitive assets in the SecureDrop system:

#. The *Journalist Interface*, because it provides access to submissions (although
   they are encrypted to an offline key), and some metadata about sources and
   submissions.
#. SSH on the *Application Server*
#. SSH on the *Monitor Server*

The installation process blocks direct access to each of these assets, and sets
up `authenticated onion services`_ to provide authenticated access
instead. Authenticated onion services share the benefits of regular onion services,
but are only accessible to users who possess a shared secret
(``auth-cookie`` in the Tor documentation) that is generated during the onion
service setup process.

In order to access an authenticated onion service, you require its authentication
secret. SecureDrop includes a set of scripts to configure Tails access to the
authenticated onion services. In order to persist these changes across reboots,
persistence must be enabled in Tails.

To install the auto-connect configuration, start by navigating to the directory
with these scripts (``~/Persistent/securedrop/``), and run the install script:

.. code:: sh

    ./securedrop-admin tailsconfig

Type the Administration Password that you selected when starting Tails and hit
**Enter**. This script installs a persistent script that runs every time you
connect to a network in Tails, and automatically configures access to
the *Journalist Interface* and to the servers via SSH. The HidServAuth info is
collected from files in
``~/Persistent/securedrop/install_files/ansible-base`` and stored in
``~/Persistent/.securedrop/torrc_additions`` thereafter.

.. tip:: Copy the files ``app-journalist-aths`` and ``app-source-ths`` to
         the Transfer Device in preparation for setting up the Journalist
         Workstation. Then you can use the ``securedrop-admin`` tool to configure
         access for Journalists as well.

In addition, the script creates desktop and menu shortcuts for the Source
and *Journalist Interfaces*, directs Tails to install Ansible at the
beginning of every session, and sets up SSH host aliases for the servers.

The only thing you need to remember to do is enable
persistence when you boot the *Admin Workstation*. If you are
using the *Admin Workstation* and are unable to connect to any
of the authenticated onion services, restart Tails and make
sure to enable persistence.

.. _authenticated onion services: https://community.torproject.org/onion-services/advanced/client-auth/

Back Up the Workstations
------------------------

USB drives can wear out, get lost, or otherwise become corrupted, making it very important to be sure to keep current backups. Follow the :ref:`Backup the Workstations <backup_workstations>` document to create a backup of your *Secure Viewing Station*, *Admin Workstation*, and *Journalist Workstations* after you've completed the installation and post-installation steps.
