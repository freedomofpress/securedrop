Onboard Journalists
===================

Congratulations! You've successfully installed SecureDrop.

At this point, the only person who has access to the system is the
administrator. In order to grant access to journalists, you will need
to do some additional setup for each individual journalist.

In order to use SecureDrop, each journalist needs two things:

1. A *Journalist Tails USB*.

     The Journalist Interface is only accessible as an authenticated Tor
     Hidden Service (ATHS). For ease of configuration and security, we
     require journalists to set up a Tails USB with persistence that
     they are required to use to access the Journalist Interface.

2. Access to the *Secure Viewing Station*.

     The Journalist Interface allows journalists to download submissions
     from sources, but they are encrypted to the offline private key
     that is stored on the Secure Viewing Station Tails USB. In order
     for the journalist to decrypt and view submissions, they need
     access to a Secure Viewing Station.

Determine access protocol for the Secure Viewing Station
--------------------------------------------------------

Currently, SecureDrop only supports encrypting submissions to a single
public/private key pair - the *SecureDrop Submission Key*. As a
result, each journalist needs a way to access the Secure Viewing
Station with a Tails USB that includes the submission private key.

The access protocol for the Secure Viewing Station depends on the
structure and distribution of your organization. If your organization
is centralized and there are only a few journalists with access to
SecureDrop, they should be fine with sharing a single Secure Viewing
Station. On the other hand, if your organization is distributed, or if
you have a lot of journalists who wish to access SecureDrop
concurrently, you will need to provision multiple Secure Viewing
Stations.

.. todo:: Describe best practices for provisioning multiple Secure
          Viewing Stations.

Create a Journalist Tails USB
-------------------------------------------

Each journalist will need a Journalist Tails USB and a *Journalist
Workstation*, which is the computer they use to boot their Tails USB.

To create a Journalist Tails USB, just follow the same procedure you
used to create a Tails USB with persistence for the Admin Tails USB,
as documented in the :doc:`Tails Setup Guide <set_up_tails>`.

Once you're done, boot into the new Journalist Tails USB on the
Journalist Workstation. Enable persistence and set an administrator
password before continuing with the next section.

Set up automatic access to the Journalist Interface
-------------------------------------------------

Since the Journalist Interface is an ATHS, we need to set up the
Journalist Tails USB to auto-configure Tor just as we did with the
Admin Tails USB. The procedure is essentially identical, except the
SSH configuration will be skipped, since only Administrators need
to access the servers over SSH.

.. tip:: Copy the files ``app-journalist-aths`` and ``app-source-ths`` from
         the Admin Workstation via the Transfer Device. Place these files
         in ``~/Persistent/securedrop/install_files/ansible-base`` on the
         Journalist Workstation, and the ``install.sh`` script will
         automatically use them.

.. warning:: Do **not** copy the files ``app-ssh-aths`` and ``mon-ssh-aths``
             to the Journalist Workstation. Those files grant access via SSH,
             and only the Admin Workstation should have shell access to the
             servers.

Since you need will the Tails setup scripts (``securedrop/tails_files``) that
you used to :doc:`Configure the Admin Workstation Post-Install
<configure_admin_workstation_post_install>`, clone (and verify) the SecureDrop
repository on the Journalist Workstation, just like you did for the Admin
Workstation. Refer to the docs for :ref:`cloning the SecureDrop
repository <Download the SecureDrop repository>`, then return here to
continue setting up the Journalist Workstation.

Once you've done this, run the install script to configure the
shortcuts for the Source and Journalist Interfaces: ::

  cd ~/Persistent/securedrop/tails_files/
  sudo ./install.sh

If you did not copy over the ``app-source-ths`` and ``app-journalist-aths``
files from the Admin Workstation, the script will prompt for the information.
Make sure to type the information carefully, as any typos will break access
for the Journalist Workstation.

Once the ``install.sh`` script is finished, you should be able to access the
Journalist Interface. Open the Tor Browser and navigate to the .onion address for
the Journalist Interface. You should be able to connect, and will be
automatically taken to a login page.

Add an account on the Journalist Interface
----------------------------------------

Finally, you need to add an account on the Journalist Interface so the journalist
can log in and access submissions. See the section on :ref:`Adding Users` in
the Administrator Guide.
