Back Up, Restore, Migrate
=========================

There are a number of reasons why you might want to backup and restore a
SecureDrop installation. Maintaining periodic backups is generally a good
practice to guard against data loss. In the event of hardware failure on
the SecureDrop servers, having a recent backup will enable you to redeploy
the system without changing Onion URLs, recreating journalist accounts,
or losing previous submissions from sources.

.. note:: Only the *Application Server* is backed up and restored, including
          historical submissions and both *Source Interface* and *Journalist
          Interface* URLs. The *Monitor Server* needs to be configured from
          scratch in the event of a hardware migration.

Minimizing Disk Use
-------------------

Since the backup and restore operations both involve transferring *all* of
your SecureDrop's stored submissions over Tor, the process can take a long time.
To save time and improve reliability for the transfers, take a moment to clean up
older submissions in the *Journalist Interface*. As a general practice, you should
encourage Journalists to delete regularly unneeded submissions from the *Journalist
Interface*.

.. tip:: Although it varies, the average throughput of a Tor Hidden Service is
         about 150 kB/s, or roughly 4 hours for 2GB. Plan your backup and
         restore accordingly.

You can use the following command to determine the volume of submissions
currently on the *Application Server*: log in over SSH and run
``sudo du -sh /var/lib/securedrop/store``.

.. note:: Submissions are deleted asynchronously and one at a time, so if you
          delete a lot of submissions through the *Journalist Interface*, it may
          take a while for all of the submissions to actually be
          deleted. SecureDrop uses ``srm`` to securely erase files, which takes
          significantly more time than normal file deletion. You can monitor the
          progress of queued deletion jobs with ``sudo tail -f
          /var/log/securedrop_worker/err.log``.

If you find you cannot perform a backup or restore due to this constraint,
and have already deleted old submissions from the *Journalist Interface*,
contact us through the `SecureDrop Support Portal`_.

.. _SecureDrop Support Portal: https://securedrop-support.readthedocs.io/en/latest/

Backing Up
----------

Open a **Terminal** on the *Admin Workstation* and ``cd`` to your clone
of the SecureDrop git repository (usually ``~/Persistent/securedrop``).
Ensure you have a tagged SecureDrop release checked out, version 0.4 or
later. (You can run ``git describe --exact-match`` to verify that you have the
right source checked out.)

.. note:: The backups are stored in the *Admin Workstation* persistent volume.
          **Verify that you have enough space to store the backups
          before running the backup command.**

          You can use the ``du`` command described earlier to get the
          approximate size of the backup file (since the majority of the backup
          archive is the stored submissions), and Tails' **Disks** utility to
          see how much free space you have on your persistent volume.

Check Connectivity
''''''''''''''''''

First, verify that your *Admin Workstation* is able to run Ansible and connect to
the SecureDrop servers.

.. code:: sh

   ssh app uptime

If this command fails (usually with an error like "SSH Error: data could not be
sent to the remote host. Make sure this host can be reached over ssh"), you need
to debug your connectivity before proceeding further. Make sure:

* Ansible is installed
* the *Admin Workstation* is connected to the Internet
* Tor starts successfully
* the ``HidServAuth`` values from ``install_files/ansible-base/app-ssh-aths``
  and ``install_files/ansible-base/mon-ssh-aths`` are in Tails at
  ``/etc/tor/torrc``

(If Ansible is not installed, or the ``HidServAuth`` values are missing
or incorrect, see :doc:`configure_admin_workstation_post_install` for detailed
instructions.)

Create the Backup
'''''''''''''''''

When you are ready to begin the backup, run

.. code:: sh

   ./securedrop-admin backup

The backup action will display itemized progress as the backup is created.
Run time will vary depending on connectivity and the number of submissions
saved on the *Application Server*.

When the backup action is complete, the backup will be stored as a compressed
archive in ``install_files/ansible-base``. The filename will begin ``sd-backup``
followed by a timestamp of when the backup was initiated, and end with
``.tar.gz``. You can find the full path to the backup archive in the output
of backup action.

.. warning:: The backup file contains sensitive information! It should only
             be stored on the *Admin Workstation*, or on a
             :doc:`dedicated encrypted backup USB <backup_workstations>`.

Restoring
---------

Prerequisites
'''''''''''''

The process for restoring a backup is very similar to the process of creating
one. As before, boot the *Admin Workstation* and ``cd`` to the
SecureDrop repository. Ensure that you have SecureDrop 0.4 or later
checked out.

The restore command expects to find a ``.tar.gz`` backup archive in
``install_files/ansible-base`` under the SecureDrop repository root directory.
If you are using the same *Admin Workstation* to do a restore from a previous
backup, it should already be there because it was placed there by the backup
command. Otherwise, you should copy the backup archive that you wish to restore to
``install_files/ansible-base``.

.. note:: The backup strategy used for SecureDrop versions prior to 0.3.7
          created encrypted archives with the extension ``.zip.gpg``.
          You can safely remove those files once you've created the ``.tar.gz``
          backup archive described in this guide.

Restoring From a Backup File
''''''''''''''''''''''''''''

To perform a restore, you must already have a backup archive. Provide its
filename in the following command:

.. code:: sh

   ./securedrop-admin restore sd-backup-2017-07-22--01-06-25.tar.gz

Make sure to replace ``sd-backup-2017-07-22--01-06-25.tar.gz`` with the filename
for your backup archive. The backup archives are located in
``install_files/ansible-base``.

Once the restore is done, the *Application Server* will use the original
*Source Interface* and *Journalist Interface* Onion URLs. You will need
to update the corresponding files on the *Admin Workstation*:

* ``app-source-ths``
* ``app-journalist-aths``
* ``app-ssh-aths``

The Onion URLs above can be fetched using the installer:

.. code:: sh

   ./securedrop-admin install

Then rerun ``./securedrop-admin tailsconfig`` to update the *Admin Workstation*
to use the restored Onion URLs again. See :doc:`configure_admin_workstation_post_install`
for detailed instructions.

Migrating
---------

Moving a SecureDrop installation to new hardware consists of

  1. *Backing up* the existing installation;
  2. *Installing* the same version of SecureDrop on the new hardware;
  3. *Restoring* the backup to the new installation.
