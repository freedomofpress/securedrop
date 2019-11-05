Set up the *Admin Workstation*
==============================

.. _set_up_admin_tails:

Earlier, you should have created the *Admin Workstation* Tails USB along with a
persistence volume for it. Now, we are going to add a couple more features to
the *Admin Workstation* to facilitate SecureDrop's setup.

If you have not switched to and booted the *Admin Workstation* Tails USB on your
regular workstation, do so now.

Start Tails with Persistence Enabled
------------------------------------

After you boot the *Admin Workstation* Tails USB on your normal workstation, you
should see a *Welcome to Tails* screen with *Encrypted Persistent
Storage*.  Enter your password and click *Unlock*. Do NOT click *Start
Tails* yet. Under *Additional Settings* click the *plus* sign.

Click *Administration password*, enter a password for use with this
specific Tails session and click *Add*. And finally click *Start
Tails*.

.. note:: The *Administration password* is a one-time password. It
      will reset every time you shut down Tails.

After Tails finishes booting, make sure you're connected to the Internet
|Network| and that the Tor status onion icon is not crossed out
|TorStatus|, consulting the icons in the upper right corner of the
screen.

.. |Network| image:: images/network-wired.png
.. |TorStatus| image:: images/tor-status-indicator.png


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

.. caution:: Do not download SecureDrop Git repository as a Zip file,
             or any other means. Only download by using the given git
             command.


Verify the Release Tag
~~~~~~~~~~~~~~~~~~~~~~

.. important::

   It is crucial for the integrity of your installation that you carefully
   follow the instructions below. By following these steps, you will verify
   if your copy of the codebase has been approved by the SecureDrop
   development team.

Download and verify the **SecureDrop Release Signing Key** using the following
command:

.. code:: sh

   gpg --keyserver hkps://keys.openpgp.org --recv-key \
    "2224 5C81 E3BA EB41 38B3 6061 310F 5612 00F4 AD77"

If you are not copy-pasting this command, we recommend you double-check you have
entered it correctly before pressing enter. GPG will implicitly verify that the
fingerprint of the key received matches the argument passed.

.. _Tails is connected to Tor: https://tails.boum.org/doc/anonymous_internet/tor_status/index.en.html

If GPG warns you that the fingerprint of the key received does not
match the one requested, do **not** proceed with the installation. If this
happens, please contact us at securedrop@freedom.press.

.. note::

   If the ``--recv-key`` command fails, first double-check that
   `Tails is connected to Tor`_. Once you've confirmed that you're successfully
   connected to Tor, try re-running the ``--recv-key`` command a few times.

   If the command still fails, the *keys.openpgp.org* keyserver may be down.
   In that case, we recommend downloading the key from the SecureDrop website:

   .. code:: sh

      cd ~/Persistent
      torify curl -LO https://securedrop.org/securedrop-release-key.asc

   Before importing it, inspect the key's fingerprint using the following
   command. The ``--dry-run`` option ensures that the key is not imported just
   yet:

   .. code:: sh

      gpg --with-fingerprint --import-options import-show --dry-run \
        --import securedrop-release-key.asc

   Compare the fingerprint in the output with the fingerprint at the beginning
   of this section. If the fingerprints match, you can safely import the key,
   using the following command:

   .. code:: sh

      gpg --import securedrop-release-key.asc

   If you encounter any difficulties verifying the integrity of the
   release key, do **not** proceed with the installation. Instead, please
   contact us at securedrop@freedom.press.

.. _Checkout and Verify the Current Release Tag:

Once you have imported the release key, verify that the current release tag was
signed with the release signing key:

.. code:: sh

    cd ~/Persistent/securedrop/
    git checkout 1.1.0
    git tag -v 1.1.0

You should see ``Good signature from "SecureDrop Release Signing Key"`` in the
output of that last command along with the fingerprint above.

.. important::

   If you do not see the message above, signature verification has failed
   and you should **not** proceed with the installation. If this happens,
   please contact us at securedrop@freedom.press.

.. _keepassxc_setup:

Create the Admin Passphrase Database
------------------------------------

We provide a KeePassXC password database template to make it easier for
admins and journalists to generate strong, unique passphrases and
store them securely. Once you have set up Tails with persistence and
have cloned the repo, you can set up your personal password database
using this template.

.. note::

   Earlier versions of Tails used KeePassX instead of KeePassXC.
   The provided template is compatible with both.

You can find the template in ``tails_files/securedrop-keepassx.kdbx``
in the SecureDrop repository that you just cloned. To use the template:

-  Copy the template to the Persistent folder - from a terminal, run the
   command:

   .. code:: sh

     cp ~/Persistent/securedrop/tails_files/securedrop-keepassx.kdbx \ 
        ~/Persistent/keepassx.kdbx

-  Open the KeePassXC program |KeePassXC| which is already installed on
   Tails
-  Select **Database**, **Open database**, and navigate to the location of
   **~/Persistent/keepassx.kdbx**, select it, and click **Open**
-  Check the **password** box and hit **OK**
-  Edit entries as required.
-  Select **Database** and **Save Database** to save your changes.

The next time you use KeepassXC, the database at ``~/Persistent/keepassx.kdbx``
will be opened by default.

.. tip:: If you would like to add a master password, navigate to **Database** and
   **Change master key**. Note that since each KeePassXC database is stored
   on the encrypted persistent volume, this additional passphrase is not necessary.

.. warning:: You will not be able to access your passwords if you
         forget the master password or the location of the key
         file used to protect the database.

In case you wish to manually create a database, the suggested password fields in
the template are:

**Admin**:

- Admin account username
- App Server SSH Onion URL
- Email account for sending OSSEC alerts
- Monitor Server SSH Onion URL
- Network Firewall Admin Credentials
- OSSEC GPG Key
- SecureDrop Login Credentials

**Journalist**:

- Auth Value: Journalist Interface
- Onion URL: Journalist Interface
- Personal GPG Key
- SecureDrop Login Credentials

**Secure Viewing Station**:

- SecureDrop GPG Key

**Backup**:

- This section contains clones of the above entries in case a user
  accidentally overwrites an entry.

.. |Terminal| image:: images/terminal.png
.. |KeePassXC| image:: images/keepassxc.png
