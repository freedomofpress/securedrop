Onboard Journalists
===================

Congratulations! You've successfully installed SecureDrop.

At this point, the only person who has access to the system is the
admin. In order to grant access to journalists, you will need
to do some additional setup for each individual journalist.

In order to use SecureDrop, each journalist needs two things:

1. A *Journalist Tails USB*.

     The *Journalist Interface* is only accessible as an authenticated
     onion service. For ease of configuration and security, we
     require journalists to set up a Tails USB with persistence that
     they are required to use to access the *Journalist Interface*.

2. Access to the *Secure Viewing Station*.

     The *Journalist Interface* allows journalists to download submissions
     from sources, but they are encrypted to the offline private key
     that is stored on the *Secure Viewing Station* Tails USB. In order
     for the journalist to decrypt and view submissions, they need
     access to a *Secure Viewing Station*.

Determine Access Protocol for the *Secure Viewing Station*
----------------------------------------------------------

Currently, SecureDrop only supports encrypting submissions to a single
public/private key pair - the *Submission Key*. As a result, each journalist
needs a way to access the *Secure Viewing Station* with a Tails USB that
includes the *Submission Private Key*.

The access protocol for the *Secure Viewing Station* depends on the
structure and distribution of your organization. If your organization
is centralized and there are only a few journalists with access to
SecureDrop, they should be fine with sharing a single Secure Viewing
Station. On the other hand, if your organization is distributed, or if
you have a lot of journalists who wish to access SecureDrop
concurrently, you will need to provision multiple *Secure Viewing
Stations*.

Create a Journalist Tails USB
-----------------------------

Each journalist will need a Journalist Tails USB and a *Journalist
Workstation*, which is the computer they use to boot their Tails USB.

To create a *Journalist Interface* Tails USB, just follow the same procedure you
used to create a Tails USB with persistence for the *Admin Workstation*,
as documented in the :doc:`Tails Setup Guide <set_up_tails>`.

.. note::

   As with your *Admin Workstation*, you can use a fresh copy of the blank
   KeePassXC template in the repository to initialize the password database
   on the *Journalist Workstation*. You can safely edit this copy to remove
   sections or fields that are not relevant for the journalist you are
   onboarding. For example, the admin section of the password database should
   never be filled in on a *Journalist Workstation*.

Once you're done, boot into the new Journalist Tails USB on the
*Journalist Workstation*. Enable persistence and set an admin
passphrase before continuing with the next section.


Set Up Automatic Access to the *Journalist Interface*
-----------------------------------------------------

Since the *Journalist Interface* is an authenticated onion service, you must
set up the *Journalist Workstation* to auto-configure Tor, similarly to 
the *Admin Workstation*. The procedure is essentially identical, except the
SSH configuration will be skipped, since only admins need
to access the servers over SSH.

- First, boot into the *Admin Workstation*. If your instance has not been set up
  to use v3 onion services, copy the following v2 service files to a *Transfer Device*:

  .. code-block:: none
 
    ~/Persistent/securedrop/install_files/ansible_base/app-source-ths
    ~/Persistent/securedrop/install_files/ansible_base/app-journalist-aths

  If your instance was set up to use v3 services, copy the following files instead:

  .. code-block:: none

    ~/Persistent/securedrop/install_files/ansible_base/app-sourcev3-ths
    ~/Persistent/securedrop/install_files/ansible_base/app-journalist.auth_private

  Then, boot into the new *Journalist Workstation* USB.

.. warning:: Do **not** copy the ``app-ssh-aths``, ``mon-ssh-aths``,
             ``app-ssh.auth_private``, ``mon-ssh.auth_private``, or ``tor_v3_keys.json``
             files to the *Journalist Workstation*. Those files contain private
             keys and authentication information for SSH server access.
             Only the *Admin Workstation* should have shell access to the
             servers.

- Install the SecureDrop application code on the workstation's persistent volume,
  following the documentation for :ref:`cloning the SecureDrop
  repository <Download the SecureDrop repository>`.

- Copy the files from the *Transfer Device* to ``~/Persistent/securedrop/install_files/ansible-base``

- Open a terminal and run the following commands:

  .. code:: sh
 
    cd ~/Persistent/securedrop
    ./securedrop-admin setup
    ./securedrop-admin tailsconfig

  .. note:: The ``setup`` command may take several minutes, and may fail partway
            due to network issues. If so, run it again before proceeding.

- Once the ``tailsconfig`` command is complete, verify that the *Source* and
  *Journalist Interfaces* are accessible at their v2 addresses via the 
  SecureDrop desktop shortcuts.

- Securely wipe the files on the *Transfer Device*, by right-clicking them
  in the file manager and selecting **Wipe**.


.. warning:: The ``app-journalist-aths`` and ``app-journalist.auth_private`` 
             files contain secret authentication information for the
             authenticated onion service used by the *Journalist Interface*,
             and should not be shared except through the onboarding process.

Add an account on the *Journalist Interface*
--------------------------------------------

Finally, you need to add an account on the *Journalist Interface* so the journalist
can log in and access submissions. See the section on :ref:`Adding Users` in
the admin Guide.

Provision a personal *Transfer Device* and *Export Device*
----------------------------------------------------------
In small organizations, a team of journalists may want to share a single
*Transfer Device* and a single *Export Device*. In larger organizations, you may
want to provision a personal *Transfer Device* and *Export Device* for each
journalist who may need to copy files off the *Secure Viewing Station*. Please
see the :doc:`setup guide <set_up_transfer_and_export_device>` for more
information.

Verify Journalist Setup
-----------------------

Once the journalist device and account have been provisioned, then the
admin should run through the following steps with *each journalist* to
verify the journalist is set up for SecureDrop.

The journalist should verify that they:

1. Have their own *Journalist Workstation* USB drive that they are able to boot
   on the computer designated for this purpose (which can be their everyday
   laptop).

.. note::

   It is important that they test exactly on the computer they will be using
   as the *Journalist Workstation*, as there can be differences in Tails
   compatibility between different laptop models.

2. Verify they are able to decrypt the persistent volume on the *Journalist
   Workstation*.

3. Ensure that they can connect to and login to the *Journalist Interface*.

4. Ensure that they have a *Transfer Device*, and access to its passphrase.

5. Verify they have access to the *Secure Viewing Station* by plugging in the
   *Secure Viewing Station* USB drive into the air-gapped computer designated
   for this purpose, booting, and verifying they can decrypt the persistent
   volume.

.. note::

   It is especially important to only boot the *Secure Viewing Station* USB
   drive on the air-gapped computer designated for this purpose.

6. Verify the *Submission Private Key* is present in the *Secure Viewing Station*
   persistent volume by clicking the clipboard icon |gpgApplet| in the top right
   corner of the Tails desktop and selecting “Manage Keys”. When clicking
   “GnuPG keys” the key should be present.

.. tip:: The journalist should have all the credentials used in this checklist
   saved in the KeePassXC database stored in the persistent volume of the *Journalist
   Workstation*.

7. If you are using a printer, verify that they are able to print a document
   from the *Secure Viewing Station*. If you are using an *Export Device*,
   verify that they are able to unlock the encrypted volume.

At this point, the journalist has verified they have the devices and credentials
they need and can proceed to a walkthrough of the entire SecureDrop workflow.

.. |gpgApplet| image:: images/gpgapplet.png
