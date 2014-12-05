#SecureDrop On Site Training Schedule

This is a high level schedule for the what happens for the 2 days during an on site install.

##Day 1: Prep and Install

###Setup and Intros

Time: 30min

Participants: all

Required: projector, WiFi access, pre configured demo SecureDrop instance and 2 laptops to act as the journalist workstation and SVS

* The demo instance has multiple sources to try to give feel of what it will look like at 2 weeks past being public and with sources in different state of reply process

###Overview of SecureDrop

Time: 2 hours

Participants: journalists, editors, securedrop admins, ossec alert recipients and anyone else interested

* Go over the SecureDrop FAQs
* Go over the SecureDrop environment diagrams
* Importance of the landing page security and Twitter feedback
* Demo the source submission process
* Demo the journalist's processes for checking the document interface
* Demo the journalist's processes for replies
* Demo working with submissions on the SVS
* Discuss scrubbing submitted documents prior to publication
* Options for distributing with other news organizations
* Show example of OSSEC alert, briefly cover what it does
* Show example is it up monitoring alerts for source interface
* Explain why the Document Interface does not have is it up monitoring.
* Discuss vanity onion URLs with Shallot and Scallion
* How to brand the source and document interface
* Physical security of servers and SVS
* How to securely publicize the organizations source interface Tor URL
* Distribute important info
  * 3rd party security mailing lists to subscribe
  * https://pressfreedomfoundation.org/staff
  * https://pressfreedomfoundation.org/securedrop
  * Hardware for SecureDrop
  * SecureDrop Deployment Best Practices
  * Source Best Practice Guide
  * Journalist Best Practice Guide
  * Answering the client vs. server side crypto debate
  * Link to security audits
  * Bunch of other in progress docs are on securedrop.hackpad.com, the hackpad.com ones are still in draft form

###Questions

Time: 30 min

###Installing SecureDrop

Time: 6 hours

* Follow [Installing SecureDrop](install.md)


##Day 2: Journalist and Admin Trianing

###Journalist Training

Time: 2 separate session about 2 hours each

Participants: journalists and admins

* Check access to previously created Tails usb
* Generate personnel GPG keys
* Setup keypass manager (one for SVS one for personnel Tails)
* Options between YubiKey/Google-Authenticator app for 2fa (SSH, document interface, FDE and password managers)
* Secure-deleting and difference between wipe and erase free space on Tails, and when to use each
* Disaster recovery for 2fa and password manager, personnel GPG keys
* Updating Tails
* Backing up the SVS
* If needed process for distributing the application's private gpg key to a distant journalist's airgapped SVS
* Do complete journalist process walk through twice either different days or morning/afternoon sessions
* Using MAT
  * What to do for unsupported formats

###Admin training

Time: 2 hours

Participants: admins

* Check access to previously created Tails usb
* Generate personnel GPG keys
* Setup keypass manager (one for SVS one for personnel Tails)
* Options between YubiKey/Google-Authenticator app for 2fa (SSH, document interface, FDE and password managers)
* Secure-deleting and difference between wipe and erase free space on Tails, and when to use each
* Disaster recovery for 2fa and password manager, personnel GPG keys
* Updating Tails
* Setting up ssh aliases for the admin Tails workstation
* How to use screen or tmux to help preventing being locked out of system
* Adding packages to Tails
* Go over common OSSEC alerts for security updates and daily reports
* Disaster recovery for application, remote access and SVS
* Common admin actions
  * Adding/removing users
  * Enabling logging
  * Sending logs to FPF
  * Generating new Tor hidden services
  * Updating application's GPG key
  * Re-IP'ing
  * Backups
  * Disk space monitoring
  * Updating SMTP and OSSEC alert configs.
  * Changing passwords (for FDE, persistent volumes, 2fa, KeePass managers...)
  * What will happen to local modifications to prod system after updates.
  * Updating SecureDrop Application
    * Unattended upgrades
    * Upgrades that require admin intervention
