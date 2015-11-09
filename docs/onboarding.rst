Onboard Journalists
===================

Congratulations! You've successfully installed SecureDrop.

At this point, the only person who has access to the system is the
administrator. In order to grant access to journalists, you will need
to do some additional setup for each individual journalist.

In order to use SecureDrop, each journalist needs two things:

1. A *Journalist Tails USB*.

     The Document Interface is only accessible as an authenticated Tor
     Hidden Service (ATHS). For ease of configuration and security, we
     require journalists to set up a Tails USB with persistence that
     they are required to use to access the Document Interface.

2. Access to the *Secure Viewing Station*.

     The Document Interface allows journalists to download submissions
     from sources, but they are encrypted to the offline private key
     that is stored on the Secure Viewing Station Tails USB. In order
     for the journalist to decrypt and view submissions, they need
     access to a Secure Viewing Station.

Determine access protocol for the Secure Viewing Station
--------------------------------------------------------

Currently, SecureDrop only supports encrypting submissions to a single
public/private key pair - the *SecureDrop Application GPG Key*. As a
result, each journalist needs a way to access the Secure Viewing
Station with a Tails USB that includes the application private key.

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

Set up automatic access to the Document Interface
-------------------------------------------------

Since the Document Interface is an ATHS, we need to set up the
Journalist Tails USB to auto-configure Tor just as we did with the
Admin Tails USB. The procedure is essentially identical, only instead
of configuring all 3 of the configured services
(``app-document-aths``, ``app-ssh-aths``, and ``mon-ssh-aths``), you
only configure it to connect to ``app-document-aths`` since only
Administrators need to access the servers over SSH.

To get started, you should copy the ``HidServAuth`` value for the
Document Interface ATHS from the Admin Workstation to the Journalist
Workstation. The easiest way to do this is to copy the
``app-document-aths`` and ``app-source-ths`` files from the Admin Workstation 
to the
Journalist Workstation with the Data Transfer Device.

Now you need the Tails setup scripts (``securedrop/tails_files``) that
you used to :doc:`Configure the Admin Workstation Post-Install
<configure_admin_workstation_post_install>`. The easiest way to do
this is to clone (and verify) the SecureDrop repository on the
journalist workstation, just like you did for the Admin
Workstation. Refer to the docs for :ref:`cloning the SecureDrop
repository <Download the SecureDrop repository>`, then return here to
continue setting up the Journalist Workstation.

Once you've done this, you should set up auto-connect and shortcuts for the 
Document
Interface ATHS the same way you did on the Admin Workstation. Follow
:ref:`the same docs <auto-connect ATHS>`, except on the Journalist
Workstation, you should enter the lines from ``app-document-aths``
and ``app-source-ths`` when prompted to by the ``install.sh`` script. Only the 
Admin Workstation should have the ``HidServAuth`` lines from ``app-ssh-aths`` 
and ``mon-ssh-aths``.

Once the ``install.sh`` script is finished, you should be able to access the
Document Interface. Open the Tor Browser and navigate to the .onion address for
the Document Interface. You should be able to connect, and will be
automatically taken to a login page.

Add an account on the Document Interface
----------------------------------------

Finally, you need to add an account on the Document Interface so the journalist
can log in and access submissions. See the section on :ref:`Adding Users` in
the Administrator Guide.
