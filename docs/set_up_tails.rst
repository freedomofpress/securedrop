.. _set_up_tails:

Create Tails USBs
=================

`Tails <https://tails.boum.org>`__ is a privacy-enhancing live operating
system that runs on removable media, such as a DVD or a USB stick. It
sends all your Internet traffic through Tor, does not touch your
computer's hard drive, and securely wipes unsaved work on shutdown.

Most of the work of installing, administering, and using SecureDrop is
done from computers using Tails, so the first thing you need to do is
set up several USB drives with the Tails operating system. To get
started, you'll need two Tails drives: one for the *Admin Workstation*
and one for the *Secure Viewing Station*. :doc:`Later <onboarding>`,
you'll set up a bunch more Tails drives for your journalists and
backups, but for now you just need two.

As soon as you create a new Tails drive, *label it immediately*. USB
drives all look alike and you're going to be juggling a whole bunch of
them throughout this installation. Label immediately. Always.

.. _setup_install_tails:

Install Tails
-------------

We recommend creating an initial Tails Live DVD or USB, and then using
that to create additional Tails drives with the *Tails Installer*, a
special program that is only available from inside Tails. All of your
Tails drives will need persistence: a way of safely saving files and so
on between reboots. *It is only possible to set up persistence on USB
drives which were created via the Tails Installer*.

The `Tails website <https://tails.boum.org/>`__ has detailed and
up-to-date instructions on how to download and verify Tails, and how to
create a bootable Tails USB drive. Follow the instructions at these
links and then return to this page:

-  `Download and verify the Tails
   .iso <https://tails.boum.org/install/download/index.en.html>`__
-  `Install onto a USB
   drive <https://tails.boum.org/install/index.en.html>`__

You will need to create 3 Tails USBs to perform the SecureDrop installation:

#. A "master" Tails USB, which you will create by copying a Tails .iso
   onto a USB drive, using one of the techniques outlined in the Tails
   documentation. This Tails USB is only used for creating other Tails
   USBs with the **Tails Installer**.
#. The *Secure Viewing Station* Tails USB.
#. The *Admin Workstation* Tails USB.

.. tip:: This process will take some time, most of which will be spent
	 waiting around. Once you have the "master" copy of Tails, you
	 have to boot it, create another Tails drive with the **Tails
	 Installer**, shut down, and boot into the new Tails USB to
	 complete the next step of setting up the persistence - for
	 each additional Tails USB.

.. note:: Tails doesn't always completely shut down and reboot
	  properly when you click "restart", so if you notice a
	  significant delay, you may have to manually power off and
	  restart your computer for it to work properly.

Enable Persistent Storage
-------------------------

Creating an encrypted persistent volume will allow you to securely save
information and settings in the free space that is left on your Tails
drive. This information will remain available to you even if you reboot
Tails. (Tails securely erases all other data on every shutdown.)

You will need to create a persistent storage on each Tails drive, with a
unique passphrase for each.

Please use the instructions on the `Tails website
<https://tails.boum.org/doc/first_steps/persistence/index.en.html>`__
to make the persistent volume on each Tails drive you create. When
creating the persistence volume, you will be asked to select from a
list of features, such as 'Personal Data'. You should enable **all** features by
selecting each item in the list.

Some other things to keep in mind:

-  Right now, you need to create a persistent volume on both the *Admin
   Workstation* Tails drive and the *Secure Viewing Station* Tails
   drive.

-  Each Tails persistent volume should have an unique and complex
   passphrase that's easy to write down or remember. We recommend using
   `Diceware
   passphrases.
   <https://theintercept.com/2015/03/26/passphrases-can-memorize-attackers-cant-guess/>`__

-  Each journalist will need their own Tails drive with their own
   persistent volume secured with their own passphrase — but :doc:`that comes
   later <onboarding>`.

-  Journalists and admins will eventually need to remember these
   passphrases. We recommend using `spaced-repetition
   <https://en.wikipedia.org/wiki/Spaced_repetition>`__  to memorize
   Diceware passphrases.

.. warning:: Make sure that you never use the *Secure Viewing Station*
	     Tails drive on a computer connected to the Internet or a
	     local network. This Tails drive will only be used on the
	     air-gapped *Secure Viewing Station*.
