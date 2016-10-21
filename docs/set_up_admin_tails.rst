Set up the Admin Workstation
============================

Earlier, you should have created the *admin Tails USB* along with a
persistence volume for it. Now, we are going to add a couple more
features to the *admin Tails USB* to facilitate SecureDrop's setup.

If you have not switched to and booted the *admin Tails USB* on your
regular workstation, do so now.

Start Tails with Persistence Enabled
------------------------------------

After you boot the *admin Tails USB* on your normal workstation, you
should see a *Welcome to Tails* screen with two options. Select *Yes* to
enable the persistent volume and enter your password, but do NOT click
Login yet. Under 'More Options," select *Yes* and click *Forward*.

Enter an *Administration password* for use with this specific Tails
session and click *Login*.

.. note:: The *Administration password* is a one-time password. It
	  will reset every time you shut down Tails.

After Tails finishes booting, make sure you're connected to the
Internet |Network| and that the Tor's Vidalia indicator onion
|Vidalia| is green, using the icons in the upper right corner.

.. |Network| image:: images/network-wired.png
.. |Vidalia| image:: images/vidalia.png


.. _Download the SecureDrop repository:

Download the SecureDrop repository
----------------------------------

The rest of the SecureDrop-specific configuration is assisted by files
stored in the SecureDrop Git repository. We're going to be using this
again once SecureDrop is installed, but you should download it now. To
get started, open a terminal |Terminal|. You will use this Terminal
throughout the rest of the install process.

Start by running the following commands to download the git repository.

.. code:: sh

    cd ~/Persistent
    git clone https://github.com/freedomofpress/securedrop.git

.. note:: Since the repository is fairly large and Tor can be slow,
	  this may take a few minutes.


Verify the Release Tag
~~~~~~~~~~~~~~~~~~~~~~

First, download and verify the *Freedom of the Press Foundation Master
Signing Key*. 

.. code:: sh

    gpg --recv-key "2224 5C81 E3BA EB41 38B3 6061 310F 5612 00F4 AD77"

.. note:: It is important you type this out correctly. If you are not
          copy-pasting this command, we recommend you double-check you have
          entered it correctly before pressing enter.

When passing the full public key fingerprint to the ``--recv-key`` command, GPG
will implicitly verify that the fingerprint of the key received matches the
argument passed.

.. caution:: If GPG warns you that the fingerprint of the key received
             does not match the one requested **do not** proceed with
             the installation. If this happens, please email us at
             securedrop@freedom.press.

Verify that the current release tag was signed with the master signing
key:

.. code:: sh

    cd securedrop/
    git checkout 0.3.10
    git tag -v 0.3.10

You should see ``Good signature from "Freedom of the Press Foundation
Master Signing Key"`` in the output of that last command.

.. caution:: If you do not, signature verification has failed and you
             *should not* proceed with the installation. If this
             happens, please contact us at securedrop@freedom.press.

Create the Admin Passphrase Database
------------------------------------

We provide a KeePassX password database template to make it easier for
admins and journalists to generate strong, unique passphrases and
store them securely. Once you have set up Tails with persistence and
have cloned the repo, you can set up your personal password database
using this template.

You can find the template in ``tails_files/securedrop-keepassx.xml``
in the SecureDrop repository that you just cloned.

.. warning:: You will not be able to access your passwords if you
	     forget the master password or the location of the key
	     file used to protect the database.

To use the template:

-  Open the KeePassX program |KeePassX| which is already installed on
   Tails
-  Select **File**, **Import from...**, and **KeePassX XML (*.xml)**
-  Navigate to the location of **securedrop-keepassx.xml**, select it,
   and click **Open**
-  Set a strong master password to protect the password database (you
   will have to write this down/memorize it)
-  Click **File** and **Save Database As**
-  Save the database in the Persistent folder

.. |Terminal| image:: images/terminal.png
.. |KeePassX| image:: images/keepassx.png
