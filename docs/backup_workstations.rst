Backup the Workstations
=======================

Now that you have set up the *Secure Viewing Station*, the *Admin Workstation*,
and your *Journalist Workstations*, it is important you make a backup. Your USB
drive may wear out, a journalist might lose their backup drive, or something
completely unexpected may happen.

In all these cases, it is useful to have a backup of your data for each device.

What you need
-------------

  #. Your *existing SecureDrop Tails USB sticks* (*Admin Workstation*,
     *Journalist Workstation*, and *Secure Viewing Station*).
  #. An *airgapped machine* to perform the Tails upgrades. The *Secure Viewing
     Station* may be used for this task.
  #. Your "master" Tails USB, which we will use to perform the backups.
  #. At least one USB drive to backup the data on your current SecureDrop
     Tails USB sticks.

  .. warning::
             An airgapped machine (such as the *Secure Viewing Station*) is
             required in order to perform these backups safely. By isolating
             the machine from all network access, you reduce the exposure of
             sensitive data to networked computers, thereby reducing the threat
             of compromise by adversaries who wish to gain access to your
             SecureDrop instance.

The airgapped machine should have 3 USB ports, so you can plug in the Tails
drive you wish to upgrade, the *master Tails USB* drive, and the *backup drive*
at the same time. If you don't have 3 USB ports available, you can use a USB
hub, which may reduce transfer speeds.

.. note::

        The steps in this section should be performed for each *Secure Viewing
        Station*, *Journalist Workstation*, and *Admin Workstation* USB drive in
        your organization.

Preparing the Backup Device
---------------------------

Navigate to **Applications** ▸ **Utilities** ▸ **Disks**.

|Applications Utilities Disks|

Insert the USB drive you wish to use as a backup drive.

Select the drive from the list of drives in the left column.

|Select the Disk|

Click the button with the two cogs and click **Format Partition...**

|Click Cogs|

Fill out the form as follows:

|Format Backup Drive|

* **Erase**: `Don't overwrite existing data (Quick)`
* **Type**: `Encrypted, compatible with Linux systems (LUKS + Ext4)`
* **Name**: `Backup`

.. warning::
            Since this will serve as a long-term backup, **make sure to use a
            strong passphrase.**

Click **Format**.

A dialog box will appear asking you **Are you sure you want to format the
volume?** appears, click **Format**.

Once completed, you will see two partitions appear:

|Two Partitions Appear|

Now that you made the backup device, plug in the device you want to backup.
Then, browse to **Places** ▸ **Computer**:

|Browse to Places Computer|

Click on the disk on the left side column. Fill in the passphrase you usually
use when you enable Persistence on that device:

|Fill in Passphrase|

You should now have both the Backup and TailsData partition to be backed up
mounted and ready to access.

|Backup and TailsData Mounted|

Open a Nautilus window with admin privileges by going to
**Applications** ▸ **System Tools** ▸ **Terminal**.

|Open Terminal|

Type ``gksu nautilus`` at the terminal prompt and hit enter. You'll need to type
your admin passphrase.

|Start gksu nautilus|

.. note::
  When you run ``gksu nautilus``, you may run into an error where Nautilus
  complains that it can't create a required folder. If that happens, just click
  OK and continue normally.

  If a Nautilus window *doesn't* come up, it might be because an admin
  passphrase wasn't set. If that's the case, you'll need to restart and set an
  admin passphrase before continuing.

.. warning::
            Make sure you use keep the `Terminal` window open while you perform
            the backups. Otherwise, the `Nautilus` window will close.

Make sure you create a directory on the backup drive to store the data from the
drive you are backing up:

|Make Folders for All Drives|

Copy over everything in the TailsData partition to the relevant folder on the
Backup drive. You can simply drag to select all the files and then copy and
paste them to the relevant folder on the Backup drive.

In particular, ensure ``gnupg`` and ``Persistent`` have been successfully
copied over. These files are critical for decrypting submissions.

Once complete, unmount the TailsData partition.

Repeat these steps for every device, making a new folder on the backup device
for each device you backup.

Finally, once you have completed the steps described in this section for each
USB drive, unmount the Backup partition and store the drive somewhere safely.

.. |Browse to Places Computer| image:: images/upgrade_to_tails_3x/browse_to_places_computer.png
.. |Click Cogs| image:: images/upgrade_to_tails_3x/click_the_button_with_cogs.png
.. |Fill in Passphrase| image:: images/upgrade_to_tails_3x/fill_in_passphrase.png
.. |Format Backup Drive| image:: images/upgrade_to_tails_3x/fill_out_as_follows.png
.. |Start gksu nautilus| image:: images/upgrade_to_tails_3x/gksu_nautilus.png
.. |Make Folders for All Drives| image:: images/upgrade_to_tails_3x/make_folders_for_all_drives.png
.. |Backup and TailsData Mounted| image:: images/upgrade_to_tails_3x/backup_and_tailsdata_mounted.png
.. |Applications Utilities Disks| image:: images/upgrade_to_tails_3x/navigate_to_applications.png
.. |Open Terminal| image:: images/upgrade_to_tails_3x/open_terminal.png
.. |Select the Disk| image:: images/upgrade_to_tails_3x/select_the_disk.png
.. |Two Partitions Appear| image:: images/upgrade_to_tails_3x/two_partitions_appear.png
