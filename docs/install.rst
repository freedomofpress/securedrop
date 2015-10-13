Installing SecureDrop
=====================

.. raw:: html

   <!-- START doctoc generated TOC please keep comment here to allow auto update -->

.. raw:: html

   <!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

**Table of Contents** *generated with
`DocToc <https://github.com/thlorenz/doctoc>`__*

-  `Before you begin <#before-you-begin>`__
-  `Set up Tails USB sticks <#set-up-tails-usb-sticks>`__

   -  `Installing Tails <#installing-tails>`__
   -  `Enabling Persistence Storage on
      Tails <#enabling-persistence-storage-on-tails>`__

-  `Set up the Secure Viewing
   Station <#set-up-the-secure-viewing-station>`__
-  `Create a GPG key for the SecureDrop
   application <#create-a-gpg-key-for-the-securedrop-application>`__
-  `Import GPG keys for journalists with access to
   SecureDrop <#import-gpg-keys-for-journalists-with-access-to-securedrop>`__
-  `Set up Admin Tails USB and
   Workstation <#set-up-admin-tails-usb-and-workstation>`__
-  `Start Tails and enable the persistent
   volume <#start-tails-and-enable-the-persistent-volume>`__
-  `Download the SecureDrop
   repository <#download-the-securedrop-repository>`__
-  `Passphrase Database <#passphrase-database>`__
-  `Set up the Network Firewall <#set-up-the-network-firewall>`__
-  `Set up the Servers <#set-up-the-servers>`__
-  `Install the SecureDrop
   application <#install-the-securedrop-application>`__
-  `Install Ansible <#install-ansible>`__
-  `Set up SSH keys for the Admin <#set-up-ssh-keys-for-the-admin>`__
-  `Gather the required
   information <#gather-the-required-information>`__
-  `Install SecureDrop <#install-securedrop>`__
-  `Set up access to the authenticated hidden
   services <#set-up-access-to-the-authenticated-hidden-services>`__
-  `Set up SSH host aliases <#set-up-ssh-host-aliases>`__
-  `Set up two-factor authentication for the
   Admin <#set-up-two-factor-authentication-for-the-admin>`__
-  `Create users for the web
   application <#create-users-for-the-web-application>`__
-  `Finalizing the Installation <#finalizing-the-installation>`__
-  `Test the web application and
   connectivity <#test-the-web-application-and-connectivity>`__
-  `Additional testing <#additional-testing>`__

.. raw:: html

   <!-- END doctoc generated TOC please keep comment here to allow auto update -->

This guide outlines the steps required to install SecureDrop 0.3.x. If
you are looking to upgrade from version 0.2.1, please use the `migration
scripts </migration_scripts/0.3>`__ we have created.

Before you begin
----------------

Before you get started, you should familiarize yourself with the
`SecureDrop overview <./overview.md>`__, `specific
terminology <./terminology.md>`__, and the description of
`roles <./roles.md>`__ involved in SecureDrop's operations. You may wish
to leave these open in other tabs as you work.

SecureDrop is a technical tool. It is designed to protect journalists
and sources, but no tool can guarantee safety. This guide will instruct
you in installing and configuring SecureDrop, but it does not explain
how to use it safely and effectively. Put another way: at the end of
this guide, you will have built a car; you will not know how to drive.
Make sure to review the `deployment
best-practices <deployment_practices.md>`__ to get the most out of your
new SecureDrop instance.

Installing SecureDrop is an extended manual process which requires a
bunch of preparation and equipment. You should probably set aside a day
to complete the install process. A successful install requires an
administrator with at-least basic familiarity with Linux, the GNU core
utilities and Bash shell. If you are not proficient in these areas, it
is strongly recommended that you contact the `Freedom of the Press
Foundation <https://securedrop.org/help>`__ for installation assistance.

Before you begin, you will need to assemble all the
`hardware <./hardware.md>`__ that you are going to use.

When running commands or editing configuration files that include
filenames, version numbers, usernames, and hostnames or IP addresses,
make sure it all matches your setup. This guide contains several words
and phrases associated with SecureDrop that you may not be familiar
with. It's recommended that you read our `Terminology
Guide </docs/terminology.md>`__ once before starting and keep it open in
another tab to refer back to.

You will also need the inventory of hardware items for the installation
listed in our `Hardware Guide </docs/hardware.md>`__.

Once you're familiar with SecureDrop, you've made your plan, your
organization is ready to follow-through and you have the required
hardware assembled before you, you're ready to begin.

Set up Tails USB sticks
-----------------------

`Tails <https://tails.boum.org>`__ is a privacy-enhancing live operating
system that runs on removable media, such as a DVD or a USB stick. It
sends all your Internet traffic through Tor, does not touch your
computer's hard drive, and securely wipes unsaved work on shutdown.

Most of the work of installing, administering, and using SecureDrop is
done from computers using Tails, so the first thing you need to do is
set up several USB drives with the Tails operating system. To get
started, you'll need two Tails drives: one for the *Admin Workstation*
and one for the *Secure Viewing Station*. `Later <./onboarding.md>`__,
you'll set up a bunch more Tails drives for your journalists and
backups, but for now you just need two.

As soon as you create a new Tails drive, *label it immediately*. USB
drives all look alike and you're going to be juggling a whole bunch of
them throughout this installation. Label immediately. Always.

Installing Tails
~~~~~~~~~~~~~~~~

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
   .iso <https://tails.boum.org/download/index.en.html>`__
-  `Install onto a USB
   drive <https://tails.boum.org/doc/first_steps/installation/index.en.html>`__

The current Tails signing key looks like this:

::

    pub   4096R/0xDBB802B258ACD84F 2015-01-18 [expires: 2017-01-11]
          Key fingerprint = A490 D0F4 D311 A415 3E2B  B7CA DBB8 02B2 58AC D84F
    uid                 [  full  ] Tails developers (offline long-term identity key) <tails@boum.org>
    uid                 [  full  ] Tails developers <tails@boum.org>
    sub   4096R/0x98FEC6BC752A3DB6 2015-01-18 [expires: 2017-01-11]
    sub   4096R/0x3C83DCB52F699C56 2015-01-18 [expires: 2017-01-11]

Note that this process will take some time because once you have one
copy of Tails, you have to create each additional Tails drive, shut
down, and boot into each one to complete the next step.

Also, you should be aware that Tails doesn't always completely shut down
and reboot properly when you click "restart", so if you notice a
significant delay, you may have to manually power off and restart your
computer for it to work properly.

Enabling Persistence Storage on Tails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating an encrypted persistent volume will allow you to securely save
information and settings in the free space that is left on your Tails
drive. This information will remain available to you even if you reboot
Tails. (Tails securely erases all other data on every shutdown.)

You will need to create a persistent storage on each Tails drive, with a
unique password for each.

Please use the instructions on the `Tails
website <https://tails.boum.org/doc/first_steps/persistence/index.en.html>`__
to make the persistent volume on each Tails drive you create.

When creating the persistence volume, you will be asked to select from a
list of features, such as 'Personal Data'. We recommend that you enable
**all** features.

Some other things to keep in mind:

-  Right now, you need to create a persistent volume on both the *Admin
   Workstation* Tails drive and the *Secure Viewing Station* Tails
   drive.

-  Each Tails persistent volume should have an unique and complex
   passphrase that's easy to write down or remember. We recommend using
   `Diceware
   passphrases. <https://theintercept.com/2015/03/26/passphrases-can-memorize-attackers-cant-guess/>`__.

-  Each journalist will need their own Tails drive with their own
   persistent volume secured with their own passphrase — but `that comes
   later <./onboarding.md>`__.

-  Journalists and admins will eventually need to remember these
   passphrases. We recommend using spaced-repetition to memorize
   Diceware passphrases.

**NOTE: Make sure that you never use the *Secure Viewing Station* Tails
drive on a computer connected to the Internet or a local network. This
Tails drive will only be used on the air-gapped *Secure Viewing
Station*.**

Set up the *Secure Viewing Station*
-----------------------------------

The *Secure Viewing Station* is the computer where journalists read and
respond to SecureDrop submissions. Once submissions are encrypted on the
*Application Server*, only the *Secure Viewing Station* has the key to
decrypt them. The *Secure Viewing Station* is never connected to the
internet or a local network, and only ever runs from a dedicated Tails
drive. Journalists download encrypted submittions using their
*Journalist Workstation*, copy them to a *Data Transfer Device* (a USB
drive or a DVD) and physically transfer the *Data Transfer Device* to
the *Secure Viewing Station*.

Since the *Secure Viewing Station* never uses a network connection or an
internal hard drive, we recommend that you physically remove any any
internal storage devices or networking hardware such as wireless cards
or Bluetooth adapters. If the machine has network ports you can't
physically remove, you should clearly cover these ports with labels
noting not to use them. For an even safer approach, fill a port with
epoxy to physically disable it. If you have questions about repurposing
hardware for the *Secure Viewing Station*, contact the `Freedom of the
Press Foundation <https://securedrop.org/help>`__.

You should have a Tails drive clearly labeled “SecureDrop Secure Viewing
Station”. If it's not labeled, label it right now, then boot it on the
*Secure Viewing Station*. After it loads, you should see a "Welcome to
Tails" screen with two options. Select *Yes* to enable the persistent
volume and enter your password, but do NOT click Login yet. Under 'More
Options,' select *Yes* and click *Forward*.

Enter an *Administration password* for use with this specific Tails
session and click *Login*. (NOTE: the *Administration password* is a
one-time password. It will reset every time you shut down Tails.)

Set up the *Data Transfer Device*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
drive. If you have a large team of journalists you may want to `create
several <./onboarding.md>`__ of these. Here we'll just walk through
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

Generate the *SecureDrop Application GPG Key*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a document or message is submitted to SecureDrop by a source, it is
automatically encrypted with the *SecureDrop Application GPG Key*. The
private part of this key is only stored on the *Secure Viewing Station*
which is never connected to the Internet. SecureDrop submissions can
only be decrypted and read on the *Secure Viewing Station*.

We will now generate the *SecureDrop Application GPG Key* key.

After booting up Tails on the *Secure Viewing Station*, you will need to
manually set the system time before you create the *SecureDrop
Application GPG Key*. To set the system time:

#. Right-click the time in the top menu bar and select *Adjust Date &
   Time.*
#. Click *Unlock* in the top-right corner of the dialog window and enter
   your temporary Tails administration password.
#. Set the correct time, region and city.
#. Click *Lock*, enter your temporary Tails administration password one
   more time and wait for the system time to update in the top panel.

Once that's done, follow the steps below to create the key.

-  Open a terminal |Terminal| and run ``gpg --gen-key``
-  When it says, ``Please select what kind of key you want``, choose
   ``(1) RSA and RSA (default)``
-  When it asks, ``What keysize do you want?`` type **``4096``**
-  When it asks, ``Key is valid for?`` press Enter to keep the default
-  When it asks, ``Is this correct?`` verify that you've entered
   everything correctly so far, and type ``y``
-  For ``Real name`` type: ``SecureDrop``
-  For ``Email address``, leave the field blank and press Enter
-  For ``Comment`` type
   ``[Your Organization's Name] SecureDrop Application GPG Key``
-  Verify that everything is correct so far, and type ``o`` for
   ``(O)kay``
-  It will pop up a box asking you to type a passphrase, but it's safe
   to click okay without typing one (since your persistent volume is
   encrypted, this GPG key is already protected)
-  Wait for your GPG key to finish generating

To manage GPG keys using the graphical interface (a program called
Seahorse), click the clipboard icon |gpgApplet| in the top right corner
and select "Manage Keys". You should see the key that you just generated
under "GnuPG Keys."

|My Keys|

Select the key you just generated and click "File" then "Export". Save
the key to the *Transfer Device* as ``SecureDrop.pgp``, and make sure
you change the file type from "PGP keys" to "Armored PGP keys" which can
be switched right above the 'Export' button. Click the 'Export' button
after switching to armored keys.

NOTE: This is the public key only.

| |My Keys|
| |My Keys|

You'll need to verify the fingerprint for this new key during the
``App Server`` installation. Double-click on the newly generated key and
change to the ``Details`` tab. Write down the 40 hexadecimal digits
under ``Fingerprint``. (Your GPG key fingerprint will be different than
what's in this photo.)

|Fingerprint|

Import GPG keys for journalists with access to SecureDrop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While working on a story, journalists may need to transfer some
documents or notes from the *Secure Viewing Station* to the journalist's
work computer on the corporate network. To do this, the journalists
should re-encrypt them with their own keys. If a journalist does not
already have a personal GPG key, he or she can follow the same steps
above to create one. The journalist should store the private key
somewhere safe; the public key should be stored on the *Secure Viewing
Station*.

If the journalist does have a key, transfer their public key from
wherever it is located to the *Secure Viewing Station*, using the
*Transfer Device*. Open the file manager |Nautilus| and double-click on
the public key to import it. If the public key is not importing, rename
the file to end in ".asc" and try again.

|Importing Journalist GPG Keys|

At this point, you are done with the *Secure Viewing Station* for now.
You can shut down Tails, grab the *admin Tails USB* and move over to
your regular workstation.

Set up Admin Tails USB and Workstation
--------------------------------------

Earlier, you should have created the *admin Tails USB* along with a
persistence volume for it. Now, we are going to add a couple more
features to the *admin Tails USB* to facilitate SecureDrop's setup.

If you have not switched to and booted the *admin Tails USB* on your
regular workstation, do so now.

Start Tails and enable the persistent volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After you boot the *admin Tails USB* on your normal workstation, you
should see a *Welcome to Tails* screen with two options. Select *Yes* to
enable the persistent volume and enter your password, but do NOT click
Login yet. Under 'More Options," select *Yes* and click *Forward*.

Enter an *Administration password* for use with this specific Tails
session and click *Login*. (NOTE: the *Administration password* is a
one-time password. It will reset every time you shut down Tails.)

After Tails is fully booted, make sure you're connected to the Internet
|Network| and that the Tor's Vidalia indicator onion |Vidalia| is green,
using the icons in the upper right corner.

Download the SecureDrop repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The rest of the SecureDrop-specific configuration is assisted by files
stored in the SecureDrop Git repository. We're going to be using this
again once SecureDrop is installed, but you should download it now. To
get started, open a terminal |Terminal|. You will use this Terminal
throughout the rest of the install process.

Start by running the following commands to download the git repository.

NOTE: Since the repository is fairly large and Tor can be slow, this may
take a few minutes.

.. code:: sh

    cd ~/Persistent
    git clone https://github.com/freedomofpress/securedrop.git

Before proceeding, verify the signed git tag for this release.

First, download the *Freedom of the Press Foundation Master Signing Key*
and verify the fingerprint.

::

    gpg --keyserver pool.sks-keyservers.net --recv-key B89A29DB2128160B8E4B1B4CBADDE0C7FC9F6818
    gpg --fingerprint B89A29DB2128160B8E4B1B4CBADDE0C7FC9F6818

The Freedom of the Press Foundation Master Signing Key should have a
fingerprint of "B89A 29DB 2128 160B 8E4B 1B4C BADD E0C7 FC9F 6818". If
the fingerprint does not match, fingerprint verification has failed and
you *should not* proceed with the installation. If this happens, please
contact us at securedrop@freedom.press.

Verify that the current release tag was signed with the master signing
key.

::

    cd securedrop/
    git checkout 0.3.5
    git tag -v 0.3.5

You should see 'Good signature from "Freedom of the Press Foundation
Master Signing Key"' in the output of ``git tag``. If you do not,
signature verification has failed and you *should not* proceed with the
installation. If this happens, please contact us at
securedrop@freedom.press.

Passphrase Database
~~~~~~~~~~~~~~~~~~~

We provide a KeePassX password database template to make it easier for
admins and journalists to generate strong, unique passphrases and store
them securely. Once you have set up Tails with persistence and have
cloned the repo, you can set up your personal password database using
this template.

You can find the template in
``/Persistent/securedrop/tails_files/securedrop-keepassx.xml`` within
the SecureDrop repository. Note that you will not be able to access your
passwords if you forget the master password or the location of the key
file used to protect the database.

To use the template:

-  Open the KeePassX program |KeePassX| which is already installed on
   Tails
-  Select ``File``, ``Import from...``, and ``KeePassX XML (*.xml)``
-  Navigate to the location of ``securedrop-keepassx.xml``, select it,
   and click ``Open``
-  Set a strong master password to protect the password database (you
   will have to write this down/memorize it)
-  Click ``File`` and ``Save Database As``
-  Save the database in the Persistent folder

Set up the Network Firewall
---------------------------

Now that you've set up your password manager, you can move on to setting
up the Network Firewall. You should stay logged in to your *admin Tails
USB*, but please go to our `Network Firewall
Guide </docs/network_firewall.md>`__ for instructions for setting up the
Network Firewall. When you are done, you will be sent back here to
continue with the next section.

Set up the Servers
------------------

Now that the firewall is set up, you can plug the *Application Server*
and the *Monitor Server* into the firewall. If you are using a setup
where there is a switch on the LAN port, plug the *Application Server*
into the switch and plug the *Monitor Server* into the OPT1 port.

Install Ubuntu Server 14.04 (Trusty) on both servers. This setup is
fairly easy, but please note the following:

-  Since the firewall is configured to give the servers a static IP
   address, you will have to manually configure the network with those
   values.
-  The hostname for the servers are, conventionally, ``app`` and
   ``mon``. Adhering to this isn't necessary, but it will make the rest
   of your install easier.
-  The username and password for these two servers **must be the same**.

For detailed instructions on installing and configuring Ubuntu for use
with SecureDrop, see our `Ubuntu Install
Guide </docs/ubuntu_config.md>`__.

When you are done, make sure you save the following information:

-  The IP address of the App Server
-  The IP address of the Monitor Server
-  The non-root user's name and password for the servers.

Before continuing, you'll also want to make sure you can connect to the
App and Monitor servers. You should still have the Admin Workstation
connected to the firewall from the firewall setup step. In the terminal,
verify that you can SSH into both servers, authenticating with your
password:

.. code:: sh

    ssh <username>@<App IP address>
    ssh <username>@<Monitor IP address>

Once you have verified that you can connect, continue with the
installation. If you cannot connect, check the firewall logs.

Install the SecureDrop application
----------------------------------

Install Ansible
~~~~~~~~~~~~~~~

You should still be on your admin workstation with your *admin Tails
USB*.

Next you need to install Ansible. To do this, you first need to update
your package manager's package lists to be sure you get the latest
version of Ansible. It should take a couple minutes.

::

    sudo apt-get update

Now, install Ansible by entering this command:

::

    sudo apt-get install ansible

Set up SSH keys for the Admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now that you've verified the code that's needed for installation, you
need to create an SSH key on the Admin Workstation. Initially, Ubuntu
has SSH configured to authenticate users with their password. This new
key will be copied to the *Application Server* and the *Monitor Server*,
and will replace the use of the password for authentication. Since the
Admin Live USB was set up with `SSH Client
persistence <https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html#index3h2>`__,
this key will be saved on the Admin Live USB and can be used in the
future to authenticate to the servers in order to perform administrative
tasks.

First, generate the new SSH keypair:

::

    $ ssh-keygen -t rsa -b 4096

You'll be asked to "enter file in which to save the key." Here you can
just keep the default, so type enter.

If you choose to passphrase-protect this key, you must use a strong,
diceword-generated, passphrase that you can manually type (as Tails'
pinentry will not allow you to copy and paste a passphrase). It is also
acceptable to leave the passphrase blank in this case.

Once the key has finished generating, you need to copy the public key to
both servers. Use ``ssh-copy-id`` to copy the public key to each server
in turn. Use the user name and password that you set up during Ubuntu
installation.

::

    $ ssh-copy-id <username>@<App IP address>
    $ ssh-copy-id <username>@<Mon IP address>

Verify that you are able to authenticate to both servers by running the
below commands (you will be prompted for the SSH password you just
created).

.. code:: sh

    ssh <username>@<App IP address> hostname
    ssh <username>@<Monitor IP address> hostname

Make sure to run the 'exit' command after testing each one.

Gather the required information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure you have the following information and files before
continuing:

-  The *App Server* IP address
-  The *Monitor Server* IP address
-  The SecureDrop application's GPG public key (from the *Transfer
   Device*)
-  The SecureDrop application's GPG key fingerprint
-  The email address that will receive alerts from OSSEC
-  The GPG public key and fingerprint for the email address that will
   receive the alerts
-  Connection information for the SMTP relay that handles OSSEC alerts.
   For more information, see the `OSSEC Alerts
   Guide </docs/ossec_alerts.md>`__.
-  The first username of a journalist who will be using SecureDrop (you
   can add more later)
-  The username of the system administrator
-  (Optional) An image to replace the SecureDrop logo on the *Source
   Interface* and *Document Interface*

   -  Recommended size: ``500px x 450px``
   -  Recommended format: PNG

Install SecureDrop
~~~~~~~~~~~~~~~~~~

From the base of the SecureDrop repo, change into the ``ansible-base``
directory:

::

    $ cd install_files/ansible-base

You will have to copy the following required files to
``install_files/ansible-base``:

-  SecureDrop Application GPG public key file
-  Admin GPG public key file (for encrypting OSSEC alerts)
-  (Optional) Custom header image file

The SecureDrop application GPG key should be located on your *Transfer
Device* from earlier. It will depend on the location where the USB stick
is mounted, but for example, if you are already in the ansible-base
directory, you can just run:

::

    $ cp /media/[USB folder]/SecureDrop.asc .

Or you may use the copy and paste capabilities of the file manager.
Repeat this step for the Admin GPG key and custom header image.

Now you must edit a couple configuration files. You can do so using
gedit, vim, or nano. Double-clicking will suffice to open them.

Edit the inventory file, ``inventory``, and update the default IP
addresses with the ones you chose for app and mon. When you're done,
save the file.

Edit the file ``prod-specific.yml`` and fill it out with values that
match your environment. At a minimum, you will need to provide the
following:

-  User allowed to connect to both servers with SSH: ``ssh_users``
-  IP address of the Monitor Server: ``monitor_ip``
-  Hostname of the Monitor Server: ``monitor_hostname``
-  Hostname of the Application Server: ``app_hostname``
-  IP address of the Application Server: ``app_ip``
-  The SecureDrop application's GPG public key:
   ``securedrop_app_gpg_public_key``
-  The SecureDrop application's GPG key fingerprint:
   ``securedrop_app_gpg_fingerprint``
-  GPG public key used when encrypting OSSEC alerts:
   ``ossec_alert_gpg_public_key``
-  Fingerprint for key used when encrypting OSSEC alerts:
   ``ossec_gpg_fpr``
-  The email address that will receive alerts from OSSEC:
   ``ossec_alert_email``
-  The reachable hostname of your SMTP relay: ``smtp_relay``
-  The secure SMTP port of your SMTP relay: ``smtp_relay_port``
   (typically 25, 587, or 465. Must support TLS encryption)
-  Email username to authenticate to the SMTP relay: ``sasl_username``
-  Domain name of the email used to send OSSEC alerts: ``sasl_domain``
-  Password of the email used to send OSSEC alerts: ``sasl_password``
-  The fingerprint of your SMTP relay (optional):
   ``smtp_relay_fingerprint``

When you're done, save the file and quit the editor.

Now you are ready to run the playbook! This will automatically configure
the servers and install SecureDrop and all of its dependencies.
``<username>`` below is the user you created during the Ubuntu
installation, and should be the same user you copied the SSH public keys
to.

::

    $ ansible-playbook -i inventory -u <username> -K --sudo securedrop-prod.yml

You will be prompted to enter the sudo password for the app and monitor
servers (which should be the same).

The Ansible playbook will run, installing SecureDrop plus configuring
and hardening the servers. This will take some time, and it will return
the terminal to you when it is complete. If an error occurs while
running the playbook, please submit a detailed `GitHub
issue <https://github.com/freedomofpress/securedrop/issues/new>`__ or
send an email to securedrop@freedom.press.

Once the installation is complete, the addresses for each Tor Hidden
Service will be available in the following files in
``install_files/ansible-base``:

-  ``app-source-ths``: This is the .onion address of the Source
   Interface
-  ``app-document-aths``: This is the ``HidServAuth`` configuration line
   for the Document Interface. During a later step, this will be
   automatically added to your Tor configuration file in order to
   exclusively connect to the hidden service.
-  ``app-ssh-aths``: Same as above, for SSH access to the Application
   Server.
-  ``mon-ssh-aths``: Same as above, for SSH access to the Monitor
   Server.

Update the inventory, replacing the IP addresses with the corresponding
onion addresses from ``app-ssh-aths`` and ``mon-ssh-aths``. This will
allow you to re-run the Ansible playbooks in the future, even though
part of SecureDrop's hardening restricts SSH to only being over the
specific authenticated Tor Hidden Services.

Set up access to the authenticated hidden services
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To complete setup of the Admin Workstation, we recommend using the
scripts in ``tails_files`` to easily and persistently configure Tor to
access these hidden services.

Navigate to the directory with these scripts and type these commands
into the terminal:

::

    cd ~/Persistent/securedrop/tails_files/
    sudo ./install.sh

Type the administration password that you selected when starting Tails
and hit enter. The installation process will download additional
software and then open a text editor with a file called
*torrc\_additions*.

Edit this file, inserting the *HidServAuth* information for the three
authenticated hidden services that you just received. You can
double-click or use the 'cat' command to read the values from
``app-document-aths``, ``app-ssh-aths`` and ``mon-ssh-aths``. This
information includes the address of the Document Interface, each
server's SSH daemon and your personal authentication strings, like in
the example below:

::

    # add HidServAuth lines here
    HidServAuth gu6yn2ml6ns5qupv.onion Us3xMTN85VIj5NOnkNWzW # client: user
    HidServAuth fsrrszf5qw7z2kjh.onion xW538OvHlDUo5n4LGpQTNh # client: admin
    HidServAuth yt4j52ajfvbmvtc7.onion vNN33wepGtGCFd5HHPiY1h # client: admin

An easy way to do this is to run ``cat *-aths`` from the
``install_files/ansible-base`` folder in a terminal window, and
copy/paste the output into the opened text editor.

When you are done, click *Save* and **close** the text editor. Once the
editor is closed, the install script will automatically resume.

Running ``install.sh`` sets up an initialization script that
automatically updates Tor's configuration to work with the authenticated
hidden services every time you login to Tails. As long as Tails is
booted with the persistent volume enabled then you can open the Tor
Browser and reach the Document Interface as normal, as well as connect
to both servers via secure shell. Tor's `hidden service
authentication <https://www.torproject.org/docs/tor-manual.html.en#HiddenServiceAuthorizeClient>`__
restricts access to only those who have the 'HidServAuth' values.

Set up SSH host aliases
~~~~~~~~~~~~~~~~~~~~~~~

This step is optional but makes it much easier to connect to and
administer the servers. Create the file ``/home/amnesia/.ssh/config``
and add a configuration following the scheme below, but replace
``Hostname`` and ``User`` with the values specific to your setup:

::

    Host app
      Hostname fsrrszf5qw7z2kjh.onion
      User <ssh_user>
    Host mon
      Hostname yt4j52ajfvbmvtc7.onion
      User <ssh_user>

Now you can simply use ``ssh app`` and ``ssh mon`` to connect to each
server, and it will be stored in the Tails Dotfiles persistence.

Set up two-factor authentication for the Admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As part of the SecureDrop installation process, you will need to set up
two-factor authentication on the App Server and Monitor Server using the
Google Authenticator mobile app.

After your torrc has been updated with the HidServAuth values, connect
to the App Server using ``ssh`` and run ``google-authenticator``. Follow
the instructions in `our Google Authenticator
guide </docs/google_authenticator.md>`__ to set up the app on your
Android or iOS device.

To disconnect enter the command ``exit``. Now do the same thing on the
Monitor Server. You'll end up with an account for each server in the
Google Authenticator app that generates two-factor codes needed for
logging in.

Create users for the web application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now SSH to the App Server, ``sudo su``, cd to /var/www/securedrop, and
run ``./manage.py add_admin`` to create the first admin user for
yourself. Make a password and store it in your KeePassX database. This
admin user is for the SecureDrop Admin + Document Interface and will
allow you to create accounts for the journalists.

The ``add_admin`` command will require you to keep another two-factor
authentication code. Once that's done, you should open the Tor Browser
|TorBrowser| and navigate to the Document Interface's .onion address.

For adding journalist users, please refer now to our `Admin Interface
Guide </docs/admin_interface.md>`__.

Finalizing the Installation
---------------------------

Some of the final configuration is included in these testing steps, so
*do not skip them!*

Test the web application and connectivity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. SSH to both servers over Tor

-  As an admin running Tails with the proper HidServAuth values in your
   ``/etc/torrc`` file, you should be able to SSH directly to the App
   Server and Monitor Server.
-  Post-install you can now SSH *only* over Tor, so use the onion URLs
   from app-ssh-aths and mon-ssh-aths and the user created during the
   Ubuntu installation i.e. ``ssh <username>@m5apx3p7eazqj3fp.onion``.

#. Make sure the Source Interface is available, and that you can make a
   submission.

-  Do this by opening the Tor Browser and navigating to the onion URL
   from ``app-source-ths``. Proceed through the codename generation
   (copy this down somewhere) and you can submit a message or attach any
   random unimportant file.
-  Usage of the Source Interface is covered by our `Source User
   Manual </docs/source_user_manual.md>`__.

#. Test that you can access the Document Interface, and that you can log
   in as the admin user you just created.

-  Open the Tor Browser and navigate to the onion URL from
   app-document-aths. Enter your password and two-factor authentication
   code to log in.
-  If you have problems logging in to the Admin/Document Interface, SSH
   to the App Server and restart the ntp daemon to synchronize the time:
   ``sudo service ntp restart``. Also check that your smartphone's time
   is accurate and set to network time in its device settings.

#. Test replying to the test submission.

-  While logged in as an admin, you can send a reply to the test source
   submission you made earlier.
-  Usage of the Document Interface is covered by our `Journalist User
   Manual </docs/journalist_user_manual.md>`__.

#. Test that the source received the reply.

-  Within Tor Browser, navigate back to the app-source-ths URL and use
   your previous test source codename to log in (or reload the page if
   it's still open) and check that the reply you just made is present.

#. We highly recommend that you create persistent bookmarks for the
   Source and Document Interface addresses within Tor Browser.
#. Remove the test submissions you made prior to putting SecureDrop to
   real use. On the main Document Interface page, select all sources and
   click 'Delete selected'.

Once you've tested the installation and verified that everything is
working, see `How to Use
SecureDrop </docs/journalist_user_manual.md>`__.

Additional testing
~~~~~~~~~~~~~~~~~~

#. On each server, check that you can execute privileged commands by
   running ``sudo su``.
#. Run ``uname -r`` to verify you are booted into grsecurity kernel. The
   string ``grsec`` should be in the output.
#. Check the AppArmor status on each server with ``sudo aa-status``. On
   a production instance all profiles should be in enforce mode.
#. Check the current applied iptables rules with ``iptables-save``. It
   should output *approximately* 50 lines.
#. You should have received an email alert from OSSEC when it first
   started. If not, review our `OSSEC Alerts
   Guide </docs/ossec_alerts.md>`__.

If you have any feedback on the installation process, please let us
know! We're always looking for ways to improve, automate and make things
easier.

.. |Accessories icon| image:: images/icons/accessories.png
.. |Disk Utility icon| image:: images/icons/disk-utility.png
.. |screenshot of the Applications menu in Tails, highlighting Disk Utility| image:: images/screenshots/applications_accessories_disk-utility.png
.. |screenshot of Disk Utility application| image:: images/screenshots/disk-utility.png
.. |screenshot of the menu to create a new partition in the Disk Utility application| image:: images/screenshots/create-partition.png
.. |screenshot of passphrase selection promprt in the Disk Utility application| image:: images/screenshots/create-passphrase.png
.. |image of the disk unlock prompt on Tails| image:: images/screenshots/passphrase-keyring.png
.. |Terminal| image:: images/terminal.png
.. |gpgApplet| image:: images/gpgapplet.png
.. |My Keys| image:: images/install/keyring.png
.. |My Keys| image:: images/install/exportkey.png
.. |My Keys| image:: images/install/exportkey2.png
.. |Fingerprint| image:: images/install/fingerprint.png
.. |Nautilus| image:: images/nautilus.png
.. |Importing Journalist GPG Keys| image:: images/install/importkey.png
.. |Network| image:: images/network-wired.png
.. |Vidalia| image:: images/vidalia.png
.. |KeePassX| image:: images/keepassx.png
.. |TorBrowser| image:: images/torbrowser.png
