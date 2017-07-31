Set up the Transfer Device
==========================

Journalists copy submissions from their *Journalist Workstation* to the
*Secure Viewing Station* using the *Transfer Device* which can be a
DVD or a USB drive.

Select DVDs or USBs
~~~~~~~~~~~~~~~~~~~

Using DVDs as the *Transfer Device* provides some protection
against certain kinds of esoteric USB-based attacks on the *Secure
Viewing Station*, but requires that you have blank DVDs, a
dedicated DVD drive for the *Secure Viewing Station*, DVD drives for use
with *Journalist Workstation*\ s, and a shredder capable of destroying
DVDs. Unless you are certain that you need to use DVDs as the *Transfer Device*,
you should use USB drives instead. If you have chosen to use DVDs instead, there
is nothing to set up now — just make sure that you have all the hardware on
hand.

USB Transfer Device Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The easiest and recommended option for a *Transfer Device* is a USB
drive. If you have a large team of journalists you may want to :doc:`create
several <onboarding>` of these. Here we'll just walk through
making one *Transfer Device* [#]_.

Create a USB Transfer Device
----------------------------

.. note:: This process will destroy all data currently on the drive.

First, label your USB drive “SecureDrop Transfer Device”.

On the *Secure Viewing Station*, open the
**Applications** menu in the top left corner and select
**Utilities** then |Disk Utility icon| **Disks**:

|screenshot of the Applications menu in Tails, highlighting Disk
Utility|

Connect your *Transfer Device* then pick your device in the menu on
the left. Since we're going to destroy all the data on this drive, it's
important that you pick the right drive. It should be named something
that sounds similar to the manufacturer's label on the outside of the
drive, and it will only appear after you plug it in. Double check that
you have clicked on the correct drive:

|screenshot of Disk Utility application|

Once you're sure you have the right drive, click the interlocking gears, then
**Format Partition...**.

.. note:: If there are multiple existing partitions on the drive, you should
          first click the "-" icon on the left of the interlocking gears icon to
          delete each partition, and then create another partition that fills
          all free space with the options as shown below.

|screenshot of the menu to create a new partition in the Disk Utility
application|

Give the partition on your *Transfer Device* a descriptive name
like “Transfer Device” and select the options as in the following screenshot:

|screenshot of passphrase selection prompt in the Disk Utility
application|

You won't need to memorize this passphrase or type it more than a few
times, so feel free to make a good long one. Then click **Format** to continue.
The Disks utility will ask you if you are sure: click **Format** to continue.
After a few seconds, your new *Transfer Device* should be ready for use.
If you haven't already, make sure to label it.

Set up the USB Transfer Device on each workstation
--------------------------------------------------

On each *Journalist Workstation* and *Secure Viewing Station* you'd like to use
the *Transfer Device* you will securely save the passphrase on the
persistent volume. This ensures that you will only have to type in the
passphrase once during initial set up and it will be automatic thereafter:

  #. Insert the Transfer Device
  #. Go to **Places ▸ Computer** and click the USB drive in the left column.
  #. Type in the passphrase and click "Remember Password":

  |image of the disk unlock prompt on Tails|

Remember to first do this on the *Secure Viewing Station* you just used to
create the device!

After you've done this on each computer you wish to use the *Transfer
Device* with, you're good to go!

.. |Disk Utility icon| image:: images/icons/disk-utility.png
.. |screenshot of the Applications menu in Tails, highlighting Disk Utility| image:: images/screenshots/applications_accessories_disk-utility.png
.. |screenshot of Disk Utility application| image:: images/screenshots/disk-utility.png
.. |screenshot of the menu to create a new partition in the Disk Utility application| image:: images/screenshots/create-partition.png
.. |screenshot of passphrase selection prompt in the Disk Utility application| image:: images/screenshots/create-passphrase.png
.. |image of the disk unlock prompt on Tails| image:: images/screenshots/passphrase-keyring.png

.. [#] Tails screenshots were taken on Tails 3.0.1. Please make an issue on
       GitHub if you are using the most recent version of Tails and the
       interface is different from what you see here.
