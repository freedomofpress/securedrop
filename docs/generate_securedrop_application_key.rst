Generate the *SecureDrop Application GPG Key*
=============================================

.. todo:: Tom complained about the name "SecureDrop Application GPG
          Key". It's verbose, and "application key" is kind of vague
          (what is its function within the application?). "SecureDrop
          Submission Key" might be a better name.

When a document or message is submitted to SecureDrop by a source, it is
automatically encrypted with the *SecureDrop Application GPG Key*. The
private part of this key is only stored on the *Secure Viewing Station*
which is never connected to the Internet. SecureDrop submissions can
only be decrypted and read on the *Secure Viewing Station*.

We will now generate the *SecureDrop Application GPG Key*.

Correct the system time
-----------------------

After booting up Tails on the *Secure Viewing Station*, you will need to
manually set the system time before you create the *SecureDrop
Application GPG Key*. To set the system time:

#. Right-click the time in the top menu bar and select *Adjust Date &
   Time.*
#. Click *Unlock* in the top-right corner of the dialog window and enter
   your temporary Tails administration password.
#. Set the correct time, region and city.
#. Click *Lock*, enter your temporary Tails administration password one
   more time and wait for the system time to update in the top panel.

Once that's done, follow the steps below to create the key.

Create the key
--------------

-  Open a terminal |Terminal| and run ``gpg --gen-key``
-  When it says, ``Please select what kind of key you want``, choose
   ``(1) RSA and RSA (default)``
-  When it asks, ``What keysize do you want?`` type **``4096``**
-  When it asks, ``Key is valid for?`` press Enter to keep the default
-  When it asks, ``Is this correct?`` verify that you've entered
   everything correctly so far, and type ``y``
-  For ``Real name`` type: ``SecureDrop``
-  For ``Email address``, leave the field blank and press Enter
-  For ``Comment`` type
   ``[Your Organization's Name] SecureDrop Application GPG Key``
-  Verify that everything is correct so far, and type ``o`` for
   ``(O)kay``
-  It will pop up a box asking you to type a passphrase, but it's safe
   to click okay without typing one (since your persistent volume is
   encrypted, this GPG key is already protected)
-  Wait for your GPG key to finish generating

To manage GPG keys using the graphical interface (a program called
Seahorse), click the clipboard icon |gpgApplet| in the top right corner
and select "Manage Keys". You should see the key that you just generated
under "GnuPG Keys."

|My Keys|

Select the key you just generated and click "File" then "Export". Save
the key to the *Transfer Device* as ``SecureDrop.pgp``, and make sure
you change the file type from "PGP keys" to "Armored PGP keys" which can
be switched right above the 'Export' button. Click the 'Export' button
after switching to armored keys.

NOTE: This is the public key only.

|Export Key|
|Export Key 2|

You'll need to verify the fingerprint for this new key during the
``App Server`` installation. Double-click on the newly generated key and
change to the ``Details`` tab. Write down the 40 hexadecimal digits
under ``Fingerprint``. (Your GPG key fingerprint will be different than
what's in this photo.)

|Fingerprint|

Import GPG keys for journalists with access to SecureDrop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

While working on a story, journalists may need to transfer some
documents or notes from the *Secure Viewing Station* to the journalist's
work computer on the corporate network. To do this, the journalists
should re-encrypt them with their own keys. If a journalist does not
already have a personal GPG key, he or she can follow the same steps
above to create one. The journalist should store the private key
somewhere safe; the public key should be stored on the *Secure Viewing
Station*.

If the journalist does have a key, transfer their public key from
wherever it is located to the *Secure Viewing Station*, using the
*Transfer Device*. Open the file manager |Nautilus| and double-click on
the public key to import it. If the public key is not importing, rename
the file to end in ".asc" and try again.

|Importing Journalist GPG Keys|

At this point, you are done with the *Secure Viewing Station* for now.
You can shut down Tails, grab the *admin Tails USB* and move over to
your regular workstation.

.. |gpgApplet| image:: images/gpgapplet.png
.. |My Keys| image:: images/install/keyring.png
.. |Export Key| image:: images/install/exportkey.png
.. |Export Key 2| image:: images/install/exportkey2.png
.. |Fingerprint| image:: images/install/fingerprint.png
.. |Nautilus| image:: images/nautilus.png
.. |Importing Journalist GPG Keys| image:: images/install/importkey.png
.. |Terminal| image:: images/terminal.png
