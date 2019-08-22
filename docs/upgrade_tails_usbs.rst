Updating Tails USBs
===================

There are 3 components of SecureDrop that use Tails USBs:

  #. The *Admin Workstation* (allowed to connect to the Internet)
  #. The *Journalist Workstation* (allowed to connect to the Internet)
  #. The *Secure Viewing Station* (airgapped, never allowed to connect to any network)

You are responsible for keeping your Tails USBs updated. This guide will
explain that process.

One-Click Updates
-----------------

For the Internet-connected Tails workstations (the *Admin Workstation* and
the *Journalist Workstation*), you'll see a notification when a new version
of Tails is available. We recommend that you :ref:`back up your existing
configuration<Step 1>` and upgrade as soon as possible.

|Upgrade Notification|

It usually takes some time for updates to download, so keep that in mind when choosing when to upgrade.

.. |Upgrade Notification| image:: images/tails_upgrade_notification.png


Manual Updates
--------------

However, because the *Secure Viewing Station (SVS)* is airgapped, it cannot
receive upgrade notifications, so it will need to be updated manually.

.. important:: 
        The *SVS* stores some of SecureDrop's most sensitive data (decrypted submissions, the SecureDrop Application private key), so we **strongly** encourage you to manually upgrade the *SVS* whenever a new version of Tails is released.

The Tails project releases updates `every 6 weeks`_. Occasionally they
release a new version ahead of the normal cycle in order to address a
security issue. For regular Tails OS and security information, check out the
Tails `Security page`_ and subscribe to the Tails RSS/Atom feed.

.. _every 6 weeks: https://tails.boum.org/support/faq/index.en.html
.. _Security page: https://tails.boum.org/security/index.en.html


Tails Manual Update Process at a Glance
----------------------------------------

The process for manually updating a Tails workstation is:

  #. Recommended: :ref:`Make a backup of the Tails workstation USB that you intend to upgrade<Step 1>`. For simplicity, we'll refer to the workstation you want to upgrade as the *Secure Viewing Station*, although this process would work on any Tails USB.
  #. Install the :ref:`latest version of Tails<Step 2>` on your *primary Tails USB*.
  #. Use the primary Tails USB to :ref:`perform a manual update of the Secure Viewing Station<Step 3>` USB on an offline (airgapped) machine.

Prerequisites
-------------

You will need:

  #. Your Admin Workstation computer
  #. A *primary Tails USB* stick (you may still have one; it was used to create the Admin Workstation, Secure Viewing Station, and Journalist Workstation Tails USBs during the initial SecureDrop Install process)
  #. Your *existing Tails USBs* that you want to update manually (*Secure   Viewing Station*, optionally *Admin Workstation* and *Journalist Workstation*)
  #. A *backup USB stick* or other storage device to back up the data on your existing Tails USBs
  #. Your airgapped *Secure Viewing Station* computer

.. _Step 1:

1. Back up existing Tails workstation(s)
----------------------------------------

`Follow the docs`_ to back up your existing Tails workstation(s).

.. _Follow the docs: https://docs.securedrop.org/en/stable/backup_workstations.html

.. _Step 2:

2. Get the latest version of Tails
----------------------------------

If you have an existing *primary Tails USB*, boot into it on your Admin
Workstation computer and follow the graphical updater prompts that guide you through the `automatic update process`_.

Alternatively, you can also download and `install the newest version of Tails from scratch`_ (as you did when you first installed SecureDrop), being sure to verify the checksums of any files you download. This may be faster if your *primary Tails USB* has not been updated in a while.

.. _automatic update process: https://tails.boum.org/doc/first_steps/upgrade/index.en.html

.. _install the newest version of Tails from scratch: https://docs.securedrop.org/en/stable/set_up_tails.html#install-tails

.. _Step 3:

3. Perform airgapped update of the SVS
--------------------------------------

In this step, we will use the up-to-date *primary Tails USB* to upgrade our
*Secure Viewing Station* Tails USB.

.. warning::
        The entire Secure Viewing Station is designed to be airgapped, so
        the SVS Tails USB should **never** be plugged into a computer with
        a network connection.

        Use the Secure Viewing Station computer to perform the steps in this
        section.

Plug your primary Tails USB into the Secure Viewing Station computer and boot
into Tails.

You can then perform the `manual upgrade steps`_.

.. _manual upgrade steps: https://tails.boum.org/upgrade/clone-overview/index.en.html


If you encounter issues
-----------------------

If you run into issues, you can always restore your data from the Backup
device following the instructions
`here <upgrade_to_tails_2x.html#restore-data-from-the-backup-device>`__.

If you continue to have problems, you can contact us through the
`SecureDrop Support Portal`_.

.. _SecureDrop Support Portal: https://securedrop-support.readthedocs.io/en/latest/

