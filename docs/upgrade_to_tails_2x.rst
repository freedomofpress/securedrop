Upgrade Tails from 1.x to 2.x
=============================

Newer versions of SecureDrop leverage improvements to the Tails OS since the introduction of Tails 2.0 (and subsequent versions). It is critical to upgrade all Tails USBs to the latest version before upgrading SecureDrop. For some admins, this might be complicated, since the upgrade from 1.x to 2.x must be done manually. Please follow this guide to updating the entire system, and special attention to only use the Secure Viewing Station computer so you benefit from its airgap while transfering sensitive data.

You will need
-------------

1. Intermediary Tails USB
1. Transfer Device
1. Your existing SecureDrop Tails devices

1. Prepare the Intermediary Tails USB
-------------------------------------

Because Tails 2.x is incompatible with older versions, you must create a new Intermediary Tails USB stick for subsequent installations and upgrades to the USB sticks already in-use by your organization.

To create this brand-new Intermediary Tails, follow the same :doc:`directions for provisioning the first USB sticks <set_up_tails>`.

You may now boot into this new Tails from your airgapped Secure Viewing Station to perform the next step. At the Tails Greeter screen, be sure to enable admin privileges.

1. Prepare the Transfer Device
------------------------------

While it's recommended to use a fresh USB stick for any backup operation, to cut down on cost and/or waste, you may also repurpose older USB sticks to function as Transfer Devices.

Open the Disks Utility by navigating to Applications->Utilities->Disks.

Insert your Transfer Device into a USB port and select it from the left column. Brand new devices sometimes have pre-configured partitions, which you will need to remove. Select any block of partitioned data, and click the minus (`-`) button to remove any unwanted partitions.

Click the plus (`+`) button to register a new partition to cover the entire available space. This should automatically be filled out for you in the wizard.

Be sure to do a full wipe of the existing data during this step, especially if you choose to repurpose an older USB stick. Select "Overwrite existing data with zeroes (Slow)" from the "Erase" options. This does mean that the reformatting step will take some extra time, but it is the best way to insure that previous data from older transfers, or manufacturer bloatware, is removed from the Transfer Device.

Give your new partition a complex, diceware-generated passphrase. If you plan on using this USB stick as a permanent backup, you will be responsible for retaining this passphrase for the long-haul. If you only want to use this USB as an intermediary backup, and plan on discarding the data after a successful migration, you may discard the passphrase once everything is completed.

2. Backup a Tails USB
--------------------------------------------

Insert your Admin Workstation Tails into a free USB port, and mount it by navigating to Places->Computer, and clicking on the encrypted disk. You will be prompted to enter the passphrase to unlock the disk (the same passphrase you normally use to log into Tails on this USB stick).

Open a Nautilus window with admin priviledges by navigating to Applications->System Tools->Root Terminal. At the terminal prompt, simply type `nautilus`.

The Nautilus window should show both the Transfer Device and the TailsData partition as mounted; copy the contents of the TailsData partition onto the Transfer Device.

Insure that all critical data has been successfully copied.  Specifically, be sure the the `gnupg`, `bookmarks`, and `Persistent` folders are completely copied.  Any loss of data from these folders could prevent users from accessing submissions.


3. Upgrade a Tails USB
------------------------------------------------------

The Tails Installer program should reliably upgrade the inserted Tails USB, but if for some reason this process fails, you have your data backed up to the Transfer Device. If you find yourself in that unlucky situation, follow step 4. Otherwise, skip to step 5 to reformat the Transfer Device for reuse or if you plan on physically destroying it.

4. Restore data from a Transfer Device
--------------------------------------



5. Reformat the Transfer Device
---------------------------------------


