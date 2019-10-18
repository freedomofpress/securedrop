Generate the *Submission Key*
=============================

When a document or message is submitted to SecureDrop by a source, it is
automatically encrypted with the *Submission Key*. The private part
of this key is only stored on the *Secure Viewing Station* which is never
connected to the Internet. SecureDrop submissions can only be decrypted and
read on the *Secure Viewing Station*.

We will now generate the *Submission Key*. If you aren't still logged into your
*Secure Viewing Station* from the previous step, boot it using its Tails USB
stick, with persistence enabled.

.. important:: Do not follow these steps before you have fully configured the
  *Secure Viewing Station* according to the :doc:`instructions <set_up_svs>`.
  The private key you will generate in the following steps is one of the most
  important secrets associated with your SecureDrop installation. This procedure
  is intended to ensure that the private key is protected by the air-gap
  throughout its lifetime.

Create the Key
--------------

#. Navigate to **Applications ▸ Terminal** to open a terminal |Terminal|.
#. In the terminal, run ``gpg --full-generate-key``:

   |GPG generate key|

#. When it says **Please select what kind of key you want**, choose "*(1) RSA
   and RSA (default)*".
#. When it asks **What keysize do you want?**, type ``4096``.
#. When it asks **Key is valid for?**, press Enter. This means your key does
   not expire.
#. It will let you know that this means the key does not expire at all and ask
   for confirmation. Type **y** and hit Enter to confirm.

   |GPG key options|

#. Next it will prompt you for user ID setup. Use the following options:
     - **Real name**: "SecureDrop"
     - **Email address**: leave this field blank
     - **Comment**: ``[Your Organization's Name] SecureDrop Submission Key``

#. GPG will confirm these options. Verify that everything is written correctly.
   Then type ``O`` for ``(O)kay`` and hit enter to continue:

   |OK to generate|

#. A box will pop up (twice) asking you to type a passphrase. Since the key is
   protected by the encryption on the Tails persistent volume, it is safe to
   simply click **OK** without entering a passphrase.
#. The software will ask you if you are sure. Click **Yes, protection is not
   needed**.
#. Wait for the key to finish generating.

Export the *Submission Public Key*
----------------------------------

To manage GPG keys using the graphical interface (a program called "Passwords
and Keys"), click the clipboard icon |gpgApplet| in the top right corner and
select "Manage Keys". Click "GnuPG keys" and you should see the key that you just
generated.

|My Keys|

#. Select the key you just generated and click "File" then "Export".
#. Save the key to the *Transfer Device* as ``SecureDrop.asc``, and make
   sure you change the file type from "PGP keys" to "Armored PGP keys" which
   can be switched at the bottom of the Save window. Click the 'Export' button
   after switching to armored keys.

.. note:: This is the public key only.

|Export Key|

|Export Key 2|

You'll need to provide the fingerprint of this new key during the
installation.  Double-click on the newly generated key and change to the
*Details* tab. Write down the 40 hexadecimal digits under *Fingerprint*.

|Fingerprint|

.. note:: Your fingerprint will be different from the one in the example
          screenshot.

At this point, you are done with the *Secure Viewing Station* for now. You
can shut down Tails, grab the *Admin Workstation* Tails USB and move over to your regular
workstation.

.. |GPG generate key| image:: images/install/run_gpg_gen_key.png
.. |GPG key options| image:: images/install/key_options.png
.. |OK to generate| image:: images/install/ok_to_generate.png
.. |gpgApplet| image:: images/gpgapplet.png
.. |My Keys| image:: images/install/keyring.png
.. |Export Key| image:: images/install/exportkey.png
.. |Export Key 2| image:: images/install/exportkey2.png
.. |Fingerprint| image:: images/install/fingerprint.png
.. |Terminal| image:: images/terminal.png
