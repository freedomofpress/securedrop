Admin Guide
===========

.. include:: ./includes/provide-feedback.txt

.. _Responsibilities:

Responsibilities
----------------

The SecureDrop architecture contains multiple machines and hardened servers.
While we have automated many of the installation and maintenance tasks, a
skilled Linux admin is required to responsibly run the system.

This section outlines the tasks the admin is responsible for in order to
ensure that the SecureDrop server continues to be a safe place for sources to
talk to journalists.

Maintaining Credentials
~~~~~~~~~~~~~~~~~~~~~~~

The admin should have her own username, passphrase, and two-factor
authentication method (via smartphone app or YubiKey). Admins are also
responsible for managing user credentials and encouraging best practices. (See
:doc:`passphrases` and :doc:`passphrase_best_practices`.)

Updating the SecureDrop Servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The admin should be aware of all SecureDrop updates and take any required
manual action if requested in the `SecureDrop Release Blog`_. We recommend
subscribing to the `SecureDrop RSS Feed`_ to stay apprised of new updates.

Most often, the SecureDrop server will automatically update via apt. However,
occasionally you will need to run ``securedrop-admin install``. We will inform you in
the release blog when this is the case. If you are onboarded to our `SecureDrop
Support Portal`_, we will let you know in advance of major releases if manual
intervention will be required.

.. _`SecureDrop Release Blog`: https://securedrop.org/news
.. _`SecureDrop RSS Feed`: https://securedrop.org/news/feed

Updating the Network Firewall
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given all traffic first hits the network firewall as it faces the non-Tor public
network, the admin should ensure that critical security patches are applied to the
firewall.

Be informed of potential updates to your network firewall. If you're using the
network firewall suggested by FPF, you can subscribe to the `Netgate RSS Feed`_
to be alerted when releases occur. If critical security updates need to be
applied, you can do so through the firewall's pfSense WebGUI. Refer to our
:ref:`Keeping pfSense up to date` documentation or the official `pfSense
Upgrade Docs`_ for further details on how to update the suggested firewall.

.. _`Netgate RSS Feed`: https://www.netgate.com/feed.xml
.. _`pfSense Upgrade Docs`: https://doc.pfsense.org/index.php/Upgrade_Guide

Updating the SecureDrop Workstations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The admin should keep all SecureDrop workstations updated with

* **Tails updates** for each *Admin Workstation*, *Journalist Workstation*, and
  *Secure Viewing Station*; and
* **SecureDrop workstation updates** for each *Admin Workstation* and
  *Journalist Workstation*.

You should apply Tails updates to your Tails drives as they are released, as they
often contain critical security fixes. Subscribe to the `Tails RSS Feed`_ to be
alerted of new releases. The online Tails drives, once booted and connected to Tor,
will alert you if upgrades are available. Follow the `Tails Upgrade Documentation`_
on how to upgrade the drives.

.. include:: includes/update-gui.txt

.. _`Tails RSS Feed`: https://tails.boum.org/news/index.en.rss
.. _`Tails
   Upgrade Documentation`: https://tails.boum.org/doc/upgrade/index.en.html

Monitoring OSSEC Alerts for Unusual Activity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The admin should decrypt and read all OSSEC alerts. Report any suspicious events to
FPF through the `SecureDrop Support Portal`_. See the :doc:`OSSEC Guide <ossec_alerts>`
for more information on common OSSEC alerts.

.. warning:: Do not post logs or alerts to public forums without first carefully
         examining and redacting any sensitive information.

.. _test OSSEC alert:

.. note:: You can send a test OSSEC alert to verify OSSEC and your email configuration
          is working properly through the *Admin Interface* by clicking **Send
          Test OSSEC Alert**:

          |Test Alert|

.. |Test Alert| image:: images/manual/screenshots/journalist-admin_ossec_alert_button.png

.. _`SecureDrop Support Portal`: https://securedrop-support.readthedocs.io/en/latest/

Common Tasks
------------

.. _Adding Users:

Adding Users
~~~~~~~~~~~~

Now you can add new logins for the journalists at your news organization
who will be checking the system for submissions. Make sure the
journalist is physically in the same room as you when you do this, as
they will have to scan a barcode for their
two-factor authentication. Since you’re logged in, this is the screen
you should see now:

|SecureDrop main page|

In the top right corner click the “Admin” link, which should bring you
to this page:

|SecureDrop admin home|

Once there, click ‘Add User’ button, which will take you to this page:

|Add a new user|

Here, you will hand the keyboard over to the journalist so they can
create their own username. Once they’re done entering a
username for themselves, have them write down their pre-generated diceware
passphrase. Then, you will select whether you would like them
to also be an admin (this allows them to add or delete other
journalist accounts), and whether they will be using FreeOTP
or a YubiKey for two-factor authentication.

FreeOTP
^^^^^^^

If they are using FreeOTP for their two-factor, they can
just proceed to the next page:

|Enable FreeOTP|

At this point, the journalist should make sure they have downloaded the
FreeOTP app to their smartphone. It can be installed from
the Apple Store for an iPhone or from the Google Play store for an
Android phone. Once you download it and open it, the app does not
require setup. It should prompt you to scan a barcode. The journalist
should use their phone's camera to scan the barcode on the screen.

If they have difficulty scanning the barcode, they can tap on the icon
at the top that shows a plus and the symbol of a key and use their
phone's keyboard to input the random characters that are highlighted
in yellow, in the ``Secret`` input field, without white space.

Inside the FreeOTP app, a new entry for this account will
appear on the main screen, with a six digit number that recycles to a
new number every thirty seconds. Enter the six digit number under
“Verification code” at the bottom of the screen, and hit
enter.

If FreeOTP was set up correctly, you will be redirected
back to the Admin Interface and will see a confirmation that the
two-factor code was verified.

.. include:: includes/otp-app.txt

YubiKey
^^^^^^^

If the journalist wishes to use a YubiKey for two-factor authentication,
check the box next to "I'm using a YubiKey". You will then need to enter
the OATH-HOTP Secret Key that your YubiKey is configured with. For more
information, read the :doc:`YubiKey Setup Guide <yubikey_setup>`.

|Enable YubiKey|

Once you've configured your YubiKey and entered the Secret Key, click
*Add user*. On the next page, enter a code from your YubiKey by
inserting it into the workstation and pressing the button.

|Verify YubiKey|

If everything was set up correctly, you will be redirected back to the
Admin Interface, where you should see a flashed message that says "The
two-factor code for user *new username* was verified successfully.".

Congratulations! You have successfully set up a journalist on
SecureDrop. Make sure the journalist remembers their username and
passphrase and always has their two-factor authentication device in their
possession when they attempt to log in to SecureDrop.

.. |SecureDrop main page|
  image:: images/manual/screenshots/journalist-admin_index_no_documents.png
.. |SecureDrop admin home|
  image:: images/manual/screenshots/journalist-admin_interface_index.png
.. |Add a new user|
  image:: images/manual/screenshots/journalist-admin_add_user_totp.png
.. |Enable FreeOTP|
  image:: images/manual/screenshots/journalist-admin_new_user_two_factor_totp.png
.. |Enable YubiKey|
  image:: images/manual/screenshots/journalist-admin_add_user_hotp.png
.. |Verify YubiKey|
  image:: images/manual/screenshots/journalist-admin_new_user_two_factor_hotp.png

Server Command Line Use
~~~~~~~~~~~~~~~~~~~~~~~

Generally, you should avoid directly SSHing into the servers in favor of using
the *Admin Interface* or ``securedrop-admin`` CLI tool. However, in some cases,
you may need to SSH in order to troubleshoot and fix a problem that cannot be
resolved via these tools.

In this section we cover basic commands you may find useful when you SSH into
the *Application Server* and *Monitor Server*.

.. tip:: When you SSH into either SecureDrop server, you will be dropped into a
        ``tmux`` session. ``tmux`` is a screen multiplexer - it allows you to tile
        panes, preserve sessions to keep your session alive if the network
        connection fails, and more. Check out this `tmux tutorial`_ to learn how
        to use ``tmux``.

.. _`tmux tutorial`:
  https://robots.thoughtbot.com/a-tmux-crash-course

.. tip:: If you want a refresher of the Linux command line, we recommend
  `this resource`_ to cover the fundamentals.

.. _`this resource`:
  http://linuxcommand.org/lc3_learning_the_shell.php

Shutting Down the Servers
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: sh

  sudo shutdown now -h

Rebooting the Servers
^^^^^^^^^^^^^^^^^^^^^

.. code:: sh

  sudo reboot

.. _investigating_logs:

Investigating Logs
^^^^^^^^^^^^^^^^^^

Consult our :doc:`Investigating Logs <logging>` topic guide for locations of the
most relevant log files you may want to examine as part of troubleshooting, and
for how to enable error logging for the *Source Interface*.

.. include:: includes/get-logs.txt

Immediately Apply a SecureDrop Update
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SecureDrop will update and reboot once per day. However, if after a SecureDrop
update `is announced`_ you wish to fetch the update immediately, you can SSH
into each server and run:

.. code:: sh

  sudo cron-apt -i -s

.. _`is announced`:
  https://securedrop.org/news

Application Server
^^^^^^^^^^^^^^^^^^

Adding Users (CLI)
&&&&&&&&&&&&&&&&&&

After the provisioning of the first admin account, we recommend
using the Admin Interface web application for adding additional journalists
and admins.

However, you can also add users via ``./manage.py`` in ``/var/www/securedrop/``
as described :doc:`during first install <create_admin_account>`. You can use
this command line method if the web application is unavailable.

Restart the Web Server
&&&&&&&&&&&&&&&&&&&&&&

If you make changes to your Apache configuration, you may want to restart the
web server to apply the changes:

.. code:: sh

  sudo service apache2 restart

.. _submission-cleanup:

Cleaning up deleted submissions
&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

When submissions are deleted through the web interface, their database
records are deleted and their encrypted files are securely wiped. For
large files, secure removal can take some time, and it's possible,
though unlikely, that it can be interrupted, for example by a server
reboot. In older versions of SecureDrop this could leave a submission
file present without a database record.

As of SecureDrop 1.0.0, automated checks send OSSEC alerts when this
situation is detected, recommending you run ``manage.py
list-disconnected-fs-submissions`` to see the files affected. As with
any ``manage.py`` usage, you would run the following on the admin
workstation:

.. code:: sh

   ssh app
   sudo -u www-data bash
   cd /var/www/securedrop
   ./manage.py list-disconnected-fs-submissions

You then have the option of running:

.. code:: sh

   ./manage.py delete-disconnected-fs-submissions

to clean them up. As with any potentially destructive operation, it's
recommended that you :doc:`back the system up <backup_and_restore>`
before doing so.

There is also the inverse scenario, where a database record could
point to a file that no longer exists. This would usually only have
happened as a result of disaster recovery, where perhaps the database
was recovered from a failed hard drive, but some submissions could not
be. The OSSEC alert in this case would recommend running:

.. code:: sh

   ./manage.py list-disconnected-db-submissions


To clean up the affected records you would run (again, preferably
after a backup):

.. code:: sh

   ./manage.py delete-disconnected-db-submissions


Even when submissions are completely removed from the application
server, their encrypted files may still exist in backups. We recommend
that you delete old backup files with ``shred``, which is available on
Tails.

Monitor Server
^^^^^^^^^^^^^^

Restart OSSEC
&&&&&&&&&&&&&

If you make changes to your OSSEC monitoring configuration, you will want to
restart OSSEC via `OSSEC's control script`_, ``ossec-control``:

.. code:: sh

   sudo /var/ossec/bin/ossec-control restart

.. _`OSSEC's control script`:
  https://ossec-docs.readthedocs.io/en/latest/programs/ossec-control.html

.. _Updating the Servers:

Updating the Servers
^^^^^^^^^^^^^^^^^^^^

Sometimes you will want to update the system configuration on the SecureDrop
servers. For example, to customize the logo on the source interface,
or change the PGP key that OSSEC alerts are encrypted to. You can do this from
your *Admin Workstation* by following the procedure described in this
section.

.. _Updating Logo Image:

Updating Logo Image
~~~~~~~~~~~~~~~~~~~

You can update the system logo shown on the web interfaces of your SecureDrop
instance via the Admin Interface. We recommend a size of ``500px x 450px``.
Simply click the **Update Instance Config** button:

|System Config Page|

And on the instance configuration page, select and upload the PNG image you prefer.
You should see a message appear indicating the change was a success:

|Logo Update|

.. |System Config Page| image:: images/manual/screenshots/journalist-admin_system_config_page.png
.. |Logo Update| image:: images/manual/screenshots/journalist-admin_changes_logo_image.png

Updating System Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _update-system-configuration:

If you want to update the system configuration, you should use the
``securedrop-admin`` tool on the *Admin Workstation*. From
``~/Persistent/securedrop``, run:

.. code:: sh

  ./securedrop-admin sdconfig

This will give you the opportunity to edit any variable. Answer the prompts with values
that match your environment. An example of one such prompt would be to set the ``daily reboot time``.
To minimize the presence/duration of plaintext in memory, the servers are rebooted every 24 hours
to periodically wipe the memory. As an admin, you can configure this automatic reboot time.
By default, it is set at 4:00 a.m. and you can change it to suit your timing. Next, you will need to
apply the changes to the servers. Again from ``~/Persistent/securedrop``:

.. code:: sh

  ./securedrop-admin install

.. include:: includes/rerun-install-is-safe.txt

Once the install command has successfully completed, the changes are applied.
Read the next section if you have multiple admins.

.. note::
  Server configuration is stored on the *Admin Workstation* in
  ``~/Persistent/securedrop/install_files/ansible-base/group_vars/all/site-specific``.

Managing ``site-specific`` Updates On Teams With Multiple Admins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Organizations with multiple admins should establish a protocol to communicate
any changes one admin makes to the ``site-specific`` configuration file on the server.

Currently, when one admin pushes changes in ``site-specific`` to the server, the
changes will not sync to the local ``site-specific`` file on the remaining admin workstations.
Without being aware of changes made to ``site-specific``, admins run the risk of pushing old
information to the servers. This can affect the receipt of OSSEC alerts, viability of the
*Submission Key*, among other critical components of the SecureDrop environment.

There are multiple ways to avoid pushing out-of-date information to the servers.
We recommend admins establish a secure communication pipeline to alert fellow admins
of any changes made to ``site-specific`` on the server. That clues every admin in on
changes in real time, providing all team members with a reminder to manually update
all ``site-specific`` files.

In addition to secure group communications, admins can learn of updates to the server
by monitoring OSSEC alerts. (Please note that while an OSSEC alert can notify you of the
occurrence of an update to the server, it may not reveal the content of the change.) Another
management option would be SSHing into the server and manually inspecting the configuration to
identify any discrepancies.

Configuring Localization for the *Source Interface* and the *Journalist Interface*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *Source Interface* and *Journalist Interface* are translated in the following
languages:

.. include:: includes/l10n.txt

At any time during and after initial setup, you can choose from a list of
supported languages to display using the codes shown in parentheses.

.. note:: With a *Source Interface* displayed in French (for example), sources
          submitting documents are likely to expect a journalist fluent in
          French to be available to read the documents and follow up in that
          language.

To add or remove locales from your instance, you'll need to :ref:`update your
system configuration <update-system-configuration>` as outlined above.

When you reach the prompt starting with "Space separated list of additional
locales to support", you will see a list of languages currently supported.
Refer to the list above to see which languages correspond to which language
codes. For example: ::

    Space separated list of additional locales to support (ru nl pt_BR fr_FR tr it_IT zh_Hant sv hi ar en_US de_DE es_ES nb_NO): nl fr_FR es_ES

You'll need to list all languages you now want to support, adding or removing
languages as needed. Locale changes will be applied after the next reboot.

Frequently Asked Questions
--------------------------

Some initial troubleshooting steps for common scenarios follow.
If you continue to have trouble after following these steps, you can contact the
SecureDrop team for further assistance.

Generic Troubleshooting Tips
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When troubleshooting, ensure you are on the latest version of SecureDrop
in your *Admin Workstation*. This is done by accepting the update
when prompted at boot in the GUI that appears.

I can't SSH into my servers over Tor from my Admin Workstation. What do I do?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At any point after the successful installation of SecureDrop, if you cannot SSH
into your Admin Workstation, you should first perform the following troubleshooting steps:

#. **Ensure that you are connected to Tor.** You can do this by browsing to any site
   in Tor Browser in your *Admin Workstation*.

#. **Ensure your servers are online.** Visit the *Admin Interface* to check
   your *Application Server* is online, and you can trigger a `test OSSEC alert`_
   to verify your *Monitor Server* is online.

#. **Ensure that SSH aliases and onion service authentication are configured:**

   - First, ensure that the correct configuration files are present in
     ``~/Persistent/securedrop/install_files/ansible-base``.

     If v2 onion services
     are configured, you should have 4 files:

     - ``app-ssh-aths``
     - ``mon-ssh-aths``
     - ``app-journalist-aths``
     - ``app-source-ths``


     If v3 onion services are
     enabled, you should have the following 5 files:

     - ``app-ssh.auth_private``
     - ``mon-ssh.auth_private``
     - ``app-journalist.auth_private``
     - ``app-sourcev3-ths``
     - ``tor_v3_keys.json``

   - Then, from ``~/Persistent/securedrop``, run  ``./securedrop-admin tailsconfig``.
     This will ensure your local Tails environment is configured properly.

#. **Confirm that your SSH key is available**: During the install, you
   configured SSH public key authentication using ``ssh-copy-id``.
   Ensure this key is available using ``ssh-add -L``. If you see the output
   "This agent has no identities." then you need to add the key via ``ssh-add``
   prior to SSHing into the servers.

I got a unusual error when running ``./securedrop-admin install``. What do I do?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the error message is not informative, try running it again. The Tor
connection can be flaky and can cause apparent errors, but there is no negative
impact of re-rerunning ``./securedrop-admin install`` more than once. The
command will simply check which tasks have been completed, and pick up where it
left off. However, if the same issue persists, you will need to investigate
further.
