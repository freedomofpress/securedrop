Test the Installation
=====================

Test connectivity
-----------------

#. SSH to both servers over Tor

   - On the Admin Workstation, you should be able to SSH to the App
     Server and the Monitor Server. ::

       $ ssh <username>@<app .onion>
       $ ssh <username>@<mon .onion>

   - If you set up :ref:`SSH Host Aliases` during the post-install
     setup for the Admin Workstation, you should be able to connect
     with the aliases: ::

       $ ssh app
       $ ssh mon

Sanity-check the install
------------------------

On each server:

#. Check that you can execute privileged commands by running ``sudo su``.
#. Verify that you are booted into a grsec kernel: run ``uname -r``
   and verify that the name of the running kernel ends with ``-grsec``.
#. Check the AppArmor status with ``sudo aa-status``. On a production
   instance all profiles should be in enforce mode.
#. Check the current applied iptables rules with ``iptables-save``. It
   should output *approximately* 50 lines.
#. You should have received an email alert from OSSEC when it first
   started. If not, review our :doc:`OSSEC Alerts
   Guide <ossec_alerts>`.

Test the web interfaces
-----------------------

#. Make sure the Source Interface is available, and that you can make a
   submission.

   - Do this by opening the Tor Browser and navigating to the onion
     URL from ``app-source-ths``. Proceed through the codename
     generation (copy this down somewhere) and you can submit a
     message or attach any random unimportant file.
   - Usage of the Source Interface is covered by our :doc:`Source User
     Manual <source>`.

#. Test that you can access the Document Interface, and that you can log
   in as the admin user you just created.

   - Open the Tor Browser and navigate to the onion URL from
     app-document-aths. Enter your password and two-factor
     authentication code to log in.
   - If you have problems logging in to the Admin/Document Interface,
     SSH to the App Server and restart the ntp daemon to synchronize
     the time: ``sudo service ntp restart``. Also check that your
     smartphone's time is accurate and set to network time in its
     device settings.

#. Test replying to the test submission.

   - While logged in as an admin, you can send a reply to the test
     source submission you made earlier.
   - Usage of the Document Interface is covered by our :doc:`Journalist
     User Manual <journalist>`.

#. Test that the source received the reply.

   - Within Tor Browser, navigate back to the app-source-ths URL and
     use your previous test source codename to log in (or reload the
     page if it's still open) and check that the reply you just made
     is present.

#. We highly recommend that you create persistent bookmarks for the
   Source and Document Interface addresses within Tor Browser.

#. Remove the test submissions you made prior to putting SecureDrop to
   real use. On the main Document Interface page, select all sources and
   click 'Delete selected'.

Once you've tested the installation and verified that everything is
working, see :doc:`How to Use SecureDrop <journalist>`.
