Backup and Restore SecureDrop
=============================

There are a number of reasons why you might want to backup and restore your SecureDrop.
You may want to move an existing SecureDrop installation to new hardware.
Performing such a migration consists of:

  1. *Backup* the existing installation.
  2. Do a new install of the same version of SecureDrop on the new hardware.
  3. *Restore* the backup to the new installation.

Maintaining periodic backups are generally a good practice to guard against data loss.
In the event of hardware failure on the SecureDrop servers, having a recent backup
will enable you to redeploy the system without changing Onion URLs, recreating
Journalist accounts, or losing historical submissions from sources.

.. note:: Currently only the Application Server is backed up and restored,
          including historical submissions and Source and Journalist Interface URLs.
          The Monitor Server will be configured from scratch in the event of a
          hardware migration.

Minimizing disk space
---------------------

Since the backup and restore operations both involve transferring *all* of
your SecureDrop's stored submissions over Tor, the process can take a long time.
To save time and improve reliability for the transfers, take a moment to clean up
older submissions in the Journalist Interface. As a general practice, you should
encourage your Journalists to delete submissions from the Journalist Interface
regularly.

.. tip:: The throughput of a Tor Hidden Service seems to average around 150 kB/s,
         or roughly 4 hours for 2GB. Plan your backup and restore accordingly.

You can use the following command to determine the volume of submissions
currently on the *Application Server* by SSHing in and running
``sudo du -sh /var/lib/securedrop/store``.

.. note:: Submissions are deleted asynchronously and one at a time, so if you
          delete a lot of submissions through the Journalist Interface, it may
          take a while for all of the submissions to actually be deleted. This
          is especially true because SecureDrop uses ``srm`` to securely erase
          file submissions, which takes significantly more time than normal file
          deletion. You can monitor the progress of queued deletion jobs with
          ``sudo tail -f /var/log/securedrop_worker/err.log``.

If you find you cannot perform a backup or restore due to this
constraint, and have already deleted old submissions from the Journalist Interface,
contact us through the `SecureDrop Support Portal`_.

.. _SecureDrop Support Portal: https://securedrop-support.readthedocs.io/en/latest/

Backing Up
----------

Open a **Terminal** on the *Admin Workstation* and ``cd`` to your clone of the
SecureDrop git repository (usually ``~/Persistent/securedrop``). Ensure you have
SecureDrop version 0.4 or later checked out (you can run ``git describe
--exact-match`` to see what Git tag you've checked out).

.. note:: The backups are stored in the *Admin Workstation*'s persistent volume.
          **You should verify that you have enough space to store the backups
          before running the backup command.**

          You can use the ``du`` command described earlier to get the
          approximate size of the backup file (since the majority of the backup
          archive is the stored submissions), and you can use Tails' **Disks**
          utility to see how much free space you have on your persistent volume.

Check connectivity
''''''''''''''''''

First, verify that your *Admin Workstation* is able to run Ansible and connect to
the SecureDrop servers.

.. code:: sh

   ssh app uptime

If this command fails (usually with an error like "SSH Error: data could not be
sent to the remote host. Make sure this host can be reached over ssh"), you need
to debug your connectivity before proceeding further. Make sure:

* Ansible is installed. If it is not, see
  :doc:`configure_admin_workstation_post_install` for detailed instructions.

* The *Admin Workstation* is connected to the Internet.
* Tor started successfully.
* The ``HidServAuth`` values from ``app-ssh-aths`` and ``mon-ssh-aths`` are in
  Tails' ``/etc/tor/torrc``. If they are not, again, see 
  :doc:`configure_admin_workstation_post_install` for detailed instructions.

Create the backup
'''''''''''''''''

Run:

.. code:: sh

   ./securedrop-admin backup

The backup action will display itemized progress as the backup is created.
Run time will vary depending on the number of submissions saved on
the *Application Server*.

When the backup action is complete, the backup will be stored as a tar archive in
``install_files/ansible-base``. The filename will start with ``sd-backup``, have
a timestamp of when the backup was initiated, and end with ``.tar.gz``. You can
find the full path to the backup archive in the output of backup action.

.. warning:: The backup file contains sensitive information! It should only
             be stored on the *Admin Workstation*, or on a
             :doc:`dedicated encrypted backup USB <backup_workstations>`.

Restoring
---------

Prerequisites
'''''''''''''

The process for restoring a backup is very similar to the process of creating
one. As before, to get started, boot the *Admin Workstation*, ``cd`` to the
SecureDrop repository, and ensure that you have SecureDrop 0.4 or later
checked out.

The restore role expects to find a ``.tar.gz`` backup archive in
``install_files/ansible-base`` under the SecureDrop repository root directory.
If you are using the same *Admin Workstation* to do a restore from a previous
backup, it should already be there because it was placed there by the backup
role. Otherwise, you should copy the backup archive that you wish to restore to
``install_files/ansible-base``.

.. note:: The backup strategy used for SecureDrop versions prior to 0.3.7
          created encrypted archives with the extension ``.zip.gpg``.
          You can safely remove those files once you've created the ``.tar.gz``
          backup archive described in this guide.

Restoring from a backup file
''''''''''''''''''''''''''''

To perform a restore, you must already have a backup archive. Provide its
filename in the following command:

.. code:: sh

   ./securedrop-admin restore sd-backup-2017-07-22--01-06-25.tar.gz

Make sure to replace ``sd-backup-2017-07-22--01-06-25.tar.gz`` with the filename
for your backup archive. The backup archives are located in
``install_files/ansible-base``.

Once the restore is done, the Application Server will use the original Source and
Journalist Interface Onion URLs. You will need to update the corresponding
files on the Admin Workstation:

.. todo:: We really should automate this process for Admins.

* ``app-source-ths``
* ``app-journalist-aths``
* ``app-ssh-aths``

Then rerun ``./securedrop-admin tailsconfig`` to update the Admin Workstation
to use the restored Onion URLs again. See :doc:`configure_admin_workstation_post_install`
for detailed instructions.
