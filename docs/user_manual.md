# How to Use SecureDrop

## SecureDrop Depends on the Tor Browser

Sources submitting documents or messages to SecureDrop, and the journalists viewing this correspondence, must connect to the respective Source or Document Interface using the Tor network, free software that makes users' internet activity much more difficult to trace. The easiest and most secure way to use Tor is to download the Tor Browser Bundle from https://www.torproject.org/. This bundle installs the Tor browser, as well as an application that is used to connect to the Tor network.

The Tor Browser can be used to access Tor _hidden service URLs_, which have domain names that end in ".onion". Media organizations will provide links to the .onion URLs of their SecureDrop pages, and each journalist that uses SecureDrop connects to the service with his or her own personal .onion URL.

## Using SecureDrop As a Source

Open the Tor Browser and navigate to the .onion hidden service URL provided by the media organization whose SecureDrop page you would like to visit. The page should look similar to the screenshot below. If this is the first time you're using the Tor browser, it's likely that you have Javascript enabled. If you do, you will see the red warning below which will explainin that this is a security risk. If you don't have Javascript enabled, you can skip the next step.

![Javascript warning](/docs/images/manual/source1.png)

Click the `Click here` link on the Javascript warning and a message will pop up telling you how to disable Javascript. Once you follow the instructions, refresh the page.

![Fix Javascript warning](/docs/images/manual/source2.png)

The page should now look similar to the screenshot below. If this is the first time you are using SecureDrop, click the `Submit Documents` button.

![Source Interface](/docs/images/manual/source3.png)

You should now see a screen that shows the unique code name that SecureDrop has generated for you. In the example screenshot below the codename is `bough fisk jed sold essen nail 1 prissy`, but yours will be different. It is extremely important that you both remember this code and keep it secret. Memorize the code or write it down and keep it in a safe place, but do not save it on your computer. After submitting documents, you will need to provide this code to log back in and check for responses.

SecureDrop allows you to choose the length of your code name, in case you want to create a longer code name for extra security. Once you have generated a code name and put it somewhere safe, click `Continue`.

![Memorizing your code name](/docs/images/manual/source4.png)

You will next be brought to the submission interface, where you may upload a document, enter a message to send to journalists, or both. You can only submit one document at a time, so you may want to combine several files into a zip archive if necessary. When your submission is ready, click `Submit`.

![Submit a document](/docs/images/manual/source5.png)

After clicking `Submit`, a confirmation page should appear, showing that your message and/or documents have been sent successfully. On this page you can make another submission or view responses to your previous messages.

![Confirmation page](/docs/images/manual/source6.png)

If you have already submitted a document and would like to check for responses, click the `Check for a Response` button on the media organizations' SecureDrop homepage.

![Source Interface](/docs/images/manual/source7.png)

The next page will ask for your secret code name; enter it and click `Continue`.

![Check for response](/docs/images/manual/source8.png)

If a journalist wishes to reply to you, they will flag your message on their end and you will see the following message below. They can't reply to you until you've seen this message for security reasons. This will only happen the first time a journalist replies and with subsequent replies you will skip this step.

![Check for an initial response](/docs/images/manual/source9.png)

Click `Refresh` or log in again. If a journalist has responded, his or her message will appear on the next page. This page also allows you to upload another document or send another message to the journalist. Be sure to delete any messages here before navigating away.

![Check for a real response](/docs/images/manual/source10.png)

After you delete the message from the journalist, make sure you see the below message. 

![Delete received messages](/docs/images/manual/source11.png)

Repeat to continue communicating with the journalist.

## Using SecureDrop As a Journalist

### Connecting to the Document Interface

Each journalist has their own authenticated Tor hidden service URL to login to the `Document Interface`. The journalist needs to use Tor through the Tails operating system to connect to the `Docuement Interface`. This is for extra security. This will take an extra few steps each time you want to login, but after practicing a few times, it will become automatic.

*Using Tails*

* Boot Tails on the Journalist Workstation using the Tails USB you created in the beginning (Note: this should be a different Tails USB stick that you use to boot the Secure Viewing Station).

* Under "Use persistence?" click "YES" and type in your password (do not hit enter).

* Under "More options?" clikc "YES", then click "Forward" 

* Set an administration password. This password will only be active during your current Tails session. Each time you will have to create this again, though it can be the same password everytime.

* Click login.

* Go to the upper right hand corner of your screen and enable your Internet connection.

* Click on `Computer` in the top left of your desktop, and go to the `Persistant` folder.

* Double click the 'copy_torrc.sh' file. This should have been created on installation by your admin.

* Click `Run In Terminal`

* Type in the administration password you created at the beginning of your session and click enter.

* When you go to your browser, in the bookmarks menu, you will now see links to both the source's SecureDrop page and the journalist's `Document Interface`.

* Click on the SecureDrop `Document Interface` link and you will be automatically logged-in. Now go down to the first screen shot below.

If any sources have uploaded documents or sent you message, they will be listed on the homepage by a code name. **Note: The code name the journalists see is different than the code name that sources see.**

![Document Interface](/docs/images/manual/document1.png)

### Moving Documents to the Secure Viewing Station

You will only be able to view the documents the source has sent you on the `Secure Viewing Station`. After clicking on an individual source you will see the below page with the messages that source has sent you. Click on a document or message name to save it.

![Load external content](/docs/images/manual/document4.png)

In order to protect you from malware, Tor Browser pops up a notice every time you try to download a file that can't be opened in Tor Browser itself. Go ahead and click `Launch application` anyway, and save the document to the designated USB stick you will use to transfer the documents from your Tails `Journalist Workstation` to the `Secure Viewing Station`. This will be known as your `Transfer USB`.

Eject your `Transfer USB` from your `Journalist Workstation`.

Next, boot up the `Secure Viewing Station` using Tails (remember, you must use a different Tails USB than you use your normal `Journalist Workstation`) and enter the password for the `Secure Viewing Station` the persistent volume. Once you have logged in, plug in the `Transfer USB`.

**Copy these documents to the Persistent folder before decrypting them. This an important step. Otherwise you might accidentally decrypt the documents on the USB stick, and they could be recoverable in the future.** You can do this by clicking on the `Computer` icon on your desk top, clicking on the `Transfer USB`, and then you can drag and drop the file into your Persistent folder.

![Copy files to Persistent](/docs/images/manual/viewing1.jpg)

Make sure to then return to your `Transfer USB` folder, right click on the file, and then click "Wipe" to securely wipe the file from your USB stick. 

### Decrypting and Working on the Secure Viewing Station

To decrypt documents, return to your Persistent folder and double-click on zipped file folder. After you extract the files, click on each file individually, and it will prompt you for the application PGP key passphrase to decrypt the document.

![Decrypting](/docs/images/manual/viewing2.jpg)

When you decrypt the file it will have the same filename, but without the .gpg at the end.

![Decrypted documents](/docs/images/manual/viewing3.jpg)

You can double-click on the decrypted document to open it in its default application.

![Opened document](/docs/images/manual/viewing4.jpg)

If the default application doesn't work, you can right-click on the document and choose `Open with Other Application...` to try opening the document with OpenOffice Writer, or Document Viewer. You can right-click on a file and choose `Rename...` to rename a document and give it a file extension.

### Interacting With Sources

Click on the code name to see the page specifically for that source. You will see all of the messages that they have written and documents that they have uploaded. Documents and messages are encrypted to the application's PGP public key. In order to read the messages or look at the documents you will need to transfer them to the `Secure Viewing Station`. But first, if you'd like to reply to the source, click the `Flag this source for reply` button.

![Read documents](/docs/images/manual/document2.png)

After clicking the `Flag this source for reply button`, you'll see this confirmation page. Click through to get back to the page that displays that souce's documents and replies.

![Flag source for reply](/docs/images/manual/document3.png)

*Note:* You will not be able to reply until after the source logs in again and sees that you would like to talk to him or her. So you may have to sit and wait. 

But after the source sees that you'd like to reply, a GPG key pair will automatically be generated and you can log back in and send a reply back.

![Sent reply](/docs/images/manual/document4.png)

Once your reply has been submitted, you will see this confirmation page.

![Sent reply confirmation](/docs/images/manual/document5.png)

Rinse and repeat.

### Working with Documents

As long as you're using the latest version of Tails, you should be able to open any document that gets submitted to you without the risk of malicious documents compromising the `Viewing Station`. However, if they do compromise it, Tails is designed so that the next time you reboot the malware will be gone.

Tails comes with lots of applications that will help you securely work with documents, including an office suite, graphics tools, desktop publishing tools, audio tools, and printing and scanning tools. For more information, visit [Work on sensitive documents](https://tails.boum.org/doc/sensitive_documents/index.en.html) on the Tails website.

Tails also comes with the [Metadata Anonymization Toolkit](https://mat.boum.org/) (MAT) that is used to help strip metadata from a variety of types of files, including png, jpg, OpenOffice/LibreOffice documents, Microsoft Office documents, pdf, tar, tar.bz2, tar.gz, zip, mp3, mp2, mp1, mpa, ogg, and flac. You can open MAT by clicking `Applications` in the top left corner, Accessories, Metadata Anonymisation Toolkit.

We recommend that you do as much work as you can inside of Tails before copying these documents back to your `Journalist Workstation`, including stripping metadata with MAT.

When you no longer need documents you can right-click on them and choose Wipe to delete them.

![Wiping documents](/docs/images/manual/viewing5.jpg)

### Encrypting and Moving Documents to Journalist Workstation

Before you move documents back to the USB stick to copy them to your workstation you should encrypt them to your personal PGP public key that you imported when setting up the `Secure Viewing Station` to begin with.

Right-click on the document you want to encrypt and choose `Encrypt...`

![Encrypting 1](/docs/images/manual/viewing6.jpg)

Then choose the public keys of the journalist you want to encrypt the documents to and click `OK`.

![Encrypting 2](/docs/images/manual/viewing7.jpg)

When you are done you will have another document with the same filename but ending in .pgp that is encrypted to the PGP keys you selected. You can copy the encrypted documents to the USB stick to transfer them to your workstation.

![Encrypted document](/docs/images/manual/viewing8.jpg)

### Decrypting and Preparing to Publish

Plug the USB stick into your workstation computer and copy the encrypted documents to it. Decrypt them with `gnupg`.

Write articles and blog posts, edit video and audio, and publish. Expose crimes and corruption, and change the world.
