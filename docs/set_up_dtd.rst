Set up the Data Transfer Device
===============================

Journalists copy submissions from their *Journalist Workstation* to the
*Secure Viewing Station* using the *Data Transfer Device* which can be a
DVD or a USB drive.

Using DVDs as the *Data Transfer Device* provides some protection
against certain kinds of esoteric USB-based attacks on the *Secure
Viewing Station*, but requires that you keep blank DVDs on hand, have a
dedicated DVD drive for the *Secure Viewing Station*, DVD drives for use
with *Journalist Workstation*\ s, and a shredder capable of destroying
DVDs. Unless you are certain that you need to use DVDs as the *Data
Transfer Device*, you should use USB drives instead. If you have chosen
to use DVDs instead, there is nothing to set up now — just make sure
that you have all the hardware on hand.

The easiest and recommended option for a *Data Transfer Device* is a USB
drive. If you have a large team of journalists you may want to :doc:`create
several <onboarding>` of these. Here we'll just walk through
making one *Data Transfer Device*. Note: this process will destroy all
data currently on the drive. You should probably use a new USB drive.

First, label your USB drive “SecureDrop Data Transfer Device”. Open the
*Applications* menu in the top left corner and select |Accessories icon|
*Accessories* then |Disk Utility icon| *Disk Utility*.

|screenshot of the Applications menu in Tails, highlighting Disk
Utility|

Connect your *Data Transfer Device* then pick your device in the menu on
the left. Since we're going to destroy all the data on this drive, it's
important that you pick the right drive. It should be named something
that sounds similar to the manufacturer's label on the ouside of the
drive, and it will only appear after you plug it in. Double check that
you have clicked on the correct drive.

|screenshot of Disk Utility application|

Once you're sure you have the right drive, click *Format Drive*. The
default *Scheme* of *Master Boot Record* is fine. Click *Format*, then
confirm by clicking *Format* again. Under the *Volumes* heading towards
the bottom of the right pane of *Disk Utility* click the large grey bar
that represents your newly-formatted drive and then click *Create
Partition* below.

|screenshot of the menu to create a new partition in the Disk Utility
application|

Give the new partition on your *Data Transfer Device* a descriptive name
like “Transfer Device” and check the *Encrypt underlying device* box,
then click *Create* to continue. You will now be prompted to create a
passphrase.

|screenshot of passphrase selection promprt in the Disk Utility
application|

You won't need to memorize this passphrase or type it more than a few
times, so feel free to make a good long one. Pick the *Remember forever*
option — this will save the passphrase securely on *Secure Viewing
Station*'s persistent volume. Click *Create* to continue. After a few
seconds, you new *Data Transfer Device* should be ready for use.

If you haven't already, make sure to label it.

--------------

Since a *Data Transfer Device* is used to move files from a *Journalist
Workstation* to the *Secure Viewing Station*, you'll also need to enter
the passphrase on each *Journalist Workstation* you use this *Data
Transfer Device* with. When you connect the *Data Transfer Device* to a
new *Journalist Workstation* for the first time, you'll be prompted to
enter the passphrase to unlock the encrypted disk.

|image of the disk unlock prompt on Tails|

Make sure to select the *Remember forever* option before entering your
passphrase. As in the *Disk Utility* application this will securely save
the passphrase on the persistent volume of that *Journalist
Workstation*, ensuring that you only ever have to type in the passphrase
once on any particular machine.

.. |Accessories icon| image:: images/icons/accessories.png
.. |Disk Utility icon| image:: images/icons/disk-utility.png
.. |screenshot of the Applications menu in Tails, highlighting Disk Utility| image:: images/screenshots/applications_accessories_disk-utility.png
.. |screenshot of Disk Utility application| image:: images/screenshots/disk-utility.png
.. |screenshot of the menu to create a new partition in the Disk Utility application| image:: images/screenshots/create-partition.png
.. |screenshot of passphrase selection promprt in the Disk Utility application| image:: images/screenshots/create-passphrase.png
.. |image of the disk unlock prompt on Tails| image:: images/screenshots/passphrase-keyring.png
