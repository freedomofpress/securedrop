Upgrade Tails from 2.x to 3.x
=============================

Why you should upgrade
----------------------

Starting with SecureDrop version 0.4, we require users update to Tails version
3.0 or later. Upgrading Tails from 2.x to 3.x must be done manually. This guide
will show you how to upgrade each Tails USB stick used your SecureDrop instance.

What you need
-------------

  #. Your *existing SecureDrop Tails USB sticks* (*Admin Workstation*,
     *Journalist Workstation*, and *Secure Viewing Station*).
  #. An *airgapped machine* to perform the Tails upgrades. The *Secure Viewing
     Station* may be used for this task.
  #. Two USB drives: one to create a new master Tails 3.x USB and one to backup
     the data on your current SecureDrop Tails USB sticks.

  .. warning::
             An airgapped machine (such as the *Secure Viewing Station*) is
             required in order to perform these upgrades safely. By isolating
             the machine from all network access, you reduce the exposure of
             sensitive data to networked computers, thereby reducing the threat
             of compromise by adversaries who wish to gain access to your
             SecureDrop instance.

The airgapped machine should have 3 USB ports, so you can plug in the Tails
drive you wish to upgrade, the *master Tails USB* drive, and the *backup drive*
at the same time. If you don't have 3 USB ports available, you can use a USB
hub, which may reduce transfer speeds.

1. Prepare the master Tails USB
-------------------------------

Because Tails 3.x is incompatible with older versions, you must create a new
"master" Tails USB stick for subsequent installations and upgrades to the USB
sticks already in use by your organization.

To create this brand new master Tails, follow the same :doc:`directions for
provisioning the first USB sticks <set_up_tails>` on another networked computer.

Once you've created a new Tails 3.x USB, boot into it from your airgapped
computer to perform the remaining steps.

At the Tails Greeter screen, enable admin privileges by setting a root password.
In Tails 3.x, you do this by clicking the **+** button, then navigating to
**Additional Settings** ▸ **Administration Password**.

2. Backup the Tails drives
--------------------------

.. note::

        The steps in this section should be performed for each *Secure Viewing
        Station*, *Journalist Workstation*, and *Admin Workstation* USB drive in
        your organization.

Before you upgrade your Tails drives, you should backup the data in case
something goes wrong.

Navigate to **Applications** ▸ **Utilities** ▸ **Disks**.

|Applications Utilities Disks|

Insert the USB drive you wish to use as a backup drive.

Select the drive from the list of drives in the left column.

|Select the Disk|

Click the button with the two cogs and click **Format Partition...**

|Click Cogs|

Fill out the form as follows:

|Format Backup Drive|

.. warning::
            Make sure you use a strong passphrase if this is a long term backup
            drive.

Click **Format**.

A dialog box will appear asking you **Are you sure you want to format the
volume?** appears, click **Format**.

Once completed, you will see two partitions appear:

|Two Partitions Appear|

Browse to **Places** ▸ **Computer**:

|Browse to Places Computer|

Click on the disk on the left side column. Fill in the passphrase you usually
use when enabling Persistence:

|Fill in Passphrase|

You should now have both the Backup and TailsData partition to be backed up
mounted.

|Backup and TailsData Mounted|

Open a Nautilus window with administrator privileges by going to
**Applications** ▸ **System Tools** ▸ **Root Terminal**.

|Root Terminal|

Type ``nautilus`` at the terminal prompt and hit enter:

|Start Nautilus|

Make sure you create a directory on the backup drive to store the data from the
drive you are backing up:

|Make Folders for All Drives|

Copy over everything in the TailsData partition to the relevant folder on the
Backup drive. You can simply drag to select all the files and then copy and
paste them to the relevant folder on the Backup drive.

In particular, ensure ``gnupg`` and ``Persistent`` have been successfully
copied over. These files are critical for decrypting submissions.

Once complete, unmount the TailsData partition.

Finally, once you have completed the steps described in this section for each
USB drive, unmount the Backup partition and store the drive somewhere safely.

.. |Nautilus| image:: images/upgrade_to_tails_3x/nautilus_start.png
.. |Browse to Places Computer| image:: images/upgrade_to_tails_3x/browse_to_places_computer.png
.. |Click Cogs| image:: images/upgrade_to_tails_3x/click_the_button_with_cogs.png
.. |Fill in Passphrase| image:: images/upgrade_to_tails_3x/fill_in_passphrase.png
.. |Format Backup Drive| image:: images/upgrade_to_tails_3x/fill_out_as_follows.png
.. |Start Nautilus| image:: images/upgrade_to_tails_3x/nautilus_start.png
.. |Make Folders for All Drives| image:: images/upgrade_to_tails_3x/make_folders_for_all_drives.png
.. |Backup and TailsData Mounted| image:: images/upgrade_to_tails_3x/backup_and_tailsdata_mounted.png
.. |Applications Utilities Disks| image:: images/upgrade_to_tails_3x/navigate_to_applications.png
.. |Root Terminal| image:: images/upgrade_to_tails_3x/root_terminal.png
.. |Select the Disk| image:: images/upgrade_to_tails_3x/select_the_disk.png
.. |Two Partitions Appear| image:: images/upgrade_to_tails_3x/two_partitions_appear.png

3. Upgrade the Tails drives
---------------------------

.. note::
        The steps in this section should be performed for each *Secure Viewing
        Station*, *Journalist Workstation*, and *Admin Workstation* USB drive in
        your organization.

Next you will upgrade each drive.

Begin by inserting the drive you wish to upgrade into the machine.

Navigate to **Applications** ▸ **Tails** ▸ **Tails Installer**.

|Tails Installer|

Click **Upgrade by cloning**.

|Upgrade by Cloning|

Make sure the correct drive is selected.

|Tails Cloning|

Click **Install Tails**.

A dialog box will appear asking you to **Please confirm your device selection**.

|Confirm Upgrade|

Click **Yes** to proceed with the installation.

It may take a while for the Tails USB to upgrade.

Once complete, you should see a success message:

|Installation Complete|

.. |Tails Installer| image:: images/upgrade_to_tails_3x/tails_installer.png
.. |Tails Cloning| image:: images/upgrade_to_tails_3x/tails_cloning.png
.. |Upgrade by Cloning| image:: images/upgrade_to_tails_3x/upgrade_by_cloning.png
.. |Confirm Upgrade| image:: images/upgrade_to_tails_3x/confirm_upgrade.png
.. |Installation Complete| image:: images/upgrade_to_tails_3x/installation_complete.png

4. Verify the Upgrades
----------------------

Verify the Journalist Workstation and SVS USB Drives Are Successfully Updated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To test these two drives, run through the following test procedure:

  #. Submit a test document to the source interface.
  #. Log in to the journalist interface.
  #. Download the test document.
  #. Transfer the test document over to the SVS.
  #. Decrypt the test document.
  #. Delete the submission.

If you are able to successfully download and decrypt your test submission, then
your upgrade was successful!

Verify the Administrator Workstation USB Drive Was Successfully Updated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure that you are able to SSH into both servers. Remember you can use the
following shortcuts:

.. code:: sh

   ssh mon
   ssh app

Destroy the Backup or Move It to a Safe Location
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At this point, you should move your backup drive to a safe location (if you used
a strong passphrase). Else, you should destroy the backup drive following the
instructions `here <upgrade_to_tails_2x.html#wipe-the-backup-device>`__.

If you encounter issues
-----------------------

If you run into issues, you can always restore your data from the Backup
device following the instructions
`here <upgrade_to_tails_2x.html#restore-data-from-the-backup-device>`__.

If you continue to have problems, you can contact us through the
`SecureDrop Support Portal`_.

.. _SecureDrop Support Portal: https://securedrop-support.readthedocs.io/en/latest/
