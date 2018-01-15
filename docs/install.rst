Install SecureDrop
==================

Install Prerequisites
----------------------

SecureDrop has some dependencies that need to be loaded onto the *Admin
Workstation* prior to the installation of the server.

To load these dependencies, from the base of the SecureDrop repository
(``~/Persistent/securedrop/``) run the following commands:

.. code:: sh

    ./securedrop-admin setup

The package installation will complete in approximately 10 minutes, depending
on network speed and computing power.

 .. note :: Occasionally this command times out due to network latency issues.
    You should be able to re-run the command and complete the setup. If you run
    into a problem, try removing the ``~/Persistent/securedrop/.venv/``
    directory and running the command again. The command should only be run as
    the ``amnesia`` user.

.. _configure_securedrop:

Localization of the source and journalist interfaces
----------------------------------------------------

The source and journalist interface are translated in the following
languages:

* German (de_DE)
* Spanish (es_ES)
* French (fr_FR)
* Italian (it_IT)
* Norwegian (nb_NO)
* Dutch (nl)
* Portuguese, Brasil (pt_BR)
* Turkish (tr)
* Chinese, Traditional (zh_Hant)

During the installation you will be given the opportunity to choose the
list of supported languages to display, using the code shown in
parentheses. When the source interface is displayed in French (for
instance), people submitting documents will expect a journalist fluent
in French is available to read them and followup.

Configure the Installation
--------------------------

Make sure you have the following information and files before
continuing:

-  The *Application Server* IP address
-  The *Monitor Server* IP address
-  The SecureDrop Submission Key (from the *Transfer
   Device*)
-  The SecureDrop Submission Key fingerprint
-  The email address that will receive alerts from OSSEC
-  The GPG public key and fingerprint for the email address that will
   receive the alerts
-  Connection information for the SMTP relay that handles OSSEC alerts.
   For more information, see the :doc:`OSSEC Alerts
   Guide <ossec_alerts>`.
-  The first username of a journalist who will be using SecureDrop (you
   can add more later)
-  The username of the system admin

You will have to copy the following required files to
``install_files/ansible-base``:

-  SecureDrop Submission Key public key file
-  Admin GPG public key file (for encrypting OSSEC alerts)

The SecureDrop Submission Key should be located on your *Transfer
Device* from earlier. It will depend on the location where the USB stick
is mounted, but for example, if you are already at the root of the SecureDrop
repository, you can just run: ::

    cp /media/[USB folder]/SecureDrop.asc install_files/ansible-base

Or you may use the copy and paste capabilities of the file manager.
Repeat this step for the Admin GPG key and custom header image.

Run the configuration playbook and answer the prompts with values that
match your environment: ::

    ./securedrop-admin sdconfig

The script will automatically validate the answers you provided, and display
error messages if any problems were detected. The answers you provided will be
written to the file ``install_files/ansible-base/group_vars/all/site-specific``,
which you can edit in case of errors such as typos before rerunning the script.
You can also run ``./securedrop-admin sdconfig --force`` to remove your entire
configuration file and start over.

When you're done, save the file and quit the editor.

.. _Install SecureDrop Servers:

Install SecureDrop Servers
--------------------------

Now you are ready to install! This process will configure
the servers and install SecureDrop and all of its dependencies on
the remote servers. ::

    ./securedrop-admin install

You will be prompted to enter the sudo passphrase for the *Application* and
*Monitor Servers* (which should be the same).

The install process will take some time, and it will return
the terminal to you when it is complete.

If an error occurs while
running the install, please check all of the details of the error output.

.. include:: includes/rerun-install-is-safe.txt

If needed, make edits to the file located at
``install_files/ansible-base/group_vars/all/site-specific``
as described above. If you continue to have issues please submit a detailed `GitHub
issue <https://github.com/freedomofpress/securedrop/issues/new>`__ or
send an email to securedrop@freedom.press.

.. note::
   The SecureDrop install process configures a custom Linux kernel hardened
   with the grsecurity patch set. Only binary images are hosted in the apt
   repo. For source packages, see the `Source Offer`_.

.. _`Source Offer`: https://github.com/freedomofpress/securedrop/blob/develop/SOURCE_OFFER

Once the installation is complete, the addresses for each Tor Hidden
Service will be available in the following files under
``install_files/ansible-base``:

-  ``app-source-ths``: This is the .onion address of the Source
   Interface
-  ``app-journalist-aths``: This is the ``HidServAuth`` configuration line
   for the Journalist Interface. During a later step, this will be
   automatically added to your Tor configuration file in order to
   exclusively connect to the hidden service.
-  ``app-ssh-aths``: Same as above, for SSH access to the Application
   Server.
-  ``mon-ssh-aths``: Same as above, for SSH access to the Monitor
   Server.

The dynamic inventory file will automatically read the Onion URLs for SSH
from the ``app-ssh-aths`` and ``mon-ssh-aths`` files, and use them to connect
to the servers during subsequent playbook runs.
