How to manually upgrade Tails
=============================


Prerequisites
-------------

You will need:

#. The Tails USB drive to be upgraded (the *Target Drive*).
#. A blank USB drive to transfer the new version of Tails (the *Install Drive*).
#. (Optional, but **strongly recommended**): A blank USB drive to store a backup of the *Target Drive*, in case something goes wrong during the upgrade process (the *Backup Drive*).

   - If you will be upgrading multiple *Target Drives*, note that you will need one *Backup Drive* for each *Target Drive*.

.. tip:: As always, we recommend using USB 3 drives and checking that you are using USB 3 compatible ports on your workstations. USB 3 is significantly faster than USB 2, which minimizes your waiting time during many steps of the upgrade process.


Overview
--------

At a high level, the steps to manually upgrade Tails are:

#. (Optional) Backup the *Target Drive* onto the *Backup Drive*.
#. Download and verify the new version of Tails.
#. Copy the new version of Tails onto the *Install Drive*.
#. Boot the new version of Tails from the *Install Drive*.
#. Insert the *Target Drive* into the computer booted from the *Install Drive*.
#. Use the *Tails Installer* with the "Upgrade by cloning" option to upgrade the *Target Drive* to the newer version of Tails running on the *Install Drive*.
#. Once the *Target Drive* is upgraded, reboot into the version of Tails running on the *Target Drive*. Verify that the upgrade was successful and you can still access your persistent data.

To get started, click **Next** for instructions on backing up the *Target Drive*.

