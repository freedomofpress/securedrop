Test the Installation
=====================

Test Connectivity
-----------------

SSH to Both Servers Over Tor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming you haven't disabled ssh over tor, SSH access will be
restricted to the tor network.

On the *Admin Workstation*, you should be able to SSH to the *Application Server* and the *Monitor Server*. ::

   ssh app
   ssh mon

The SSH aliases should have been configured automatically by running
the ``./securedrop-admin tailsconfig`` tool. If you're unable to connect via aliases,
try using the verbose command format to troubleshoot: ::

   ssh <username>@<app .onion>
   ssh <username>@<mon .onion>

.. tip:: If your instance uses v2 onion services, you can find the Onion
         URLs for SSH in ``app-ssh-aths`` and ``mon-ssh-aths`` inside the
         ``install_files/ansible-base`` directory. If your instance uses v3
         onion services, check the ``app-ssh.auth_private`` and
         ``mon-ssh.auth_private`` files instead.

Log in to Both Servers via TTY
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All access to the SecureDrop servers should be performed over SSH from the
*Admin Workstation*. To aid in troubleshooting, login via a physical keyboard
attached to the server is also supported.

Sanity-Check the Installation
-----------------------------

On each server:

#. Check that you can execute privileged commands by running ``sudo su``.
#. Verify that you are booted into a grsec kernel: run ``uname -r``
   and verify that the name of the running kernel ends with ``-grsec``.
#. Check the current applied iptables rules with ``iptables-save``. It
   should output *approximately* 50 lines.
#. You should have received an email alert from OSSEC when it first
   started. If not, review our :doc:`OSSEC Alerts
   Guide <ossec_alerts>`.

On the *Application Server*:

#. Check the AppArmor status with ``sudo aa-status``. On a production
   instance all profiles should be in ``enforce`` mode.

Test the Web Interfaces
-----------------------

#. Make sure the *Source Interface* is available, and that you can make a
   submission.

   - Open the *Source Interface* in the Tor Browser by clicking on its desktop
     shortcut. Proceed through the codename
     generation (copy this down somewhere) and submit a
     test message or file.
   - Usage of the Source Interface is covered by our :doc:`Source User
     Manual <source>`.

#. Test that you can access the *Journalist Interface*, and that you can log
   in as the admin user you just created.

   - Open the *Journalist Interface* in the Tor Browser by clicking on its desktop
     shortcut.  Enter your passphrase and two-factor code to log in.
   - If you have problems logging in to the *Admin/Journalist Interface*,
     SSH to the *Application Server* and restart the ntp daemon to synchronize
     the time: ``sudo service ntp restart``. Also check that your
     smartphone's time is accurate and set to network time in its
     device settings.

#. Test replying to the test submission.

   - While logged in as an admin, you can send a reply to the test
     source submission you made earlier.
   - Usage of the *Journalist Interface* is covered by our :doc:`Journalist
     User Manual <journalist>`.

#. Test that the source received the reply.

   - Within Tor Browser, navigate back to the *Source Interface* and
     use your previous test source codename to log in (or reload the
     page if it's still open) and check that the reply you just made
     is present.

#. Remove the test submissions you made prior to putting SecureDrop to
   real use. On the main *Journalist Interface* page, select all sources and
   click **Delete selected**.

Once you've tested the installation and verified that everything is
working, see :doc:`How to Use SecureDrop <journalist>`.
