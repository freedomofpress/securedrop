Download the SecureDrop repository
==================================

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
-------------------

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

.. |Terminal| image:: images/terminal.png
.. |KeePassX| image:: images/keepassx.png
