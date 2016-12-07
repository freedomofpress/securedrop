Generate the SecureDrop Submission Key
======================================

When a document or message is submitted to SecureDrop by a source, it is
automatically encrypted with the *SecureDrop Submission Key*. The
private part of this key is only stored on the *Secure Viewing Station*
which is never connected to the Internet. SecureDrop submissions can
only be decrypted and read on the *Secure Viewing Station*.

We will now generate the *SecureDrop Submission Key* on the
*Secure Viewing Station*.

Correct the system time
-----------------------

After booting up Tails on the *Secure Viewing Station*, you will need to
manually set the system time before you create the *SecureDrop
Submission Key*. To set the system time:

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
-  When it says *Please select what kind of key you want*, choose
   *(1) RSA and RSA (default)*.
-  When it asks *What keysize do you want?*, type ``4096``.
-  When it asks *Key is valid for?*, press Enter to keep the default.
-  When it asks *Is this correct?*, verify that you've entered
   everything correctly so far, then type ``y``.
-  For *Real name*, type: ``SecureDrop``
-  For *Email address*, leave the field blank and press Enter
-  For *Comment*, type
   ``[Your Organization's Name] SecureDrop Submission Key``
-  Verify that everything is correct so far, then type ``o`` for
   ``(O)kay``
-  It will pop up a box asking you to type a passphrase, but it's safe
   to click okay without typing one. The key is protected by the
   encryption on the Tails persistent volume.
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

.. todo:: I would prefer a filename of ``SecureDrop.pub.asc``, as that
          explicitly denotes the file is a public key and is
          ASCII-armored.

.. note:: This is the public key only.

|Export Key|

|Export Key 2|

.. todo:: The screenshot shows them saving the public key with a
          filename of ``SecureDrop.asc``. The screenshot should be
          consistent with the recommendations in the text of the docs.

You'll need to provide the fingerprint of this new key during the
installation.  Double-click on the newly generated key and change to
the *Details* tab. Write down the 40 hexadecimal digits under
*Fingerprint*.

|Fingerprint|

.. note:: Your fingerprint will be different from the one in the
          example screenshot.

Import GPG keys for journalists with access to SecureDrop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. todo:: This is the wrong place for this. The first phase of the
          documentation should be focused just on installing
          SecureDrop. We should have a whole separate section for
          onboarding journalists.

While working on a story, journalists may need to transfer some
documents or notes from the *Secure Viewing Station* to the journalist's
work computer on the corporate network. To do this, the journalists
should re-encrypt them with their own keys. If a journalist does not
already have a personal GPG key, they can follow the same steps
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
