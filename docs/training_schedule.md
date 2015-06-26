<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [SecureDrop On-Site Training Schedule](#securedrop-on-site-training-schedule)
  - [Day 1: Preparation and Install](#day-1-preparation-and-install)
    - [Setup and Introductions](#setup-and-introductions)
    - [Overview of SecureDrop](#overview-of-securedrop)
    - [Questions](#questions)
    - [Installing SecureDrop](#installing-securedrop)
  - [Day 2: Journalist and Admin Training](#day-2-journalist-and-admin-training)
    - [Journalist Training](#journalist-training)
    - [Admin training](#admin-training)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

#SecureDrop On-Site Training Schedule

This is a high level schedule for what happens for the 2 days during an on-site install.

##Day 1: Preparation and Install

###Setup and Introductions

Time: 30min

Participants: all

Required: projector, WiFi access, pre-configured demo SecureDrop instance and 2 laptops to act as the Journalist Workstation and SVS

* The demo instance has multiple sources to try and give a feel of what it will look like at 2 weeks past being public with sources in different states of the reply process

###Overview of SecureDrop

Time: 2 hours

Participants: journalists, editors, SecureDrop admins, OSSEC alert recipients and anyone else interested

* Go over the SecureDrop FAQs
* Go over the SecureDrop environment diagrams
* Importance of the landing page security and Twitter feedback
* Demo the source submission process
* Demo the journalist's processes for checking the Document Interface
* Demo the journalist's processes for replies
* Demo working with submissions on the SVS
* Discuss scrubbing submitted documents prior to publication
* Options for distributing with other news organizations
* Show example of an OSSEC alert, briefly cover what it does
* Show example of 'is it up?' Nagios monitoring alerts for Source Interface
* Explain why the Document Interface does not have 'is it up?' monitoring
* Discuss vanity onion URLs with Shallot and Scallion
* How to brand the Source and Document Interface
* Physical security of servers and SVS
* How to securely publicize the organization's Source Interface Tor URL
* Distribute important info:
  * Third-party security mailing lists to subscribe to
  * https://freedom.press/about/staff
  * https://freedom.press/securedrop
  * Hardware for SecureDrop
  * SecureDrop Deployment Best Practices
  * Source Best Practice Guide
  * Journalist Best Practice Guide
  * Answering the client vs. server side crypto debate
  * Link to security audits
  * Bunch of other in-progress docs are on securedrop.hackpad.com, many are still in draft form

###Questions

Time: 30 min

###Installing SecureDrop

Time: 6 hours

* Follow [Installing SecureDrop](install.md)


##Day 2: Journalist and Admin Training

###Journalist Training

Time: 2 separate sessions, about 2 hours each

Participants: journalists and admins

* Check access to previously created Tails USB
* Generate personnel GPG keys
* Setup KeyPassX manager (one for SVS, one for personnel Tails)
* Options between YubiKey/Google Authenticator app for 2FA (SSH, Document Interface, FDE and password managers)
* Secure-deleting and difference between wipe and erase free space on Tails, and when to use each
* Disaster recovery for 2FA and password manager, personnel GPG keys
* Updating Tails
* Backing up the SVS
* If needed, process for distributing the Application's private GPG key to a distant journalist's air-gapped SVS
* Do complete journalist process walk through twice, either on different days or between morning/afternoon sessions
* Using MAT
  * What to do for unsupported formats

###Admin training

Time: 2 hours

Participants: admins

* Check access to previously created Tails USB
* Generate personnel GPG keys
* Setup KeyPassX manager (one for SVS, one for personnel Tails)
* Options between YubiKey/Google Authenticator app for 2FA (SSH, Document Interface, FDE and password managers)
* Secure-deleting and difference between wipe and erase free space on Tails, and when to use each
* Disaster recovery for 2FA and password manager, personnel GPG keys
* Updating Tails
* Setting up SSH aliases for the admin Tails workstation
* How to use screen or tmux to help prevent being locked out of the system
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
  * Updating SMTP and OSSEC alert configs
  * Changing passwords (for FDE, persistent volumes, 2FA, KeePass managers...)
  * What will happen to local modifications to prod system after updates
  * Updating SecureDrop Application
    * Unattended upgrades
    * Upgrades that require admin intervention
