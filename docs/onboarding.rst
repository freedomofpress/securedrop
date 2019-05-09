Onboard Journalists
===================

Congratulations! You've successfully installed SecureDrop.

At this point, the only person who has access to the system is the
admin. In order to grant access to journalists, you will need
to do some additional setup for each individual journalist.

In order to use SecureDrop, each journalist needs two things:

1. A *Journalist Tails USB*.

     The *Journalist Interface* is only accessible as an Authenticated Tor
     Hidden Service (ATHS). For ease of configuration and security, we
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

Once you're done, boot into the new Journalist Tails USB on the
*Journalist Workstation*. Enable persistence and set an admin
passphrase before continuing with the next section.


Set Up Automatic Access to the *Journalist Interface*
-----------------------------------------------------

Since the *Journalist Interface* is an ATHS, we need to set up the
*Journalist Workstation* to auto-configure Tor just as we did with the
*Admin Workstation*. The procedure is essentially identical, except the
SSH configuration will be skipped, since only admins need
to access the servers over SSH.

.. tip:: Copy the files ``app-journalist-aths`` and ``app-source-ths`` from
         the *Admin Workstation* via the Transfer Device. Place these files
         in ``~/Persistent/securedrop/install_files/ansible-base`` on the
         *Journalist Workstation*, and the ``./securedrop-admin tailsconfig``
         tool will automatically use them. Don't forget to securely delete
         these files from the *Transfer Device* when you're done, by
         right-clicking them in the file manager and selecting **Wipe**.

.. warning:: Do **not** copy the files ``app-ssh-aths`` and ``mon-ssh-aths``
             to the *Journalist Workstation*. Those files grant access via SSH,
             and only the *Admin Workstation* should have shell access to the
             servers.

.. warning:: The ``app-journalist-aths`` file contains a password for the
             authenticated hidden service used by the *Journalist Interface*,
             and should not be shared except through the onboarding process.

Since you need will the Tails setup scripts (``securedrop/tails_files``) that
you used to :doc:`Configure the *Admin Workstation* Post-Install
<configure_admin_workstation_post_install>`, clone (and verify) the SecureDrop
repository on the *Journalist Workstation*, just like you did for the Admin
Workstation. Refer to the docs for :ref:`cloning the SecureDrop
repository <Download the SecureDrop repository>`, then return here to
continue setting up the *Journalist Workstation*.

Once you've done this, use the ``securedrop-admin`` script to configure the
shortcuts for the Source and *Journalist Interfaces*: ::

  ./securedrop-admin setup
  ./securedrop-admin tailsconfig

If you did not copy over the ``app-source-ths`` and ``app-journalist-aths``
files from the *Admin Workstation*, the script will prompt for the information.
Make sure to type the information carefully, as any typos will break access
for the *Journalist Workstation*.

Once the script is finished, you should be able to access the
*Journalist Interface*. Open the Tor Browser and navigate to the .onion address for
the *Journalist Interface*. You should be able to connect, and will be
automatically taken to a login page.

Add an account on the *Journalist Interface*
--------------------------------------------

Finally, you need to add an account on the *Journalist Interface* so the journalist
can log in and access submissions. See the section on :ref:`Adding Users` in
the admin Guide.

Import GPG Keys for Journalists with Access to SecureDrop to the SVS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While working on a story, journalists may need to transfer some documents or
notes from the *Secure Viewing Station* to the journalist's work computer on
the corporate network. To do this, the journalist should re-encrypt them with
their own keys. If a journalist does not already have a personal GPG key,
they can follow the same steps above to create one. The journalist should
store the private key somewhere safe; the public key should be stored on the
*Secure Viewing Station*.

If the journalist does have a key, transfer their public key from wherever it
is located to the *Secure Viewing Station*, using the *Transfer Device*. Open
the file manager |Nautilus| and double-click on the public key to import it.

|Importing Journalist GPG Keys|

.. |Nautilus| image:: images/nautilus.png
.. |Importing Journalist GPG Keys| image:: images/install/importkey.png

Verify Journalist Setup
-----------------------

Once the journalist device and account have been provisioned, then the
admin should run through the following steps with *each journalist* to
verify the journalist is set up for SecureDrop.

The journalist should verify that they:

1. Have their own *Journalist Tails USB* that they have verified they are able
   to boot on the *Journalist Workstation*.

.. note:: It is important that they test on the same *Journalist Tails USB* and
   the same *Journalist Workstation* they will be using on a day to day basis.
   Issues may arise due to differences in USB drives or laptop models.

2. Verify they are able to decrypt the persistent volume on the *Journalist
   Tails USB*.

3. Ensure that they can connect to and login to the *Journalist Interface*.

4. Ensure that they have a *Data Transfer Device* with a saved passphrase.

5. Verify they have access to the *Secure Viewing Station* they will be using by
   plugging in the *SVS USB*, booting, and verifying they can decrypt the
   persistent volume.

.. note:: Again, it is important that they test on the same *SVS Tails USB* and
   the same *Secure Viewing Station* they will be using on a day to day basis.

6. Verify the *Submission Private Key* is present in the *Secure Viewing Station*
   persistent volume by clicking the clipboard icon |gpgApplet| in the top right
   corner of the Tails desktop and selecting “Manage Keys”. When clicking
   “GnuPG keys” the key should be present.

.. tip:: The journalist should have all the credentials used in this checklist
   saved in the KeePassX database stored in the persistent volume of the *Journalist
   Workstation*.

At this point, the journalist has verified they have the devices and credentials
they need and can proceed to a walkthrough of the entire SecureDrop workflow.

.. |gpgApplet| image:: images/gpgapplet.png
