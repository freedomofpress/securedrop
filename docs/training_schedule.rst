SecureDrop On-Site Training Schedule
====================================

This is a high level schedule for what happens for the 2 days during an
on-site install.

Day 1: Preparation and Install
------------------------------

Setup and Introductions
~~~~~~~~~~~~~~~~~~~~~~~

Time: 30min

Participants: all

Required: projector, WiFi access, pre-configured demo SecureDrop
instance and 2 laptops to act as the Journalist Workstation and *SVS*

-  The demo instance has multiple sources to try and give a feel of what
   it will look like at 2 weeks past being public with sources in
   different states of the reply process

Overview of SecureDrop
~~~~~~~~~~~~~~~~~~~~~~

Time: 2 hours

Participants: journalists, editors, SecureDrop admins, OSSEC alert
recipients and anyone else interested

-  Go over the SecureDrop `FAQs <https://securedrop.org/faq>`__
-  Go over the SecureDrop :ref:`environment diagrams <securedrop_architecture_diagram>`
-  Importance of the *Landing Page* security and Twitter feedback
-  Demo the source submission process
-  Demo the journalist's processes for checking the *Journalist Interface*
-  Demo the journalist's processes for replies
-  Demo working with submissions on the *SVS*
-  Discuss scrubbing submitted documents prior to publication
-  Options for distributing with other news organizations
-  Show example of an OSSEC alert, briefly cover what it does
-  Show example of 'is it up?' Nagios monitoring alerts for Source
   Interface
-  Explain why the *Journalist Interface* does not have 'is it up?'
   monitoring
-  Discuss vanity onion URLs with
   `Shallot <https://github.com/katmagic/Shallot>`__ and
   `Scallion <https://github.com/lachesis/scallion>`__
-  How to brand the *Source Interface* and *Journalist Interface*
-  Physical security of servers and *SVS*
-  How to securely publicize the organization's Source Interface Tor URL
-  Distribute important info:

   -  Third-party security mailing lists to subscribe to
   -  https://freedom.press/about/staff
   -  https://securedrop.org
   -  https://docs.securedrop.org
   -  :doc:`Hardware for SecureDrop <hardware>`
   -  :ref:`Deployment` guidelines
   -  :doc:`Source Best Practice Guide <source>`
   -  :doc:`Journalist Best Practice Guide <journalist>`
   -  :doc:`Admin Best Practice Guide <admin>`
-  Answering the client vs. server side crypto debate
-  Link to security audits

Questions
~~~~~~~~~

Time: 30 min

Installing SecureDrop
~~~~~~~~~~~~~~~~~~~~~

Time: 6 hours

-  Follow :doc:`Installing SecureDrop <install>`

Day 2: Journalist and Admin Training
------------------------------------

Journalist Training
~~~~~~~~~~~~~~~~~~~

Time: 2 separate sessions, about 2 hours each

Participants: journalists and admins

-  Check access to previously created Tails USB
-  Generate personnel GPG keys
-  Setup KeyPassX manager (one for *SVS*, one for personnel Tails)
-  Options between YubiKey/FreeOTP app for 2FA (SSH,
   *Journalist Interface*, FDE and password managers)
-  Secure-deleting and difference between wipe and erase free space on
   Tails, and when to use each
-  Disaster recovery for 2FA and password manager, personnel GPG keys
-  Updating Tails
-  Backing up the *SVS*
-  If needed, process for distributing the Application's private GPG key
   to a distant journalist's air-gapped *SVS*
-  Do complete journalist process walk through twice, either on
   different days or between morning/afternoon sessions
-  Using MAT (Metadata Anonymisation Toolkit)
-  What to do for unsupported formats

Admin Training
~~~~~~~~~~~~~~

Time: 2 hours

Participants: admins

-  Check access to previously created Tails USB
-  Generate personnel GPG keys
-  Setup KeyPassX manager (one for *SVS*, one for personnel Tails)
-  Options between YubiKey/FreeOTP app for 2FA (SSH,
   *Journalist Interface*, FDE and password managers)
-  Secure-deleting and difference between wipe and erase free space on
   Tails, and when to use each
-  Disaster recovery for 2FA and password manager, personnel GPG keys
-  Updating Tails
-  Setting up SSH aliases for the *Admin Workstation*
-  How to use screen or tmux to help prevent being locked out of the
   system
-  Adding packages to Tails
-  Go over common OSSEC alerts for security updates and daily reports
-  Disaster recovery for application, remote access and *SVS*
-  Common admin actions
-  Adding/removing users
-  Enabling logging
-  Sending logs to FPF
-  Generating new Tor onion services
-  Updating application's GPG key
-  Re-IP'ing
-  Backups
-  Disk space monitoring
-  Updating SMTP and OSSEC alert configs
-  Changing passphrases (for FDE, persistent volumes, 2FA, KeePassXC
   managers...)
-  What will happen to local modifications to prod system after updates
-  Updating SecureDrop Application

   -  Unattended upgrades
   -  Upgrades that require admin intervention
