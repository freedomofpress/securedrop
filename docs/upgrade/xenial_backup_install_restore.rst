Ubuntu 16.04 LTS (Xenial) -  back up, install, restore
======================================================

One way to upgrade your instance to Xenial is to take a backup of your existing 
instance, install a new Xenial-based instance on new hardware, and then cut over to and validate the new instance. 

This approach has the following benefits

[ list here ]

However, some downsides include:

[ list here ]

This method may also be used to restore an instance that has become unusable due to an upgrade or hardware failure.


Communicating with users before the change
------------------------------------------

[ blurb here ]

 - You should coordinate the timing of the upgrade with the people responsible for checking for submissions. If they have ongoing conversations with sources, or are expecting submissions, it may be necessary to reschedule the upgrade.
 - You should also consider communicating the downtime downtime and reason for it on your instance's landing page.
 

Step 1: back up your instance
-----------------------------

[ refer to existing backup docs - some additional detail ] 


Step 2: install using Xenial
----------------------------

[ refer to existing installation notes ]


Step 3: Restore your instance data and config from backup
---------------------------------------------------------

[ refer to backup/restore docs ]

Step 4: Cut over to the new instance
------------------------------------

[ describe process of cutting over to new instance - collision between hidden services etc ]

Step 5: Test the instance connectivity and configuration
--------------------------------------------------------

[ TBD - either a bunch of shell commands that check installed versions and stuff like grsec and Apparmor, or a single script provided with the release to do basic server tests ]

[ Also a checklist for basic functionality - connectivity to the 4 services, and a run through the submission-to-decryption workflow ]

[ Anything else? ]

