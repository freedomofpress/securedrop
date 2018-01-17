Tails Guide
===========

To log-in SecureDrop and retreived messages sent by sources, the journalist
must be using the Tails operating system. The admin must also use Tails to
access the *Journalist Interface* and create new users.

If you followed the :doc:`SecureDrop Installation instructions <install>`
correctly, you should have already created a *journalist Tails USB* and an
*admin Tails USB* and enabled the persistence volume on each. If you have not,
or need to create another *journalist Tails USB* for a second journalist,
follow the steps below.

If you already know how to boot the *admin Tails USB* or the *journalist Tails
USB* with persistence, you can skip down to the step 'download the repository'.

Note that for all of these instructions to work, you should have already
installed the main SecureDrop application. It is also required that you use
Tails version 2.x or greater.

Installing Tails on USB sticks
------------------------------

Tails is a live operating system that is run from removable media, such as a
DVD or a USB stick. For SecureDrop, you'll need to install Tails onto USB
sticks and enable persistent storage.

We recommend creating an initial Tails Live USB or DVD, and then using that to
create additional Tails Live USBs with the *Tails Installer*, a special program
that is only available from inside Tails. *You will only be able to create
persistent volumes on USB sticks that had Tails installed via the Tails
Installer*.

The `Tails website <https://tails.boum.org/>`__ has detailed and up-to-date
instructions on how to download and verify Tails, and how to create a Tails USB
stick. Here are some links to help you out:

-  `Download and verify the Tails .iso`_
-  `Install onto a USB stick or SD card`_
-  `Create & configure the persistent volume`_

.. _`Download and verify the Tails .iso`: https://tails.boum.org/download/index.en.html
.. _`Install onto a USB stick or SD card`: https://tails.boum.org/doc/first_steps/installation/index.en.html
.. _`Create & configure the persistent volume`: https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html

Note for Mac OS X users manually installing Tails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Tails documentation for `manually installing Tails onto a USB device
on Mac OS X`_ describes how to copy the downloaded .iso image to a USB stick in
Section 4, "Do the copy". This section includes the following ``dd`` invocation
to copy the .iso to the USB:

::

    dd if=[tails.iso] of=/dev/diskX

This command is *very slow*. In our testing, it took about 18 minutes to copy
the .iso to a USB 2.0 drive. You can speed it up by changing the arguments to
``dd`` like so:

::

    dd if=[tails.iso] of=/dev/rdiskX bs=1m

Note the change from ``diskX`` to ``rdiskX``. This reduced the copy time to 3
minutes for us.

.. _`manually installing Tails onto a USB device on Mac OS X`: https://tails.boum.org/doc/first_steps/installation/manual/mac/index.en.html

Configure Tails for use with SecureDrop
---------------------------------------

.. _enable_persistence_in_tails:

Persistence
~~~~~~~~~~~

Creating an encrypted persistent volume will allow you to securely save
information in the free space that is left on the Transfer Device. This
information will remain available to you even if you reboot Tails. Instructions
on how to create and use this volume can be found on the `Tails
website <https://tails.boum.org/doc/first_steps/persistence/index.en.html>`__.
You will be asked to select from a list of persistence features, such as
personal data. We require that you enable **all** features.

Start Tails and enable the persistent volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When starting Tails, you should see a "Welcome to Tails" screen with two
options. Select *Yes* to enable the persistent volume and enter your passphrase.
Select *Yes* to show more options and click *Forward*. Enter an *Administration
passphrase* for use with this specific Tails session and click *Login*.

Download the repository
~~~~~~~~~~~~~~~~~~~~~~~

The rest of the SecureDrop-specific configuration is assisted by files stored
in the SecureDrop git repository. To get started, open a terminal and run the
following commands to download the git repository. Note that since the
repository is fairly large and Tor can be slow, this may take a few minutes.

.. code:: sh

    cd ~/Persistent
    git clone https://github.com/freedomofpress/securedrop.git

Passphrase Database
~~~~~~~~~~~~~~~~~~~

We provide a KeePassX passphrase database template to make it easier for
admins and journalists to generate strong, unique passphrases and
store them securely. Once you have set up Tails with persistence and
have cloned the repo, you can set up your personal passphrase database
using this template.

You can find the template in ``tails_files/securedrop-keepassx.kdbx``
in the SecureDrop repository that you just cloned.

To use the template:

-  Open the KeePassX program |KeePassX| which is already installed on
   Tails
-  Select **Database**, **Open database**, and navigate to the location of
   **securedrop-keepassx.kdbx**, select it, and click **Open**
-  Check the **password** box and hit **OK**
-  Click **Database** and **Save Database As**
-  Save the database in the Persistent folder

.. tip:: If you would like to add a master passphrase, navigate to **Database** and
   **Change master key**. Note that since each KeePassX database is stored
   on the encrypted persistent volume, this additional passphrase is not necessary.

.. warning:: You will not be able to access your passphrases if you
	     forget the master passphrase or the location of the key
	     file used to protect the database.


Set up easy access to the Journalist Interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To complete setup of the *Admin Workstation* or Journalist Workstation, we
recommend using the scripts in ``tails_files`` to easily configure Tor to
access the *Journalist Interface*.

Navigate to the directory with the setup scripts and begin the installation
by typing these commands into the terminal:

::

    ./securedrop-admin tailsconfig

Type the administration passphrase that you selected when starting Tails and hit
enter. This installation script does the following:

* Downloads additional software
* Installs a program that automatically and persistently configures Tor to
  access the SecureDrop servers and interfaces, by adding ``HidServAuth`` values
  to ``/etc/tor/torrc``.
* Sets up desktop and main menu shortcuts for the *Journalist Interface* and
  *Source Interface*
* Sets up SSH host aliases for ``mon`` and ``app``
* Makes it so that Tails installs Ansible at the beginning of every session

If you are missing any files, the script will exit with an error. If you're
running this script as an admin, the entire setup should be automatic.

If you're running the script as a journalist, you will need the .onion addresses
for each interface, provided to you by the admin.

We use an "authenticated" Tor Hidden Service so that adversaries cannot access
the Journalist Interface, providing a layer of defense-in-depth which protects the
Journalist Interface even if there is a security vulnerability in the web
application, or if the journalist's username, passphrase, and two-factor token
are stolen. The extra configuration that is required is handled by this script.

Our ``./securedrop-admin tailsconfig`` tool sets up Tails to work with SecureDrop
every time you login. As long as Tails is booted with the persistent volume enabled
then you can open the Tor Browser and connect to the Journalist Interface as normal.

Create bookmarks for Source and Journalist Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want, you can open the browser and create bookmarks for the Source and
Journalist Interfaces. Navigate to the site you wish to bookmark, select
*Bookmarks* and *Bookmark This Page*, give the site a useful name (e.g. *Source
Interface*), and click *Done*. Tails will remember the bookmarks even if you
reboot.

.. |KeePassX| image:: images/keepassx.png
