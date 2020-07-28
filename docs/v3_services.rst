SecureDrop V3 Onion Services
============================
Tor onion services provide anonymous inbound connections to websites and other
servers exclusively over the Tor network. For example, SecureDrop uses onion services
for the *Journalist* and *Source Interface* websites, as well as for
adminstrative access to the servers in SSH-over-Tor mode.

SecureDrop currently supports both the older v2 version of the onion services
protocol, and the current version, v3. The current version provides stronger
cryptographic primitives than v2 onion services, and includes redesigned
protocols that guard against service information leaks on the Tor network.

Because of these important improvements, the Tor project is
`deprecating support for v2 onion services <https://blog.torproject.org/v2-deprecation-timeline>`__.
SecureDrop will remove support for v2 onion services as part of its 2.0.0
release, planned for **February 2021**. If you are currently using v2 onion services,
they will become unreachable at that point.

The unique identifier in v3 onion addresses is 56 characters long - for example:

.. code-block:: none

  http://vww6ybal4bd7szmgncyruucpgfkqahzddi37ktceo3ah7ngmcopnpyyd.onion/

This makes them easily distinguishable from 16-character v2 onion addresses,
such as:

.. code-block:: none

  http://secrdrop5wyphb5x.onion/

.. important::

   If you are currently advertising a 16-character v2 address like the above
   to your sources, it will become unreachable in February 2021. You must
   update to v3 onion services before then.

   There is no downgrade path from v3 to v2 using the ``securedrop-admin``
   tool. We recommend that you follow the v2+v3 migration path below, and test v3
   functionality thoroughly before :ref:`disabling v2 onion services <disable_v2>`.

Migrating from v2 to v3 only or v2+v3
-------------------------------------

Preparing for the migration
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Before starting the migration process, you should decide whether to move
straight to v3 only, or move to v2+v3 temporarily. As the URLs of your onion
services will change with the move to v3, moving to v2+v3 first will allow
you to minimize the impact of the migration on sources and journalists.

URL changes will affect the following:

- The *Source Interface* address will change - once the migration is complete,
  you will need to update your landing page and other resources that reference
  the address, such as your SecureDrop directory entry.
- *Journalist* and *Admin Workstations* will need to be updated to use the v3
  addresses of the *Journalist* and *Source Interface*, and the SSH proxy
  services if your instance is using SSH over Tor.
- If your instance uses HTTPS, you will need to provision a new certificate for
  the v3 *Source Interface* address - this will need to be done `after` the new
  address has been generated.

.. note:: If your certificate provisioning process requires validation of the
          new v3 domain, you may not be able to complete the v3 migration process
          without first disabling HTTPS for v2. If your instance currently uses
          HTTPS with an EV certificate, please contact us via the `SecureDrop
          support portal`_ or via email to securedrop@freedom.press
          before proceeding with the migration. Please use `our GPG key`_ for
          any email communication.

.. _SecureDrop Support Portal: https://securedrop-support.readthedocs.io/en/latest/
.. _our GPG key: https://securedrop.org/sites/default/files/fpf-email.asc

Before proceeding with the migration, you should also back up the instance and
*Admin Workstation* USB - for more information, see the following instructions:

- :doc:`Back up the instance <backup_and_restore>`.
- :doc:`Back up the Admin Workstation <backup_workstations>`.


Enabling v3 onion services
^^^^^^^^^^^^^^^^^^^^^^^^^^
To enable v3 onion services, you will need to run the installation playbook,
via the ``./securedrop-admin install`` command, and then update the *Admin
Workstation* with ``./securedrop-admin tailsconfig``.

- First, boot into the *Admin Workstation* with the persistent volume unlocked
  and an admin password set.
- Next, open a terminal via **Applications ▸ System Tools ▸ Terminal** and change
  the working directory to the Securedrop application directory:

  .. code:: sh

    cd ~/Persistent/securedrop

- Verify that SecureDrop version 1.0.0 or greater is available or installed on
  your instance with the command:

  .. code:: sh

    ssh app apt-cache policy securedrop-app-code

  Version 1.0.0 should be listed as installed or as an installation candidate.
- Verify that the *Admin Workstation*'s SecureDrop code is on 1.0.0 or greater,
  using the GUI updater or the command:

  .. code:: sh

    ./securedrop-admin update

- After updating the latest SecureDrop version, use the following command to
  update ``securedrop-admin``'s dependencies:

  .. code:: sh

    ./securedrop-admin setup

- Next, enable v3 onion services (and optionally disable v2 services) using:

  .. code:: sh

    ./securedrop-admin sdconfig

  This command will step through the current instance configuration. None of the
  current settings should be changed. When prompted to enable v2 and v3
  services, you should choose either ``yes`` to both to use v2 and v3
  concurrently, or ``no`` to v2 and ``yes`` to v3 to migrate to v3 only.

- Once the configuration has been updated, run the installation playbook using
  the command:

  .. code:: sh

    ./securedrop-admin install

  This will enable v3 onion services on the *Application* and *Monitor Servers*.

- When the installation playbook run is complete, update the *Admin Workstation*
  to use v3 onion services using the command:

  .. code:: sh

    ./securedrop-admin tailsconfig

- Next, verify connectivity between the *Admin Workstation* and the SecureDrop
  instance as follows:

  - Use the Source desktop shortcut to connect to the *Source Interface* and
    verify that the new 56-character address is present in the Tor Browser
    address bar.
  - Use the Journalist desktop shortcut to connect to the *Journalist Interface*
    and verify that the new 56-character address is present in the Tor Browser
    address bar.
  - Use the commands ``ssh app`` and ``ssh mon`` in a terminal to verify
    SSH access to the *Application* and *Monitor Servers*.

- Finally, back up the instance and *Admin Workstation* USB.

(Optional) enabling HTTPS
^^^^^^^^^^^^^^^^^^^^^^^^^
If your instance serves the *Source Interface* over HTTPS, and you plan to
continue using HTTPS with v3 onion services, you'll need to provision a
new certificate for the new v3 address.

You'll find the new *Source Interface* address in the file:

.. code-block:: none

  ~/Persistent/securedrop/install_files/ansible-base/app-sourcev3-ths

Follow the instructions in :doc:`HTTPS on the Source Interface <https_source_interface>`
to provision and install the new certificate.


Updating Workstation USBs
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you chose to keep v2 enabled, *Admin* and *Journalist Workstations* that have
not yet been updated will still be able to connect to the v2 onion services. Even
so, you should update all workstations to use v3 services as soon as possible.

Journalist Workstation:
~~~~~~~~~~~~~~~~~~~~~~~

 - In the *Admin Workstation* used to enable v3 onion services, copy the
   following files to an encrypted *Transfer Device*:

   .. code-block:: none

     ~/Persistent/securedrop/install_files/ansible-base/app-sourcev3-ths
     ~/Persistent/securedrop/install_files/ansible-base/app-journalist.auth_private

 - Then, boot into the *Journalist Workstation* to be updated, with the persistent
   volume unlocked and an admin password set.
 - Next, open a terminal via **Applications ▸ System Tools ▸ Terminal** and change
   the working directory to the Securedrop application directory:

   .. code:: sh

     cd ~/Persistent/securedrop


 - Ensure that the SecureDrop application code has been updated to the latest version,
   using either the GUI updater or the ``./securedrop-admin update`` command.

 - Insert the *Transfer Device*.
   Copy the ``app-sourcev3-ths`` and ``app-journalist.auth_private`` files from
   the *Transfer Device* to ``~/Persistent/securedrop/install_files/ansible-base``.

 - Open a terminal and run ``./securedrop-admin tailsconfig`` to update the
   SecureDrop desktop shortcuts.

 - Verify that the new 56-character addresses are in use by visiting the *Source*
   and *Journalist Interfaces* via the SecureDrop desktop shortcuts.

 - Securely wipe the files on the *Transfer Device*, by right-clicking them
   in the file manager and selecting **Wipe**.

Admin Workstation:
~~~~~~~~~~~~~~~~~~

 - In the *Admin Workstation* used to enable v3 onion services, copy the
   following files to an encrypted *Transfer Device*:

   .. code-block:: none

     ~/Persistent/securedrop/install_files/ansible-base/app-sourcev3-ths
     ~/Persistent/securedrop/install_files/ansible-base/app-journalist.auth_private
     ~/Persistent/securedrop/install_files/ansible-base/tor_v3_keys.json
     ~/Persistent/securedrop/install_files/ansible-base/group_vars/all/site-specific

   If your instance uses SSH over Tor, also copy the following files:

   .. code-block:: none

     ~/Persistent/securedrop/install_files/ansible-base/app-ssh.auth_private
     ~/Persistent/securedrop/install_files/ansible-base/mon-ssh.auth_private

 - Then, boot into the *Admin Workstation* to be updated, with the persistent
   volume unlocked and an admin password set.
 - Next, open a terminal via **Applications ▸ System Tools ▸ Terminal** and change
   the working directory to the Securedrop application directory:

   .. code:: sh

     cd ~/Persistent/securedrop

 - Ensure that the SecureDrop application code has been updated to the latest version,
   using either the GUI updater or the ``./securedrop-admin update`` command.

 - Insert the *Transfer Device*.
   Copy the ``app-sourcev3-ths``, ``*.auth_private``, and ``tor_v3_keys.json`` files from
   the *Transfer Device* to ``~/Persistent/securedrop/install_files/ansible-base``.

 - Copy the ``site-specific`` file from the *Transfer Device* to
   ``~/Persistent/securedrop/install_files/ansible-base/group_vars/all``.

 - Open a terminal and run ``./securedrop-admin tailsconfig`` to update the
   SecureDrop desktop shortcuts.

 - Verify that the new 56-character addresses are in use by visiting the *Source*
   and *Journalist Interfaces* via the SecureDrop desktop shortcuts.

 - Verify that ``~/.ssh/config`` contains the new 56-character addresses for the
   ``app`` and ``mon`` host entries, and that the *Application* and *Monitor
   Servers* are accessible via ``ssh app`` and ``ssh mon`` respectively.

 - Securely wipe the files on the *Transfer Device*, by right-clicking them
   in the file manager and selecting **Wipe**.


Updating Source Interface references
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In order for sources to find and use the new v3 *Source Interface*, you'll
need to update your landing page. If your instance details are listed
anywhere else (for example, in the SecureDrop directory), you should update
those listings too.

You'll find the new *Source Interface* address in the file:

.. code-block:: none

  ~/Persistent/securedrop/install_files/ansible-base/app-sourcev3-ths


.. _disable_v2:

Disabling v2 onion services
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Once you've successfully enabled v3 onion services, and updated your workstations,
you should disable v2 onion services altogether.

First, it's recommended that you coordinate with the journalists using the
instance to ensure that any ongoing source conversations are uninterrupted. They
can use SecureDrop's reply feature to give active sources advance notice of
the address change.

When you're ready, follow the steps below to transition to v3 services only:

- First, boot into the *Admin Workstation* with the persistent volume unlocked
  and an admin password set.

- Open a terminal and change the working directory to the SecureDrop application
  directory with the command:

  .. code:: sh

    cd ~/Persistent/securedrop


- Next, update the application configuration using the command:

  .. code:: sh

    ./securedrop-admin sdconfig

  This command will step through the current instance configuration. When prompted
  you should type ``no`` for v2 services and ``yes`` for v3 services to migrate to
  v3 only. No other settings should be modified.

- Once the configuration has been updated, run the installation playbook using
  the command:

  .. code:: sh

    ./securedrop-admin install

  This will disable v2 onion services on the *Application* and *Monitor Servers*.

- When the installation playbook run is complete, update the *Admin Workstation*
  to use v3 onion services only using the command:

  .. code:: sh

    ./securedrop-admin tailsconfig

- Next, verify connectivity between the *Admin Workstation* and the SecureDrop
  instance, checking the desktop shortcuts and SSH access.

- Then back up the instance and *Admin Workstation* USB.

- Finally, update your other *Admin Workstations*: from a terminal, run:

  .. code:: sh

    ./securedrop-admin sdconfig   # choose "no" for v2, "yes" for v3
    ./securedrop-admin tailsconfig
