2FA for app and mon servers
===========================

As part of the SecureDrop installation process, you will need to set
up two-factor authentication (2FA) using the FreeOTP app for both the
*Application* and *Monitor Servers*.

Connect to each of the servers using ``ssh`` and run ``google-authenticator``.
Follow the prompts, saying "yes" when prompted for a "yes/no" response. When
you've finished, open the FreeOTP app on your smartphone and
follow the steps below.

.. include:: includes/otp-app.txt

- Tap the QRcode symbol at the top
- Scan the barcode using your phone's camera

A new entry will automatically be added to the list. If you wish to edit
this entry and give it a new name, do the following:

- Tap on the three vertical dots at the right of the line
- Select ``Edit``

To get a two-factor authentication token tap on the line. Six digits
will show: they are the token. A timer to the left shows how much of
the 30 seconds remains before it expires. If it is about to expire you
can just wait and a new token will display and you'll have 30 seconds
to use it.

Once you've properly set up the first server, repeat these steps again
on the other.
