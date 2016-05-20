Upgrade Tails from 1.x to 2.x
=============================

Starting with SecureDrop version 0.3.7, SecureDrop's Tails integration
leverages improvements to the Tails OS since the introduction of Tails 2.0. It
is critical to upgrade all of your Tails USBs to the latest version of Tails
before upgrading SecureDrop to 0.3.7 or later.

.. warning:: Tails 1.x is no longer receiving updates, and is therefore
             vulnerable to a growing list of security vulnerabilities. We
             strongly encourage you to upgrade all of your Tails USBs to the
             latest version of Tails as soon as possible.

Upgrading Tails from 1.x to 2.x must be done manually. Please follow this guide
to updating each Tails USB stick used in your SecureDrop instance. Be sure to
use the Secure Viewing Station computer so you benefit from its airgap while
transfering sensitive data.

.. note:: You will need:

    #. A *master Tails USB* running the most recent version of Tails (at least
       v2.3).
    #. A *backup device*, a separate, encrypted USB drive used to store backups
       of the old Tails sticks.
    #. Your *existing SecureDrop Tails USB sticks* (Admin, Journalist, and Secure
       Viewing Station).
    #. An *airgapped machine* to perform the Tails upgrades. It is ok to reuse
       the Secure Viewing Station for this task.

An airgapped machine (such as the SVS) is required in order to perform these
upgrades safely. By isolating the machine from all network access, you reduce
the exposure of sensitive data to networked computers, thereby reducing the
threat of compromise by adversaries who wish to gain access to your SecureDrop
instance.

Upgrade each Tails device
-------------------------

1. Prepare the master Tails USB
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Because Tails 2.x is incompatible with older versions, you must create a new
"master" Tails USB stick for subsequent installations and upgrades to the USB
sticks already in-use by your organization.
To create this brand-new master Tails, follow the same :doc:`directions for
provisioning the first USB sticks <set_up_tails>` on another networked computer.

Once you've created a new Tails 2.x USB, boot into it from your airgapped
computer to perform the next steps. At the Tails Greeter screen, be sure to
enable admin privileges.

2. Prepare the Backup Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We will use the **Tails Installer** to upgrade your Tails 1.x USB to Tails 2.x.
While this usually works without any issues, we're going to start by making
backups of the important data on your current Tails USBs, so you can use them for
recovery in case something goes wrong.

.. tip:: While it's recommended to use a fresh USB stick for any backup operation,
         to cut down on cost, clutter, and/or waste, you may also repurpose old USB
         sticks to function as Backup Devices. *Note that this process will
         permanently erase any data stored on the Backup Device.*

After logging into the master Tails device, open the Disks Utility by
navigating to **Applications ▸ Utilities ▸ Disks**. Insert the Backup Device
into a USB port. It will appear in the list of disks in the left column. Select
it.

|Selected Backup Device|

Click the button with the interlocking gears icon and choose **Format...**.

|Format...|

Fill out the **Format Volume** settings as shown in the screenshot below.
There's no need to overwrite existing data, and doing so can take a long time.
You should use a strong passphrase to encrypt the drive.

.. note:: If you plan on using this USB stick as a permanent backup, you will be
    responsible for retaining this passphrase for the long-haul. If you only want
    to use this USB as an intermediary backup, and plan on discarding the data
    after a successful migration, you may discard the passphrase once all steps are
    completed.

|Format Settings|

Click **Format...**. A dialog box will ask: "Are you sure you want to format the
volume?". Click **Format**.

While the drive is being formatted, you will see a spinning progress indicator
next to the drive's name in the left column. Wait until it is done. When it is
done, you will see the partition layout has two nested partitions (LUKS and
ext4), like this:

|Formatted|

You're ready to start backing up your current Tails USBs.

.. |Selected Backup Device| image:: images/upgrade_to_tails_2x/ready_to_format.png
.. |Format...| image:: images/upgrade_to_tails_2x/format.png
.. |Format Settings| image:: images/upgrade_to_tails_2x/format_settings.png
.. |Formatted| image:: images/upgrade_to_tails_2x/formatted.png


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

- ``persistence.conf``
   In older versions of Tails, this file might have
   slightly different directives in it that could temporarily brick a Tails 2.x
   USB.
- ``claws-mail``
   Claws Mail is no longer included in Tails. The OS uses Icebird instead. Some
   users might not have this folder, so if you don't see it there, do not be
   alarmed.

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

.. |Root Terminal| image:: images/upgrade_to_tails_2x/root_terminal.png
.. |Migrate Data 1| image:: images/upgrade_to_tails_2x/migrate_data_1.png
.. |Migrate Data 2| image:: images/upgrade_to_tails_2x/migrate_data_2.png

4. Upgrade a Tails USB
~~~~~~~~~~~~~~~~~~~~~~

With the Admin/Journo/SVS Tails USB still insterted in the machine, navigate to
**Applications ▸ Tails ▸ Tails Installer** and select the **Upgrade by
cloning** option.

|Upgrade by cloning|

Select the Tails 1.x USB that you wish to upgrade from the drop-down menu
labeled **Target Device**. If it is the only other USB plugged in to the
computer, it should be automatically selected.

|Select Target Device|

The clone process will take a few minutes, and will display a message once it is
complete. If you see an error message about the device not being ready, try
unplugging and remounting the Tails device you're trying to upgrade.

When you're done, move on to the next Tails device. Once you have backed up all
Tails devices, move on to the **Finishing up** section below.

.. |Upgrade by cloning| image:: images/upgrade_to_tails_2x/upgrade_by_cloning.png
.. |Select Target Device| image:: images/upgrade_to_tails_2x/select_target_device.png

Finishing up
------------

.. _verify-post-upgrade:

Verify all devices are working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Shut down each Tails USB on the airgapped computer and move it to the computer
you normally use it on. Boot into each newly upgraded Tails USB, enabling
persistence. Confirm that the persistent files are present and that your
workflow is unaffected.

As a test, consider submitting a test submission, downloading it on the
Journalist Workstation, and finally decrypting it on the SVS.
If you are able to decrypt the submission successfully, you have verified that
the Journalist Workstation and SVS are working correctly after the upgrade.

To test the Admin Workstation, make sure you can still SSH into the servers:

.. code:: sh

    $ ssh <username>@<app server .onion address> hostname
    app
    $ ssh <username>@<monitor server .onion address> hostname
    mon

.. tip:: If you forgot, your SSH username is in
         ``install_files/ansible-base/prod-specific.yml`` as the value of the
         ``ssh_users`` variable. The .onion addresses for SSH for each server
         are in ``install_files/ansible-base/app-ssh-aths`` and
         ``install_files/ansible-base/mon-ssh-aths``, respectively.

.. tip:: Consider retaining the encrypted backup drive as a disaster recovery
         device. Document the passphrase in the Admin Workstation KeePassX
         database, and store the physical Backup Device in a locked safe or
         other secure location.

Wipe the Backup Device
~~~~~~~~~~~~~~~~~~~~~~

If you do not have a secure location for storing the backups, or already have
other backups, you should wipe the Backup Device. There is a lot of debate over
the best way to do this, but we think it's sufficient to simply overwrite it
with random data a couple of times. Since the Backup Device is encrypted with
LUKS, which employs a number of anti-forensic-recovery techniques, this should
be enough to prevent forensic recovery.

First, find the path to the Backup Device. You can find the path with the
**Disks** application, selecting the drive in the left column, and looking at
the **Device** entry. It is usually a string that starts with ``/dev/sd``.

.. warning:: Make sure you use the correct path for the Backup Device in the
             next command! Otherwise, you run the risk of irreversibly wiping a
             different drive on the system, such as the Tails USB you are
             running.

To overwrite the Backup Device, open a **Terminal** and run:

.. code:: sh

    dd if=/dev/urandom of=<path to Backup Device>

Re-run this command at least twice. Each run will take a while.

If you want to reuse the drive for another purpose, use the **Disks** utility to
reformat it appropriately.

.. note:: While it probably isn't necessary to physically destroy a Backup
          Device (because it's encrypted, and LUKS is designed to thwart
          forensic recovery), if you're *really* paranoid you can additionally
          smash the device with a hammer until the chips containing its flash
          memory are broken up, then dispose of the pieces in the garbage.

Troubleshooting
---------------

The steps described above should cleanly update your Tails devices without
issue. In the event that one or more of your upgraded Tails USBs are not working
as expected, don't worry: you can still manually restore from the Backup Device
you created. (Isn't it great to have backups?)

1. Restore data from the Backup Device
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On the same airgapped machine, boot up the Tails USB stick you want to restore,
with both persistence and admin privileges. Insert your Backup Device into a
free USB port, and mount it by navigating to **Places ▸ Computer**, and clicking
on the encrypted disk. You will be prompted to enter its passphrase.

Open a Nautilus window with admin priviledges by navigating to **Applications ▸
System Tools ▸ Root Terminal**. At the terminal prompt, simply type `nautilus`
and hit Enter. Type ``ctrl`` + ``l``, type
`/live/persistence/TailsData_unlocked`, and hit Enter to navigate there.

|Navigate to TailsData_unlocked|

|TailsData_unlocked|

Open a new tab in Nautilus (``ctrl`` + ``t``) and navigate to your Backup
Device. Drag and drop the backup data from your Backup Device onto the
TailsData_unlocked tab.

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
    ``tails_files/install.sh`` script when restoring an Admin or Journalist
    Workstation.

.. |Navigate to TailsData_unlocked| image:: images/upgrade_to_tails_2x/tails_data_unlocked_1.png
.. |TailsData_unlocked| image:: images/upgrade_to_tails_2x/tails_data_unlocked_2.png

2. Reinstall the SecureDrop Tails Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Continue checking your persistent files for the following critical assets:

- Bookmarks in Tor Browser
- SecureDrop files, especially the ``torrc_additions`` file in
  ``~/Persistent/.securedrop``.
- If you're an admin, also be sure the files in
  ``~/Persistent/securedrop/install_files/`` and the SSH keys in ``~/.ssh`` are
  available.

Shut down your Tails USB on the airgapped station and move to the computer you
normally use to check for submissions. At this stage, all data has been
migrated and it's safe to use this Tails USB on a networked computer.

Boot up Tails once again with persistence and admin privileges.

.. warning::
    Copy ``~/Persistent/.securedrop/torrc_additions`` to a place like
    your desktop. You'll need these old values for the following step.

Re-install the Securedrop Tails configuration with ``cd
~/Persistent/securedrop/tails_files && sudo ./install.sh``. Once completed, test
your access to the Document Interface, and, if you're a Secure Drop admin, test
your ssh connection to the application and monitor servers.

