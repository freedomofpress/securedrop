Source Guide
============

.. note::

   This guide provides an introduction to using SecureDrop as a source.
   It is not exhaustive, it does not address ethical or legal dimensions of
   whistleblowing, and it does not speak to other methods for confidentially
   communicating with journalists. Please proceed at your own risk. For additional
   background, also see the Freedom of the Press Foundation guide, `How to Share Sensitive
   Leaks With the Press <https://freedom.press/news/sharing-sensitive-leaks-press/>`__.


Choosing the Right Location
---------------------------

When national security is involved, we suggest you buy a new computer and a
USB flash drive, using cash. In any case you must then find a busy coworking
place or cyber cafe you don't regularly go to and sit at a place with your back
to a wall to avoid cameras capturing information on your screen or keystrokes.

Get the Tor Browser
-------------------

Each SecureDrop instance has a publicly available *Source Interface:* a website
where sources can create anonymous accounts, submit files and messages, and
check back for replies.

Each *Source Interface* is only available as an onion service, which is a
special type of website with an address ending in ".onion" that is only
accessible through Tor. Tor is an anonymizing network that makes it difficult
for anybody observing the network to associate a user's identity (e.g., their
computer's IP address) with their activity (e.g., uploading information to
SecureDrop).

The easiest and most secure way to use Tor is to download the Tor Browser from
the `Tor Project website`_. The Tor Browser is a modified version of the Firefox
web browser. It was designed to protect your security and anonymity while
using Tor. If there is a chance that downloading the Tor Browser raises
suspicion, you have a few alternatives, for example:

* If your mail provider is less likely to be monitored, you can send a mail to
  gettor@torproject.org with the text "linux", "windows" or "osx" in the body
  (for your preferred operating system) and a bot will answer with instructions.
* You can download a copy of the Tor Browser for your operating system from the
  `GitLab mirror <https://gitlab.com/thetorproject/gettorbrowser/tree/torbrowser-releases>`__.
  maintained by the Tor team.

While using the Tor Browser on your personal computer helps hide your activity
on the network, it leaves traces of its own installation on your local
machine. Your operating system may keep additional logs, for example, of the
last time you used Tor Browser.

In general, when you are trying to stay anonymous, many time-saving features of
your computer or phone turn into threats: bookmarks, recommendations,
synchronization features, shortcuts to frequently opened files, and so on. It
is very easy to make small mistakes that can endanger your anonymity, especially
if you use the same device for any other purpose.

For greater deniability and security, we recommend booting into the
`Tails operating system`_ (typically from a USB stick). Tails is specifically
designed to run on your computer without leaving traces of your activity or
saving logs. It automatically routes all of your Internet browsing through Tor
so you can easily access SecureDrop safely.

Even if you are using a dedicated computer for your SecureDrop activity that you
have never used and will never use for anything else, we recommend also using
Tails to avoid leaving traces of your activity on the computer's hard disk, in
your ISP's logs, or on cloud services.

.. important::

   Tor protects your anonymity, but third parties who can monitor your network
   traffic can detect *that you are using Tor*. They may even be able to do so
   long after your browser session, using network activity logs. This is why we
   recommend using Tor Browser from a cybercafe or coworking space you do not
   visit regularly.

.. _`Tor Project website`: https://www.torproject.org/
.. _`Tails operating system`: https://tails.boum.org/

Choose Who to Submit To
-----------------------
We recommend conducting all research related to your submission in Tor Browser.
If you are unsure whether you are using Tor, you can visit the address
https://check.torproject.org.

All organizations operating SecureDrop have a *Landing Page* that provides their
own organization-specific recommendations for using SecureDrop. We encourage you
to consider an organization's *Landing Page* before submitting to them.

.. note::

   Each SecureDrop instance is operated and administered independently by
   the organization you are submitting to. Only the journalists associated
   with that organization can see your submissions.

Most organizations make their *Landing Page* prominently accessible from their
main website's homepage (for news organizations, typically under sections called
"Tips" or "Contact us"). You can also find an incomplete list of organizations
accepting submissions through SecureDrop in the `SecureDrop Directory`_
maintained by Freedom of the Press Foundation.

Using the Tor Browser, find the ".onion" address for the *Source Interface* of
the organization that you wish to submit to.

.. tip::

   If the organization does have an entry in the SecureDrop Directory, we
   recommend comparing the address of the entry with the one on the
   organization's own *Landing Page*.

   If the two addresses don't match, please do not submit to this organization
   yet. Instead, please `contact us <https://securedrop.org/report-an-error>`__
   through the SecureDrop Website, using the Tor Browser. For additional
   security, you can use our .onion service address in Tor:

   ``secrdrop5wyphb5x.onion/report-an-error``

   We will update the directory entry if the information in it is incorrect.

Once you have located the ".onion" address, copy it into the address bar in Tor
Browser to visit the organization's *Source Interface*.

.. _`SecureDrop Directory`: https://securedrop.org/directory

Making Your First Submission
----------------------------

Open the Tor Browser and navigate to the .onion address for the SecureDrop
*Source Interface* you wish to make a submission to. The page should look similar
to the screenshot below, although it will probably have a logo specific to the
organization you are submitting to:

|Source Interface with Javascript Disabled|

If this is the first time you're using the Tor Browser, it's likely that you
have JavaScript enabled and that the Tor Browser's security setting is set
to "Low". In this case, there will be a purple warning banner at the top of
the page that encourages you to disable JavaScript and change the security
setting to "Safest":

|Source Interface Security Slider Warning|

Click the **Security Setting** link in the warning banner, and a message bubble
will pop up explaining how to adjust this setting:

|Fix Javascript warning|

Follow the instructions, and the security setting in Tor Browser should look
similar to this screenshot:

|Security Slider|

.. note::

   The "Safest" setting disables the use of JavaScript on every page you visit
   using Tor Browser, even after a browser restart. This may cause other
   websites you visit using Tor Browser to no longer work correctly, until
   you adjust the Security Setting again. We recommend keeping the setting at
   "Safest" during the entirety of the session in which you access an
   organization's SecureDrop instance.

The SecureDrop *Source Interface* should now refresh automatically and look
similar to the screenshot below. If this is the first time you are using
SecureDrop, click the **Get Started** button.

|Source Interface with Javascript Disabled|

You should now see a screen that shows the unique codename that SecureDrop has
generated for you. Note that your codename will not be the same as the codename
shown in the image below. It is extremely important that you both remember this
code and keep it secret. After submitting documents, you will need to provide
this code to log back in and check for responses.

The best way to protect your codename is to memorize it. If you cannot memorize
it right away, we recommend writing it down and keeping it in a safe place at
first, and gradually working to memorize it over time. Once you have memorized
it, you should destroy the written copy.

.. tip:: For detailed recommendations on best practices for managing your
   passphrase, check out :doc:`passphrase_best_practices`.

Once you have generated a codename and put it somewhere safe, click
**Submit Documents**.

|Memorizing your codename|

You will next be brought to the submission interface, where you may
upload a document, enter a message to send to journalists, or both. You
can only submit one document at a time, so you may want to combine
several files into a ZIP archive if necessary. The maximum submission
size is currently 500MB. If the files you wish to upload are over that
limit, we recommend that you send a message to the journalist explaining
this, so that they can set up another method for transferring the
documents.

When your submission is ready, click **Submit**.

|Submit a document|

After clicking **Submit**, a confirmation page should appear, showing
that your message and/or documents have been sent successfully. On this
page you can make another submission or view responses to your previous
messages.

|Confirmation page|

Once you are finished submitting documents, be certain you have saved your
secret codename and then click the **Log out** button:

|Logout|

The final step to clearing your session is to restart Tor Browser for
optimal security. You can either close the browser entirely or follow
the notification: click on the Tor onion in the toolbar, click
**New Identity** and then click **Yes** in the dialog box that appears
to confirm you'd like to restart Tor Browser:

|Restart TBB|


Continuing the Conversation
---------------------------

If you have already submitted a document and would like to check for
responses, click the **Log in** button on the media
organization's *Source Interface*.

|Source Interface with Javascript Disabled|

The next page will ask for your secret codename. Enter it and click
**Continue**.

|Check for response|

If a journalist has responded, their message will appear on the
next page. This page also allows you to upload another document or send
another message to the journalist. Before leaving the page, you should
delete any replies. In the unlikely event that someone learns
your codename, this will ensure that they will not be able to see the previous
correspondences you had with journalists.

|Check for a reply|

After you delete the message from the journalist, make sure you see the
below message.

|Delete received messages|

If the server is experiencing a surge in traffic, you may see the message below:

|Check for an initial response|

This will only happen once for a given codename. It means that the journalist
wants to reply to your submission, but for security reasons, they cannot do so
until you've seen this message. Log in again at a later time to see if the
journalist has responded.

Repeat these steps to continue communicating with the journalist.

.. |Source Interface Security Slider Warning| image:: images/manual/securedrop-security-slider-warning.png
.. |Security Slider| image:: images/manual/source-turn-slider-to-high.png
.. |Fix Javascript warning| image:: images/manual/security-slider-high.png
.. |Source Interface with Javascript Disabled|
  image:: images/manual/screenshots/source-index.png
.. |Memorizing your codename|
  image:: images/manual/screenshots/source-generate.png
.. |Submit a document|
  image:: images/manual/screenshots/source-submission_entered_text.png
.. |Confirmation page|
  image:: images/manual/screenshots/source-lookup.png
.. |Logout|
  image:: images/manual/screenshots/source-logout_flashed_message.png
.. |Restart TBB| image:: images/manual/restart-tor-browser.png
.. |Check for response|
  image:: images/manual/screenshots/source-enter-codename-in-login.png
.. |Check for a reply|
  image:: images/manual/screenshots/source-checks_for_reply.png
.. |Delete received messages|
  image:: images/manual/screenshots/source-deletes_reply.png
.. |Check for an initial response|
  image:: images/manual/screenshots/source-flagged.png
