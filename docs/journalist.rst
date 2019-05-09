Journalist Guide
================

.. include:: ./includes/provide-feedback.txt

This guide presents an overview of the SecureDrop system for a
journalist. It covers the core functions necessary to start working
with the platform: logging in securely, viewing documents, editing
documents, and interacting with sources.

Updating Your Workstation
-------------------------

You should keep your SecureDrop workstations updated with:

* **Tails updates**
* **SecureDrop workstation updates**

You should apply Tails updates to your Tails drive as they are released, as they
often contain critical security fixes. The *Journalist Workstation* Tails drive, once booted and
connected to Tor, will alert you if upgrades are available. For most Tails
upgrades, you can simply follow the steps in the Tails Upgrader that appears on
screen to update your Tails drive. However, sometimes Tails upgrades are "manual"
which means that you should follow the instructions in
`Tails Upgrade Documentation`_ to upgrade the drives. Talk to your SecureDrop
administrator if you have trouble.

.. include:: includes/update-gui.txt

.. _`Tails
   Upgrade Documentation`: https://tails.boum.org/doc/first_steps/upgrade/index.en.html


Creating a GPG Key
------------------

Each journalist needs a personal GPG key for encrypting files. A GPG
key has two parts: a *public key* and a *private key*. The private
key, used for decryption, stays on the *Journalist Workstation*. The
public key, used for encryption, is copied to the *Secure Viewing
Station*.

If you do not yet have a GPG key, follow the instructions for your
operating system to set one up:

- `GNU/Linux <https://ssd.eff.org/en/module/how-use-pgp-linux>`__
- `Windows <https://ssd.eff.org/en/module/how-use-pgp-windows>`__
- `Mac OS <https://ssd.eff.org/en/module/how-use-pgp-mac-os-x>`__

Connecting to the *Journalist Interface*
----------------------------------------

Journalists viewing documents on SecureDrop must connect to the
*Journalist Interface* using the `Tails operating system
<https://tails.boum.org/>`__ on a USB drive. Your admin can
help provide you with a Tails drive.

.. important:: See our guide on setting up :doc:`Tails for the Admin
          and Journalist Workstation <tails_guide>` before continuing.

.. note:: The Tails OS makes using SecureDrop very different from
          other computing experiences. The added layers of security
          mean extra steps each time you want to login. With practice,
          you will become increasingly comfortable with the process.

Each journalist has an authenticated Tor hidden service URL for
logging in to the *Journalist Interface*. This must be done using the
Tails operating system. Click the *Journalist Interface* icon on the
desktop. This will open Tor Browser to a ".onion" page. Log in with
your username, passphrase, and two-factor authentication token, as
shown in the first screenshot below. (See :doc:`Using YubiKey with the
Journalist Interface <yubikey_setup>`.)

|Journalist Interface Login|

Reset Passphrase or Two-factor Authentication Token
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If necessary journalists may reset their user passphrase or two-factor authentication token in their user profile. To navigate to your user profile, log in to the *Journalist Interface* and click on the link in the upper right of the screen where it says **Logged on as <your user name>.**

If you have lost or forgotten your passphrase or two-factor authentication device, you will need to contact your SecureDrop admin for assistance.

|Journalist account profile|

Daily Journalist Alerts About Submissions
-----------------------------------------

When a SecureDrop has little activity and receives only a few
submissions every other week, checking the *Journalist Interface*
daily only to find there is nothing is a burden. It is more convenient
for journalists to be notified daily via encrypted email about whether
or not there has been submission activity in the past 24 hours.

If the email shows submissions were received, the journalist can
connect to the *Journalist Interface* to get them.

This is an optional feature that must be activated :doc:`by the
administrator <admin>`. In the simplest case a journalist provides
her/his email and GPG public key to the admin. If a team of journalist
wants to receive these daily alerts, they should share a GPG key and
ask the admin to setup a mail alias (SecureDrop does not provide that
service) so they all receive the alerts and are able to decrypt them.

Interacting With Sources
------------------------

If any sources have uploaded documents or sent messages, they will be
listed on the homepage by codename.

|Journalist Interface|

.. note:: Codenames that journalists see are different than the
          codenames visible to sources.

Click on a codename to see the dedicated page for that source. You
will see all of the messages that they have written and documents that
they have uploaded. If the name of a source is difficult to say or
remember, you can rename a source using the **Change codename** button
next to their current codename.

|Cycle source codename|

.. tip:: You can also **Star** interesting or promising sources to
         easily return to them later.

If you want to reply to the source, write your message in the text
field and click **Submit**.

|Sent reply|

Once your reply has been successfully submitted, you will be returned
to the source page and see a message confirming that the reply was
stored. The source will see your reply the next time they log in with
their unique codename. To minimize the impact of a source codename
being compromised, the source interface encourages the source to delete
the reply after reading it. Once a source has read your reply and deleted
it from their inbox, a checkmark will appear next to the reply in the interface.

.. note:: Prior to SecureDrop 0.9.0, replies when deleted from the source inbox
  would also disappear from the journalist inbox. As such, if there are older
  conversations, there may be discontinuities in the conversation.

You may also delete replies if you change your mind after sending them.

Documents and messages are encrypted to the SecureDrop installation's
*Submission Public Key*. In order to read the messages or look at the documents
you will need to transfer them to the *Secure Viewing Station*, which holds
the *Submission Private Key*. To recall the conversation history between your
organization and sources, you can also download replies and transfer them to the
*Secure Viewing Station* for decryption.

Flag for Reply
~~~~~~~~~~~~~~

If the server experiences a large number of new sources signing up at
once and is overloaded with submissions, you will need to flag sources
for reply before you can communicate with them. Click the **Flag this
source for reply** button.

|Flag for reply button|

After clicking the **Flag this source for reply** button, you will see
this confirmation page. Click through to get back to the page that
displays that source's documents and replies.

|Flag for reply notification|

You will not be able to reply until after the source logs in again and
sees that you would like to talk to them. So you may have to sit and wait. After
the source sees that you'd like to reply, a GPG key pair will automatically be
generated and you can log back in and send a reply.

Moving Documents to the *Secure Viewing Station*
------------------------------------------------

Documents sent by sources can only be viewed on the *Secure Viewing
Station*. After clicking on an individual source, you will see the
page below with any messages that source has sent you. Click on a
document or message name to save it, or select a number of documents
and save them all at once by clicking **Download Selected**.

|Load external content|

A dialog box will appear asking if you want to **Open** or **Save**
the file. Select **Save File**:

|Download selected|

In order to protect you from malware, the browser in Tails will only
allow you to download documents to a special persistent folder located
at ``/home/amnesia/Tor Browser``.

|Download to sandbox folder|

.. tip:: The special folder mentioned here is called **Tor Browser**,
         not "Persistent." Attempting to download directly into the
         **Persistent** folder will only lead to frustration.

Once downloaded to this folder, move the document to the designated
USB stick you intend to use to transfer the documents from your
*Journalist Workstation* to the *Secure Viewing Station*. This storage
device will be known as your *Transfer Device*.

|Move to transfer device 1|

|Move to transfer device 2|

Eject the *Transfer Device* from the *Journalist Workstation*.

Next, boot up the *Secure Viewing Station* using Tails and enter the
passphrase for the *Secure Viewing Station* persistent volume. Once you
have logged in, plug in the *Transfer Device*.

.. note:: The *Secure Viewing Station* and *Journalist Workstation*
          are on separate Tails USB drives.

Click on the computer icon on your desktop, then on the *Transfer
Device*. Drag and drop the file into your **Persistent** folder.

.. important:: Copy these documents to the **Persistent** folder *before*
             decrypting them. Otherwise you might accidentally decrypt
             the documents on the USB stick, and they could be
             recoverable in the future.

|Copy files to persistent|

After successfully copying, erase the files from your *Transfer
Device* by returning to the *Transfer Device* folder. Right click on
the files that need removal and click "Wipe" to securely delete the
files from your device.

Decrypting on the *Secure Viewing Station*
------------------------------------------

To decrypt documents, return to your **Persistent** folder and
double-click on the zipped file folder. After you extract the files,
click on each file individually. If you have configured a passphrase during
the generation of your *Submission Key*, you will be prompted for it.

|Decrypting|

When you decrypt the file it will have the same filename, but without
".gpg" at the end.

|Decrypted documents|

You can now double-click on the decrypted file to open it in its
default application.

|Opened document|

If the default application does not work, you can right-click on the
document and choose **Open with Other Application...** to try opening
the document with OpenOffice Writer, or Document Viewer. You might
also need to right-click on a file and choose **Rename...** to rename
a document with a proper file extension (for example, ".jpg" instead
of ".jpeg").

Working with Documents
----------------------

This section describes how to handle unusual file formats, safely research
submissions, remove metadata, and mitigate risks from submitted malware.

Handling File Formats
~~~~~~~~~~~~~~~~~~~~~

SecureDrop accepts submissions of any file type. Tails comes with
pre-installed applications for securely working with documents, including
`the Tor Browser <https://www.torproject.org/>`__, an office suite, graphics
tools, desktop publishing tools, audio tools, and printing and scanning tools.

Pre-Encrypted Submissions
`````````````````````````

SecureDrop sources can optionally encrypt prior to submitting to SecureDrop.
This means that once you decrypt the document as you usually do by double
clicking the document in the file navigator, there will be another layer of
encryption.

Most often, the file will be encrypted to the SecureDrop key. If the file is
encrypted to your SecureDrop key, you should be able to double click the file as
usual once more in the SVS and it should decrypt.

However, it's also possible the file is encrypted to another key, potentially
your personal key. If this occurs, you will get an error message in Tails that
reads "Decryption failed. You probably do not have the decryption key".
To determine which key was used, if you are comfortable at the command line, you
can open the ``Terminal``, navigate to the file, and use:

.. code:: sh

  gpg --decrypt NAME_OF_FILE

replacing ``NAME_OF_FILE`` with the name of the file you wish to decrypt. This
command will tell you what key was used to encrypt the file. If you are not
comfortable at the command line, contact your SecureDrop admin or
Freedom of the Press Foundation for assistance.

.. warning:: **Do not** transfer source material off the *Secure Viewing Station*
             for decryption. Instead, transfer cryptographic keys *to* the SVS
             device for decryption and metadata removal.

Researching Submissions
~~~~~~~~~~~~~~~~~~~~~~~

Journalists should take care to research submissions using the Tor
Browser, ideally in a new Tails session for highly sensitive
submissions. For more information, visit the Tails guide to `working
with sensitive documents`_.

Removing Metadata
~~~~~~~~~~~~~~~~~

.. tip:: For detailed information about removing metadata from documents, check out
         this in-depth `guide to removing metadata`_.

Tails also comes with the `Metadata Anonymisation Toolkit`_ (MAT) that
is used to help strip metadata from a variety of types of files,
including png, jpg, OpenOffice/LibreOffice documents, Microsoft Office
documents, pdf, tar, tar.bz2, tar.gz, zip, mp3, mp2, mp1, mpa, ogg,
and flac. You can open MAT by clicking **Applications** in the top
left corner, Accessories, Metadata Anonymisation Toolkit.

We recommend always doing as much work as possible inside of Tails
before copying documents back to your *Journalist Workstation*. This
includes stripping metadata with MAT.

.. warning:: MAT is no longer actively maintained and **will not**
             strip all metadata, even when the output claims the
             document is clean. Some metadata are likely to persist:
             you must **never** assume MAT has removed all metadata.

When you no longer need documents, you can right-click on them and
choose **Wipe** to delete them.

|Wiping documents|

.. _`guide to removing metadata`: https://freedom.press/training/everything-you-wanted-know-about-media-metadata-were-afraid-ask/

Risks From Malware
~~~~~~~~~~~~~~~~~~

As long as you are using the latest version of Tails, you should be
able to open submitted documents with a low risk of malicious
files compromising the *Secure Viewing Station*. However, even if a
compromise does occur, Tails is designed so that the next time you
reboot, the malware will be gone.

`Never scan QR codes`_ from the *Secure Viewing Station* using a network
connected device. These QR codes can contain links that your connected device
will automatically visit. In general, you should take care when opening any
links provided in a SecureDrop submission, as this can leak information to third
parties. If you are unsure if a link is safe to click, you should consult your
digital security staff or Freedom of the Press Foundation for assistance.

.. _`Never scan QR codes`: https://securedrop.org/news/security-advisory-do-not-scan-qr-codes-submitted-through-securedrop-connected-devices
.. _`working with sensitive documents`: https://tails.boum.org/doc/sensitive_documents/index.en.html
.. _`Metadata Anonymisation Toolkit`: https://mat.boum.org/

Encrypting and Moving Documents to the *Journalist Workstation*
---------------------------------------------------------------

Before moving documents back to the *Transfer Device* to copy them to
your workstation, encrypt them to your personal GPG key that you
imported when setting up the *Secure Viewing Station*.

To do this, right-click on the document you want to encrypt and choose
**Encrypt...**.

|Encrypting 1|

Then choose your public key (and, if you choose, any additional keys,
such as an editor's) and click **OK**.

|Encrypting 2|

When you are done encrypting, you will have another document with the
same filename but ending in ".gpg". This file is encrypted to the GPG
keys you selected. You can safely copy these encrypted files to the
*Transfer Device* to transfer them to your workstation.

|Encrypted document|

Decrypting and Preparing to Publish
-----------------------------------

Plug the *Transfer Device* into your workstation computer and copy
over the encrypted documents. Decrypt them with GPG.

You are now ready to write articles and blog posts, edit video and
audio, and begin publishing important, high-impact work!

.. tip:: Check out our SecureDrop :doc:`Promotion Guide
         <getting_the_most_out_of_securedrop>` to read about
         encouraging sources to use SecureDrop.

.. |Journalist Interface Login| image:: images/manual/screenshots/journalist-index_with_text.png
.. |Journalist Interface| image:: images/manual/screenshots/journalist-index_javascript.png
.. |Load external content| image:: images/manual/screenshots/journalist-clicks_on_source_and_selects_documents.png
.. |Download selected| image:: images/manual/tbb_Document5.png
.. |Download to sandbox folder| image:: images/manual/tbb_Document6.png
.. |Move to transfer device 1| image:: images/manual/tbb_Document7.png
.. |Move to transfer device 2| image:: images/manual/tbb_Document8.png
.. |Copy files to persistent| image:: images/manual/viewing1.png
.. |Decrypting| image:: images/manual/viewing2.png
.. |Decrypted documents| image:: images/manual/viewing3.png
.. |Opened document| image:: images/manual/viewing4.png
.. |Cycle source codename| image:: images/manual/change-codename.png
.. |Sent reply| image:: images/manual/screenshots/journalist-composes_reply.png
.. |Flag for reply button| image:: images/manual/screenshots/journalist-col_has_no_key.png
.. |Flag for reply notification| image:: images/manual/screenshots/journalist-col_flagged.png
.. |Wiping documents| image:: images/manual/viewing5.png
.. |Encrypting 1| image:: images/manual/viewing6.png
.. |Encrypting 2| image:: images/manual/viewing7.png
.. |Encrypted document| image:: images/manual/viewing8.png
.. |Journalist account profile| image:: images/manual/screenshots/journalist-edit_account_user.png
