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

.. note:: The backup and restore functionality described in this guide was introduced
          in SecureDrop 0.3.7. Prior versions of SecureDrop included a less featureful
          backup process. Make sure you have upgraded to SecureDrop 0.3.7 or greater
          before continuing.

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
SecureDrop version 0.3.7 or later checked out (you can run ``git describe
--exact-match`` to see what Git tag you've checked out).

.. note:: The backups are stored in the Admin Workstation's persistent volume.
          **You should verify that you have enough space to store the backups
          before running the backup command.**

          You can use the ``du`` command described earlier to get the
          approximate size of the backup file (since the majority of the backup
          archive is the stored submissions), and you can use Tails' **Disks**
          utility to see how much free space you have on your persistent volume.

Check connectivity
''''''''''''''''''

First, verify that your Admin Workstation is able to run Ansible and connect to
the SecureDrop servers.

.. code:: sh

   cd install_files/ansible-base
   ansible -i inventory -u <SSH username> -m ping all

.. tip:: If you forgot your SSH username, it is the value of the ``ssh_users``
         variable in ``prod-specific.yml``.

If this command fails (usually with an error like "SSH Error: data could not be
sent to the remote host. Make sure this host can be reached over ssh"), you need
to debug your connectivity before proceeding further. Make sure:

* Ansible is installed (``which ansible`` should return a path instead of "not found").

  * Ansible should be automatically installed by the Tails auto-configuration
    for SecureDrop. If it is not, you probably need to re-run
    ``tails_files/install.sh``. See
    :doc:`configure_admin_workstation_post_install` for detailed instructions).

* The Admin Workstation is connected to the Internet.
* Tor started successfully.
* The ``HidServAuth`` values from ``app-ssh-aths`` and ``mon-ssh-aths`` are in
  Tails' ``/etc/tor/torrc``.

  * Tor should be automatically configured to connect to the authenticated Tor
    Hidden Services by the Tails auto-configuration for SecureDrop. If it is
    not, you probably need to re-run ``tails_files/install.sh``. See
    :doc:`configure_admin_workstation_post_install` for detailed instructions).

Run the backup Ansible role
'''''''''''''''''''''''''''

Now you can run the production Ansible playbook with special flags tag to
perform the backup:

.. code:: sh

   cd install_files/ansible-base
   ansible-playbook -i inventory -u <SSH username> -t backup securedrop-prod.yml -e perform_backup=true

.. todo:: Test this on a real Admin Workstation

The backup role will print out the results of its tasks as it completes them.
You can expect the ``fetch the backup file`` step to take a long time,
especially if you have a lot of saved submissions.

When the backup role is complete, the backup will be stored as a tar archive in
``ansible-base``. The filename will start with ``sd-backup``, have a timestamp
of when the backup was initiated, and end with ``.tar.gz``. You can find the
full path to the backup archive in the output of the ``fetch the backup file``
task, as the value of the variable ``"dest"`` in the results dictionary.

.. warning:: The backup file contains sensitive information! Be careful where you
             copy it.

Restoring
---------

Prerequisites
'''''''''''''

The process for restoring a backup is very similar to the process of creating
one. As before, to get started, boot the Admin Workstation, ``cd`` to the
SecureDrop repository, and ensure that you have SecureDrop 0.3.7 or later
checked out.

The restore role expects to find a ``.tar.gz`` backup archive in
``install_files/ansible-base`` under the SecureDrop repository root directory.
If you are using the same Admin Workstation to do a restore from a previous
backup, it should already be there because it was placed there by the backup
role. Otherwise, you should copy the backup archive that you wish to restore to
``install_files/ansible-base``.

.. note:: The backup strategy used for SecureDrop versions prior to 0.3.7
          created encrypted archives with the extension ``.zip.gpg``.
          You can safely remove those files once you've created the ``.tar.gz``
          backup archive described in this guide.

Run the restore Ansible role
''''''''''''''''''''''''''''

To perform a restore, simply run the *same* command that you ran to perform a
backup:

.. code:: sh

   cd install_files/ansible-base
   ansible-playbook -i inventory -t backup securedrop-prod.yml -e restore_file="<your backup archive filename>"

This actually performs a backup, followed by a restore. A backup is done before
the restore as an emergency precaution, to ensure you can recover the server in
case something goes wrong with the restore.

Once the restore is done, the Ansible playbook will fetch the Tor HidServAuth
credentials for the various Authenticated Tor Hidden Services (ATHS) back to the
Admin Workstation. This synchronizes the state on the Admin Workstation with the
state of the restored server. You should re-run the Tails custom configuration
script (``tails_files/install.sh``, see
:doc:`configure_admin_workstation_post_install` for detailed instructions).
