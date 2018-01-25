Admin Guide
===========

You (the admin) should have your own username and passphrase, plus
two-factor authentication through either the FreeOTP app
on your smartphone or a YubiKey.

.. _Responsibilities:

Responsibilities
----------------

The SecureDrop architecture contains multiple hardened servers, and while we have
automated many of the installation and maintenance tasks, a skilled Linux
admin and some manual intervention is required to responsibly run the system.

This section outlines the tasks the admin is responsible for in order to
ensure that the SecureDrop server continues to be a safe place for sources to
talk to journalists.

Keep your SecureDrop Server Updated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should maintain awareness of SecureDrop updates and take any required
manual action if requested in the `SecureDrop Release Blog`_. We recommend
subscribing to the `SecureDrop RSS Feed`_ to stay apprised of new updates.

Most often, the SecureDrop server will automatically update via apt. However,
occasionally you will need to run the Ansible playbooks. We will inform you in
the release blog when this is the case. If you are onboarded to our `SecureDrop
Support Portal`_, we will let you know in advance of major releases if manual
intervention will be required.

.. _`SecureDrop Release Blog`: https://securedrop.org/news
.. _`SecureDrop RSS Feed`: https://securedrop.org/news/feed

Keep your Network Firewall Updated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Given all traffic first hits the network firewall as it faces the non-Tor public
network, you will want to ensure that critical security patches are applied.

Be informed of potential updates to your network firewall. If you're using the
suggested network firewall by FPF you can subscribe to the `Netgate RSS Feed`_
to be alerted when releases occur. If critical security updates need to be
applied, you can do so through the firewall's pfSense WebGUI. Refer to our
:ref:`Keeping pfSense up to date` documentation or the official `pfSense
Upgrade Docs`_ for further details on how to update the suggested firewall.

.. _`Netgate RSS Feed`: https://www.netgate.com/feed.xml
.. _`pfSense Upgrade Docs`: https://doc.pfsense.org/index.php/Upgrade_Guide

Keep your Tails Drives Updated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should apply updates to your Tails drives as they are released, as they
can contain critical security fixes. Subscribe to the `Tails RSS Feed`_ to be
alerted of new releases. The online Tails drives, once booted and connected to Tor,
will alert you if upgrades are available. Follow the `Tails Upgrade Documentation`_
on how to upgrade the drives.

.. _`Tails RSS Feed`: https://tails.boum.org/news/index.en.rss
.. _`Tails
   Upgrade Documentation`: https://tails.boum.org/doc/first_steps/upgrade/index.en.html

Monitor OSSEC alerts for Unusual Activity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should decrypt and read your OSSEC alerts. Report any suspicious events to
FPF through the `SecureDrop Support Portal`_. See the :doc:`OSSEC Guide <ossec_alerts>`
for more information on common OSSEC alerts.

.. warning:: Do not post logs or alerts to public forums without first carefully
    examining and redacting any sensitive information.

.. note:: You can send a test OSSEC alert to verify OSSEC and your email configuration
          is working properly through the *Admin Interface* by clicking **Send
          Test OSSEC Alert**:

          |Test Alert|

.. |Test Alert| image:: images/manual/screenshots/journalist-admin_ossec_alert_button.png

.. _`SecureDrop Support Portal`: https://securedrop-support.readthedocs.io/en/latest/


.. _Adding Users:

Adding Users
------------

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
~~~~~~~

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
two-factor token was verified.

.. include:: includes/otp-app.txt

YubiKey
~~~~~~~

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
Admin Interface, where you should see a flashed message that says "Two
factor token successfully verified for user *new username*!".

Congratulations! You have successfully set up a journalist on
SecureDrop. Make sure the journalist remembers their username and
passphrase and always has their 2 factor authentication device in their
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

Server Command Line
-------------------

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

Both Servers
~~~~~~~~~~~~

.. tip:: If you want a refresher of the Linux command line, we recommend
  `this resource`_ to cover the fundamentals.

.. _`this resource`:
  http://linuxcommand.org/lc3_learning_the_shell.php

Shutdown the Servers
^^^^^^^^^^^^^^^^^^^^

.. code:: sh

  sudo shutdown now -h

Rebooting the Servers
^^^^^^^^^^^^^^^^^^^^^

.. code:: sh

  sudo reboot

Investigating Logs
^^^^^^^^^^^^^^^^^^^

Refer to the :doc:`Useful Logs <logging>` documentation to see the locations of
files that contain relevant information while debugging issues on your SecureDrop
servers.

.. note:: You can also use the ``securedrop-admin`` tool to extract logs to
  send to Freedom of the Press Foundation for analysis:

    .. code:: sh

      cd ~/Persistent/securedrop
      ./securedrop-admin logs

  This command will produce encrypted tarballs containing logs from each server.

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
~~~~~~~~~~~~~~~~~~

Adding Users (CLI)
^^^^^^^^^^^^^^^^^^

After the provisioning of the first administrator account, we recommend
using the Admin Interface web application for adding additional journalists
and administrators.

However, you can also add users via ``./manage.py`` in ``/var/www/securedrop/``
as described :doc:`during first install <create_admin_account>`. You can use
this command line method if the web application is unavailable.

Restart the Web Server
^^^^^^^^^^^^^^^^^^^^^^^

If you make changes to your Apache configuration, you may want to restart the
web server to apply the changes:

.. code:: sh

  sudo service apache2 restart

Monitor Server
~~~~~~~~~~~~~~

Restart OSSEC
^^^^^^^^^^^^^

If you make changes to your OSSEC monitoring configuration, you will want to
restart OSSEC via `OSSEC's control script`_, ``ossec-control``:

.. code:: sh

   sudo /var/ossec/bin/ossec-control restart

.. _`OSSEC's control script`:
  https://ossec-docs.readthedocs.io/en/latest/programs/ossec-control.html

.. _Updating the Servers:

Updating the Servers
--------------------

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

And on the instance configuration page, select and upload the image you prefer.
You should see a message appear indicating the change was a success:

|Logo Update|

.. |System Config Page| image:: images/manual/screenshots/journalist-admin_system_config_page.png
.. |Logo Update| image:: images/manual/screenshots/journalist-admin_changes_logo_image.png

Updating system configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Other server configuration is stored on the *Admin Workstation* in
``~/Persistent/securedrop/install_files/ansible-base/group_vars/all/site-specific``.

If you want to update the system configuration, there are two options:

1. Manually edit the ``site-specific`` file to make the desired modifications.
2. From ``~/Persistent/securedrop``, run
   ``./securedrop-admin sdconfig --force``, which will require you to retype
   each variable in ``site-specific``.

Once you have edited the ``site-specific`` server configuration file, you will
need to apply the changes to the servers. From ``~/Persistent/securedrop``:

.. code:: sh

  ./securedrop-admin install

.. include:: includes/rerun-install-is-safe.txt

Once the install command has successfully completed, the changes are applied.
Read the next section if you have multiple admins.

Managing ``site-specific`` updates on teams with multiple admins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Organizations with multiple admins should establish a protocol to communicate
any changes one admin makes to the ``site-specific`` configuration file on the server.

Currently, when one admin pushes changes in ``site-specific`` to the server, the
changes will not sync to the local ``site-specific`` file on the remaining admin workstations.
Without being aware of changes made to ``site-specific``, admins run the risk of pushing old
information to the servers. This can affect the receipt of OSSEC alerts, viability of the
Submission Key, among other critical components of the SecureDrop environment.

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
