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

.. note:: The backup and restore operations both involve transferring *all* of
          your SecureDrop's stored submissions over Tor. Since Tor is very slow,
          backups and restores can take a long time. For example, in our testing
          we found that backing up or restoring an instance with 2GB of stored
          submissions took 2-6 hours, depending on the speed of the connection
          to the Tor Hidden Service (which varies widely depending on a number
          of complex factors that you should not attempt to manipulate, because
          in doing so you could potentially compromise your anonymity).

          As a result, it is possible for you to have so many saved submissions
          that performing a backup or restore, while possible, is infeasible -
          it could take days or weeks to transfer everything over Tor.

          You can get a sense of the total size of your saved submissions by
          SSHing to the *App Server* and running ``sudo du -sh
          /var/lib/securedrop/store``. Empirically, the average sustained
          throughput of a Tor Hidden Service seems to average around 150 kB/s,
          so you can use that to estimate the amount of time it will take to
          transfer a backup which includes all of your saved submissions.

          If you find you cannot perform a backup or restore due to this
          constraint, we recommend taking the following steps, in order:

          1. Use the Document Interface to delete unnecessary submissions before
             performing a backup. It is generally a best practice to minimize
             the number of submissions stored on the *App Server* - if possible,
             you should delete them from the App Server after transferring them
             to the Secure Viewing Station, optionally retaining a copy on
             encrypted cold storage if the contents of the submissions are worth
             keeping.
          2. If that doesn't work, or you are still having trouble, contact us
             through the `SecureDrop Support Portal`_.

.. _SecureDrop Support Portal: https://securedrop-support.readthedocs.io/en/latest/

Backups and restores must be performed from an Admin Workstation, so to get
started, boot your Admin Workstation with persistence enabled.

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

Now you can run the production Ansible playbook with the ``backup`` tag to
perform the backup:

.. code:: sh

   cd install_files/ansible-base
   ansible-playbook -i inventory -t backup securedrop-prod.yml

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
one. As before, get started by booting the Admin Workstation, ``cd``'ing to the
SecureDrop repository, and ensuring that you have SecureDrop 0.3.7 or later
checked out.

The restore role expects to find a ``.tar.gz`` backup archive in
``install_files/ansible-base`` under the SecureDrop repository root directory.
If you are using the same Admin Workstation to do a restore from a previous
backup, it should already be there because it was placed there by the backup
role. Otherwise, you should copy the backup archive that you wish to restore to
``install_files/ansible-base``.

Once you have moved the backup archive to the correct location, copy the backup
archive filename (just the filename, not the full path). Open
``prod-specific.yml`` in a text editor and add a line that defines
``restore_file`` as the backup archive filename, e.g.

.. code:: yaml

   restore_file: "<your backup archive filename>"

There is an example and explanatory comment at the end of ``prod-specific.yml``
to help you. Make sure you save your changes to ``prod-specific.yml`` before
continuing.

Run the restore Ansible role
''''''''''''''''''''''''''''

To perform a restore, simply run the *same* command that you ran to perform a
backup:

.. code:: sh

   cd install_files/ansible-base
   ansible-playbook -i inventory -t backup securedrop-prod.yml

This actually performs a backup, followed by a restore. A backup is done before
the restore as an emergency precaution, to ensure you can recover the server in
case something goes wrong with the restore.

Once the restore is done, the Ansible playbook will fetch the Tor HidServAuth
credentials for the various Authenticated Tor Hidden Services (ATHS) back to the
Admin Workstation. This synchronizes the state on the Admin Workstation with the
state of the restored server. You should re-run the Tails custom configuration
script (``tails_files/install.sh``, see
:doc:`configure_admin_workstation_post_install` for detailed instructions).

.. warning:: Once the restore has completed successfully, **be sure to remove**
             ``restore_file`` from ``prod-specific.yml``. Ansible checks for
             this variable in order to decide whether to run the restore. If you
             re-run the ``securedrop-prod.yml`` playbook at a later date (for
             example, to upgrade SecureDrop), you could overwrite or otherwise
             damage your existing SecureDrop installation by accidentally
             repeating the restore (which restores the state of your SecureDrop
             from an earlier date in the past).
