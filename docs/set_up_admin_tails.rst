Set up the *Admin Workstation*
==============================

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

.. caution:: Do not skip this step as this steps validates the files
             in your Git repository.

First, download and verify the **SecureDrop Release Signing Key**.

.. code:: sh

    gpg --recv-key "2224 5C81 E3BA EB41 38B3 6061 310F 5612 00F4 AD77"

.. note:: It is important you type this out correctly. If you are not
          copy-pasting this command, we recommend you double-check you have
          entered it correctly before pressing enter.

.. tip:: If the ``--recv-key`` command fails, first double-check that
   `Tails is connected to Tor`_.

   Once you've confirmed that you're successfully connected to Tor, try
   re-running the ``--recv-key`` command a few times. The default GPG
   configuration on Tails uses a keyserver pool, which may occasionally return
   a malfunctioning keyserver, causing the ``--recv-key`` command to fail.

   If the command is consistently failing after a few tries, it could
   indicate that the default GPG key servers are down or unreachable. As a
   workaround, another keyserver can be specified by adding the ``--keyserver``
   option to the ``gpg --recv-key`` command. In our experience, the SKS HKPS
   keyserver pool is usually a reliable alternative, so try:

   .. code:: sh

      gpg --keyserver hkps://hkps.pool.sks-keyservers.net --recv-key "2224 5C81 E3BA EB41 38B3 6061 310F 5612 00F4 AD77"

   Again, this is a keyserver pool, so you may need to retry the command a
   couple of times before it succeeds.

.. _Tails is connected to Tor: https://tails.boum.org/doc/anonymous_internet/tor_status/index.en.html

When passing the full public key fingerprint to the ``--recv-key`` command, GPG
will implicitly verify that the fingerprint of the key received matches the
argument passed.

.. caution:: If GPG warns you that the fingerprint of the key received
             does not match the one requested **do not** proceed with
             the installation. If this happens, please email us at
             securedrop@freedom.press.

.. _Checkout and Verify the Current Release Tag:

Verify that the current release tag was signed with the release signing
key:

.. code:: sh

    cd ~/Persistent/securedrop/
    git checkout 0.12.2
    git tag -v 0.12.2

You should see ``Good signature from "SecureDrop Release Signing Key"`` in the
output of that last command along with the fingerprint above.

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

.. tip:: If you would like to add a master password, navigate to **Database** and
   **Change master key**. Note that since each KeePassX database is stored
   on the encrypted persistent volume, this additional passphrase is not necessary.

.. warning:: You will not be able to access your passwords if you
         forget the master password or the location of the key
         file used to protect the database.

In case you wish to manually create a database, the suggested password fields in
the admin template are:

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
.. |KeePassX| image:: images/keepassx.png
