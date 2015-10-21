Finalizing the Installation
===========================

Some of the final configuration is included in these testing steps, so
*do not skip them!*

Test the web application and connectivity
-----------------------------------------

#. SSH to both servers over Tor

-  As an admin running Tails with the proper HidServAuth values in your
   ``/etc/torrc`` file, you should be able to SSH directly to the App
   Server and Monitor Server.
-  Post-install you can now SSH *only* over Tor, so use the onion URLs
   from app-ssh-aths and mon-ssh-aths and the user created during the
   Ubuntu installation i.e. ``ssh <username>@m5apx3p7eazqj3fp.onion``.

#. Make sure the Source Interface is available, and that you can make a
   submission.

-  Do this by opening the Tor Browser and navigating to the onion URL
   from ``app-source-ths``. Proceed through the codename generation
   (copy this down somewhere) and you can submit a message or attach any
   random unimportant file.
-  Usage of the Source Interface is covered by our `Source User
   Manual </docs/source_user_manual.md>`__.

#. Test that you can access the Document Interface, and that you can log
   in as the admin user you just created.

-  Open the Tor Browser and navigate to the onion URL from
   app-document-aths. Enter your password and two-factor authentication
   code to log in.
-  If you have problems logging in to the Admin/Document Interface, SSH
   to the App Server and restart the ntp daemon to synchronize the time:
   ``sudo service ntp restart``. Also check that your smartphone's time
   is accurate and set to network time in its device settings.

#. Test replying to the test submission.

-  While logged in as an admin, you can send a reply to the test source
   submission you made earlier.
-  Usage of the Document Interface is covered by our `Journalist User
   Manual </docs/journalist_user_manual.md>`__.

#. Test that the source received the reply.

-  Within Tor Browser, navigate back to the app-source-ths URL and use
   your previous test source codename to log in (or reload the page if
   it's still open) and check that the reply you just made is present.

#. We highly recommend that you create persistent bookmarks for the
   Source and Document Interface addresses within Tor Browser.
#. Remove the test submissions you made prior to putting SecureDrop to
   real use. On the main Document Interface page, select all sources and
   click 'Delete selected'.

Once you've tested the installation and verified that everything is
working, see `How to Use
SecureDrop </docs/journalist_user_manual.md>`__.

Additional testing
------------------

#. On each server, check that you can execute privileged commands by
   running ``sudo su``.
#. Run ``uname -r`` to verify you are booted into grsecurity kernel. The
   string ``grsec`` should be in the output.
#. Check the AppArmor status on each server with ``sudo aa-status``. On
   a production instance all profiles should be in enforce mode.
#. Check the current applied iptables rules with ``iptables-save``. It
   should output *approximately* 50 lines.
#. You should have received an email alert from OSSEC when it first
   started. If not, review our `OSSEC Alerts
   Guide </docs/ossec_alerts.md>`__.

If you have any feedback on the installation process, please let us
know! We're always looking for ways to improve, automate and make things
easier.

