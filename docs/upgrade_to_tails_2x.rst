Upgrade Tails from 1.x to 2.x
=============================

.. warning:: Tails 1.x is no longer receiving updates, and is therefore
             vulnerable to a growing list of security vulnerabilities.

Newer versions of SecureDrop leverage improvements to the Tails OS since the
introduction of Tails 2.0. It is critical to upgrade all Tails USBs to the
latest version before upgrading SecureDrop. Upgrading Tails from 1.x to 2.x
must be done manually. Please follow this guide to updating each Tails USB
stick used in your SecureDrop instance. Be sure to use the Secure Viewing
Station computer so you benefit from its airgap while transfering sensitive
data.

.. note:: You will need:

    #. A "master" Tails USB running the most recent version of Tails (at least
       v2.3).
    #. A separate USB stick used to store encrypted backups of the old Tails
       sticks.
    #. Your existing SecureDrop Tails USB sticks (Admin, Journalist, and Secure
       Viewing Station).
    #. An airgapped machine to perform each Tails upgrade. (SVS reuse is OK.)

An airgapped machine (such as the SVS) is required in order to perform these
upgrades safely. By isolating the machine from all network access, you thereby
reduce the threat of compromise by actors who wish to gain access to your
SecureDrop instance.

Upgrade each Tails device
-------------------------

1. Prepare the master Tails USB
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because Tails 2.x is incompatible with older versions, you must create a new
"master" Tails USB stick for subsequent installations and upgrades to the USB
sticks already in-use by your organization.
To create this brand-new master Tails, follow the same :doc:`directions for
provisioning the first USB sticks <set_up_tails>` on another networked computer.

You may now boot into the master Tails device from your airgapped computer to
perform the next steps. At the Tails Greeter screen, be sure to enable admin
privileges.

2. Prepare the Backup Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. tip::
    While it's recommended to use a fresh USB stick for any backup operation,
    to cut down on cost, clutter, and/or waste, you may also repurpose older USB
    sticks to function as Backup Devices.

After logging into the master Tails device, open the Disks Utility by
navigating to **Applications ▸ Utilities ▸ Disks**.

Insert your Backup Device into a USB port and select it from the left column.
Brand new devices sometimes have pre-configured partitions, which you will need
to remove. Select any block of partitioned data, and click the minus (``-``)
button to remove any unwanted partitions.

|Unwanted Bloatware Partition|

Click the plus (``+``) button to register a new partition to cover the entire
available space. This should automatically be filled out for you in the wizard.

Be sure to do a full wipe of the existing data during this step, especially if
you choose to repurpose an older USB stick. Select **Overwrite existing data
with zeroes (Slow)** from the **Erase** options. This does mean that the
reformatting step will take some extra time, but it is the best way to insure
that previous data from older transfers, or manufacturer bloatware, are removed
from the Backup Device.

Give your new partition a strong passphrase.

|Create Partition|

.. tip:: If you plan on using this USB stick as a permanent backup, you will be
    responsible for retaining this passphrase for the long-haul. If you only want
    to use this USB as an intermediary backup, and plan on discarding the data
    after a successful migration, you may discard the passphrase once all steps are
    completed.

3. Backup a Tails USB
~~~~~~~~~~~~~~~~~~~~~

Insert the Tails USB (that you want to back up) into a free USB port.

Mount it by navigating to **Places ▸ Computer**, and clicking on the
encrypted disk. You will be prompted to enter the passphrase to unlock the disk
(the same passphrase you normally use to log into Tails on that USB stick).

Open a Nautilus window with admin priviledges by navigating to **Applications
▸ System Tools ▸ Root Terminal**. At the terminal prompt, simply type
``nautilus``.

|Root Terminal|

The Nautilus window should show both the Backup Device and the TailsData
partition as mounted.

|Migrate Data 1|

Copy the all data from the TailsData partition onto the Backup Device
**except**:

- ``persistence.conf``: in older versions of Tails, this file might have
slightly different directives in it that could temporarily brick a Tails 2.x
USB.
- ``claws-mail`` folder: Claws Mail is no longer included in Tails. The OS uses
Icebird instead. Some users might not have this folder, so if you don't see it
there, do not be alarmed.

|Migrate Data 2|

Ensure that all critical data has been successfully copied.  Specifically, be
sure the the ``gnupg``, ``bookmarks``, and ``Persistent`` folders are
completely copied.  Any loss of data from these folders could prevent users
from accessing submissions.

.. tip::
    Create subdirectories for each USB drive (Admin, Journalist, and SVS)
    within the Backup Device. Not only will doing so speed up the upgrade
    process, it will also provide you with long-term encrypted backups of the
    USB devices. In the event of a lost or stolen drive, you can restore access
    via this encryped backup device.

Once data are correctly copied, unmount the TailsData partition.

4. Upgrade a Tails USB
~~~~~~~~~~~~~~~~~~~~~~

With the Admin/Journo/SVS Tails USB still insterted in the machine, navigate to
**Applications ▸ Tails ▸ Tails Installer** and select the **Upgrade by
cloning** option.

|Upgrade by cloning|

The clone process will take a few minutes, and will display a message once it
is complete. If you see an error message about the device not being ready, try unplugging
and remounting the Tails device you're trying to back up.

Then move on to the next Tails device. If you have backed up all Tails devices,
move on to the **Finishing up** section below.

Finishing up
------------

Verify all devices are working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Boot into each drive and confirm that persistent files are present. Consider
submitting a test submission from the Admin Workstation, then downloading it on
the Journalist Workstation, and finally decrypting it on the SVS.
If you are able to decrypt the submission successfully, you have verified that
all Tails devices are working properly.

Consider retaining the encrypted backup drive for a disaster recovery device.
Document the passphrase in the Admin Workstation KeePass database, and store
the physical Backup Device in a locked safe or other secure location.


Reformat the Backup Device
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you do not have a secure location for storing the backups, or already have
other backups, you should destroy the Backup Device. Follow the procedure below
to destroy the device safely.

First, write random data to the disk.  You can discover the path to your Backup
Device by either running the ``fdisk -l`` command in terminal, or by observing
the information listed in Tails' Disks application.  Once you know where your
Backup Device is mounted, run ::

    dd if=/dev/urandom of=/dev/sdX

Repeat this step at least twice.

Next, repeat step 2 to restore a USB stick to a pristine state. While it
probably isn't necessary to physically destroy a Backup Device (because
LUKS-encrypted data is very hard to forensically recover), you could smash the
device with a hammer until the chips containing its flash memory are broken up
into pieces before disposal.

Troubleshooting
---------------

The steps described above should cleanly update your Tails devices without
issue. In the event that you are unable to access your persistent files on one
of the upgraded Tails devices, don't worry: you can still restore the original
files from the Backup Device you created. (Isn't it great to have backups?)

1. Restore data from a Backup Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the same airgapped machine, boot up the Tails USB stick you want to restore,
with both persistence and admin privileges.

Insert your Backup Device into a free USB port, and mount it by navigating to
**Places ▸ Computer**, and clicking on the encrypted disk. You will be
prompted to enter its passphrase.

Open a Nautilus window with admin priviledges by navigating to **Applications
▸ System Tools ▸ Root Terminal**. At the terminal prompt, simply type
`nautilus`.

Type ``ctrl`` + ``l`` and navigate to `/live/persistence/TailsData_unlocked`.

|Navigate to TailsData_unlocked|

Open a new tab (``ctrl`` + ``t``) and navigate to your Backup Device. Drag and
drop the backup data from your Backup Device onto the TailsData_unlocked tab.

When copying a folder, select the **Apply this action to all files** option and
click **Merge** to apply to all subfolders. Then you might have to select again
the **Apply this action to all files** option and click **Replace** to apply to
all files.

In a root terminal, or as sudo, execute the following command to fix the
ownership of your personal files: ::

    find /live/persistence/TailsData_unlocked/ -uid 1000 -exec chown -R 1000:1000 '{}' \;

Shut down, and boot up **with your primary Tails USB** and verify *everything*
is still there and accessible to you, including:

- KeePassX Database
- PGP keys

.. note::
    If you are restoring a Secure Viewing Station Tails USB, you may skip the
    **Reinstall SecureDrop** step below. It is only necessary to rerun the
    ``install.sh`` script when restoring an Admin or Journalist Workstation.

2. Reinstall SecureDrop
~~~~~~~~~~~~~~~~~~~~~~~

Continue checking your persistent files for the following critical assets:

- Bookmarks in Tor Browser
- SecureDrop files, especially the ``torrc_additions`` file in
  ``~/Persistent/.securedrop``.
- If you're an admin, also be sure the files in
  ``~/Persistent/securedrop/install_files/`` are available.

Shut down your Tails USB on the airgapped station and move to the computer you
normally use to check for submissions. At this stage, all data has been
migrated and it's safe to use this Tails USB on a networked computer.

Boot up Tails once again with persistence and admin privileges.

.. warning::
    Copy ``~/Persistent/.securedrop/torrc_additions`` to a place like
    your desktop. You'll need these old values for the following step.

Re-install Securedrop with ``cd ~/Persistent/securedrop/tails_files && sudo
./install.sh``. Once completed, test your access to the Document Interface,
and, if you're a Secure Drop admin, test your ssh connection to the application
and monitor servers.

.. |Migrate Data 1| image:: images/backup_and_migrate/migrate_data_2.png
.. |Migrate Data 2| image:: images/backup_and_migrate/migrate_data_1.png
.. |Create Partition| image:: images/backup_and_migrate/partition_create_3.png
.. |Unwanted Bloatware Partition| image:: images/backup_and_migrate/partition_create_7.png
.. |Root Terminal| image:: images/backup_and_migrate/root_terminal_3.png
.. |Navigate to TailsData_unlocked| image:: images/backup_and_migrate/tails_data_unlocked_2.png
.. |Upgrade by cloning| image:: images/backup_and_migrate/tails_installer_2.png
