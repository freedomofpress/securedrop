Ubuntu 16.04 LTS (Xenial) - Upgrading in Place
==============================================

.. caution::
  You can perform an upgrade from Ubuntu 14.04 to Ubuntu 16.04 in place, but
  please be advised that this may result in prolonged downtime of your SecureDrop
  instance, especially in the event of problems during the upgrade process.

  If you have access to backup hardware, we recommend following the procedure
  described in :doc:`xenial_backup_install_restore` instead.

Communicating with users before the change
------------------------------------------

The process of upgrading in place will result in downtime for your instance. Our
testing indicates that the upgrade may take up to 8 hours, assuming no issues.
We recommend that you plan for 2 days of work, during which the instance will be
unavailable.

In addition to placing a maintenance notice on your instance's *Landing Page*,
we recommend coordinating the upgrade schedule with the internal users of the
system responsible for checking for submissions. If they have ongoing
conversations with sources, or are expecting submissions, it may be necessary to
reschedule the upgrade.


Preparatory steps
-----------------
Before performing the upgrade, please perform all the steps outlined in
:doc:`xenial_prep`.

.. warning::
  In order to successfully upgrade your SecureDrop instance, it is of critical
  importance that your *Admin Workstation* and your servers use SecureDrop
  0.12.0. Older releases of SecureDrop do not not support Ubuntu 16.04.

Upgrade and validate the *Monitor Server*
-----------------------------------------

On your *Admin Workstation*, open a terminal by selecting
**Applications > Favorites > Terminal**. Then connect to the *Monitor Server*
with the command ``ssh mon``.

Before running the ``do-release-upgrade`` command, you must edit the
``/etc/update-manager/release-upgrades``, changing `Prompt=never` to
`Prompt=lts`. **[ED - this won't be necessary when #4104 lands]**

The operating system upgrade process for the *Monitor Server* will take
approximately 30-60 minutes, depending on your server specifications and
available bandwidth, and should not be interrupted once begun. To begin the
process, run the command below and then supply the answers listed below to the
prompts that follow:

.. code:: sh

  sudo do-release-upgrade

.. note:: The prompt answers below have been tested on the
  :ref:`recommended hardware <Specific Hardware Recommendations>` for
  SecureDrop. If your instance uses non-standard hardware, you may see different
  or additional prompts. In general, when responding to these prompts, you
  should choose to preserve existing configuration files whenever possible.

- Run ``sudo do-release-upgrade`` to start the upgrade process
- Press Enter after the "Some third party entries..." message
- Type 'y' and press Enter to continue after the "Installing the upgrade..."
  message
- Type 'y' and press Enter to continue after the "Fetching and installing..."
  message

.. note:: The ``do-release-upgrade`` script displays some dialogs using
  ``ncurses``, a library for rendering GUI elements in text-only displays. It
  may display incorrectly within your terminal window. To force a redraw, adjust
  the terminal window's size to approximately 150 columns by 40 rows, by
  dragging the corners. If it still does not display correctly, make small
  adjustments to the terminal size to force successive redraws.

- Choose **OK** to close the Postfix information dialog
- Choose **No Configuration** and **OK** on the "General type of mail
  configuration" dialog
- Choose **Yes** on the "Configuring libssl.0.0:amd64" dialog - when you do so,
  the ``sshd`` and ``tor`` daemons will restart, breaking your connection to the
  *Monitor Server*
- Close the terminal window, open a new one, and reconnect with the command
  ``ssh mon``
- Choose **No** to overriding local changes on the "PAM configuration" dialog
- Choose the default action (keep local version) when prompted about
  ``blacklist.conf`` changes
- Choose **Keep the local version currently installed** on the
  "Configuring grub-efi-amd64" dialog
- Choose default (keep current version) when prompted about ``/etc/ssh/moduli``
  changes
- Choose default (keep current version) when prompted about
  ``/etc/ssh/ssh_config`` changes
- Choose default (keep current version) when prompted about ``/etc/pam.d/sshd``
  changes
- Choose **keep local version currently installed** and **OK** on the
  "Configuring unattended-upgrades" dialog
- Type 'y' and press Enter to remove obsolete packages when prompted
- Type 'y' and press Enter to restart the system and complete the update

The *Monitor Server* will now reboot - this may take several minutes. In order
to reconnect via ``ssh mon``, you must stop and restart the
*Admin Workstation's* Internet connection, using the upper-right-hand control in
the Tails menu bar.

To confirm that the upgrade succeeded, connect from a terminal using the command
``ssh mon`` and run the following command to display the installed OS version:

.. code:: sh

  sudo lsb_release -a

The output should include the text "Ubuntu 16.04.5 LTS".

Exit the SSH session to the *Monitor Server*. Next, you will upgrade the
*Application Server* using a a similar procedure.

Upgrade and validate the *Application Server*
---------------------------------------------
On your *Admin Workstation*, open a terminal by selecting
**Applications > Favorites > Terminal**. Then connect to the
*Application Server* with the command ``ssh app``.

First, open a terminal by selecting **Applications > Favorites > Terminal**.
Then connect to the Application Server with the command ``ssh app``.

Before running the ``do-release-upgrade`` command, you must edit the
``/etc/update-manager/release-upgrades``, changing `Prompt=never` to
`Prompt=lts`. **[ED - this won't be necessary when #4104 lands]**

The operating system upgrade process should take a similar amount of time as
the upgrade of the *Monitor Server*, and should not be interrupted once begun.

To begin the process, run the command below and then supply the answers listed
below to the prompts that follow.

.. code:: sh

  sudo do-release-upgrade

.. note:: As with the *Monitor Server*, the exact prompts may vary based on your
  hardware, and you should choose to preserve existing configuration files
  whenever possible.

- Run ``sudo do-release-upgrade`` to start the upgrade process
- Press Enter after the "Some third party entries..." message
- Type 'y' and press Enter to continue after the "Installing the upgrade..."
  message
- Type 'y' and press Enter to continue after the "Fetching and installing..."
  message
- Choose **OK** to close the Postfix information dialog
- Choose **No Configuration** and **OK** on the "General type of mail
  configuration" dialog
- Choose **Yes** on the "Configuring libssl.0.0:amd64" dialog - when you do so,
  the ``sshd`` and ``tor`` daemons will restart, breaking your connection to the
  *Application Server*
- Close the terminal window, open a new one, and reconnect with the command
  ``ssh app``
- Choose **No** to overriding local changes on the "PAM configuration" dialog
- Choose the default action (keep local version) when prompted about
  ``blacklist.conf`` changes
- Choose **Keep the local version currently installed** on the
  "Configuring grub-efi-amd64" dialog
- Choose default (keep current version) when prompted about ``/etc/ssh/moduli``
  changes
- Choose default (keep current version) when prompted about
  ``/etc/ssh/ssh_config`` changes
- Choose default (keep current version) when prompted about ``/etc/pam.d/sshd``
  changes
- Choose **keep local version currently installed** and **OK** on the
  "Configuring unattended-upgrades" dialog
- Type 'y' and press Enter to remove obsolete packages when prompted
- Type 'y' and press Enter to restart the system and complete the update

The *Application Server* will now reboot - this may take several minutes. In
order to reconnect via ``ssh app``, you must stop and restart the
*Admin Workstation's* Internet connection,  using the upper-right-hand control
in the Tails menu bar.

To confirm that the upgrade succeeded, connect from a terminal using the command
``ssh app`` and run the following command to display the installed OS version:

.. code:: sh

  sudo lsb_release -a

The output should include the text "Ubuntu 16.04.5 LTS".

Disconnect the SSH session to the Application Server. You are now ready to move
on to the next step: updating to the Ubuntu 16.04 version of the application
code and configuration using ``./securedrop-admin install``

Reinstall the SecureDrop application
------------------------------------

Open a new Terminal, and run the following commands to set up the SecureDrop admin environment:

.. code:: sh

  cd ~/Persistent/securedrop
  ./securedrop-admin setup

Next, verify that the SecureDrop configuration matches expected values, by stepping through the configuration using:

.. code:: sh

  ./securedrop-admin sdconfig

Finally, install the Ubuntu 16.04 version of the server application code and
configuration:

.. code:: sh

  ./securedrop-admin install

You will be prompted for the admin user's passphrase on the servers. Type it in
and press Enter.

Perform additional tests
------------------------
While we have extensively tested the upgrade on recommended hardware, we
recommend performing the following tests yourself to identify potential issues
specific to your system configuration.

Validate the kernel version
^^^^^^^^^^^^^^^^^^^^^^^^^^^
Ensure you are logged out, and then type the commands ``ssh app uname -r`` and
``ssh mon uname -r`` in your terminal window.

The output for both commands should be ``4.4.167-grsec``, which indicates that
the latest available kernel for SecureDrop is installed on your *Application
Server* and your *Monitor Server*.

Validate the application version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To confirm that you are running SecureDrop 0.12.0 for Xenial, on the Tails
desktop, you should find a shortcut called **SecureDrop Source Interface**.
Double-click it to launch the Tor browser.

After the *Source Interface* loads, add the path ``/metadata`` to the URL in
your address bar. If your *Source Interface* can be found at
``examplenot4real.onion``, then the address you should visit is
``examplenot4real.onion/metadata``. That page should show you key/value pairs,
including ``0.12.0`` for ``sd_version`` and ``16.04`` for ``server_os``.

End-to-end test
^^^^^^^^^^^^^^^
We recommend an end-to-end test of document submission, reply and decryption.
First, confirm that you can log into the *Journalist Interface*. On the Tails
desktop, you should find a shortcut called **SecureDrop Journalist Interface**.
Double-click it to launch the Tor browser.

Once the page has finished loading, sign in using your SecureDrop login
credentials. Confirm that you can view the list of submissions as expected.

Keep the browser window open, and launch the **SecureDrop Source Interface**
using its shortcut on the Tails desktop. The *Source Interface* should load in
another browser tab.

Once the page has finished loading, click **Submit Documents**. On the subsequent
page, click **Submit Documents** again (you may want to write down your codename
in case you need it for further testing).On the following screen, choose a
simple file to upload, and enter a message to go along with it, then press
**Submit**.

Switch to the tab with the *Journalist Interface*, reload it, and confirm that
you can see your new submission. Write a reply, and switch back to the
*Source Interface*. Reload it, and confirm that you can see the reply.

Now, from the *Journalist Interface*, download the submission you just made.
Copy it to your *Transfer Device* and boot into your *Secure Viewing Station*.
Confirm that you can open the encrypted document.

Just in case you picked the wrong submission, we strongly recommend following
standard precautions, e.g., do not open the document directly from the *Transfer
Device* but copy it onto the *Secure Viewing Station* first.

Contact us
----------
If you have questions or comments regarding this process, or if you
encounter any issues, you can always contact us by the following means:

- via our `Support Portal <https://support.freedom.press>`_, if you are a member
  (membership is approved on a case-by-case basis);
- via securedrop@freedom.press
  (`GPG encrypted <https://securedrop.org/sites/default/files/fpf-email.asc>`__)
  for sensitive security issues (please use judiciously);
- via our `community forums <https://forum.securedrop.org>`_.

If you encounter problems that are not security-sensitive, we also encourage you
to `file an issue <https://github.com/freedomofpress/securedrop/issues/new/>`
in our public GitHub repository.
