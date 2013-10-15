# How to Use SecureDrop

## SecureDrop Depends on the Tor Browser

Sources who submit documents and journalists who download these documents must connect to the SecureDrop website using the Tor network. The easiest and most secure way to use Tor is to download the Tor Browser Bundle from https://www.torproject.org/.

Once you have the Tor Browser installed you can access Tor hidden service URLs that have domain names that end in .onion. Media organizations must link to the .onion URL for their instance of SecureDrop from their website. Each journalist that uses SecureDrop has their own personal .onion URL that they use to connect.

## As a Source

Open the Tor Browser and visit the hidden service for the SecureDrop website you're visiting.

![Source website](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source1.png)

If this is the first time you're using SecureDrop with this organization, click the "Submit Documents" button.

![Generating code name](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source2.png)

SecureDrop will create a code name for you to use. In the preview screenshot the codename that was generated was `naiad edit carrie bahama brew hardy cannot gosh`. You must either memorize this or write it down in a safe place. After you submit documents, you must know this code name in order to login and check for responses.

You can choose the length of your code name. Longer code names are more secure but harder to memorize, and shorter code names are less secure but easier to memorize, so use your discretion. Once you have generated a code name, click Continue.

![Generating code name](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source3.png)

You can then choose to upload a document and/or enter a message to send to the journalists. When you are done, click Submit.

![Document upload success](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source4.png)

If you have already submitted a document and you would like to check for a response, from the source homepage click the "Check for a Response" button instead.

![Check for response](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source5.png)

Enter the code name that you already know and click Continue.

![Check for response](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source6.png)

If a journalist has responded there will be a message waiting for you to read and delete. You can also upload another document or send another message to the journalists.

## As a Journalist

### Connecting to the Document Server

Each journalist has their own authenticated Tor hidden service URL. The journalist needs to use the Tor Browser that [has been configured for their use only](https://github.com/freedomofpress/securedrop/blob/master/docs/install.md#server-installation).

Start by opening Tor Browser and loading the .onion URL to access the `Document Server`. If any sources have uploaded documents or sent you message, they will be listed on the homepage by a code name. **Note: The code name the journalists see is different than the code name that sources see.**

![Document server](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/document1.png)

### Interacting With Sources

Click on the code name to see the page specifically for that source. You will see all of the messages that they have written and documents that they have uploads.

![Read documents](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/document2.png)

Documents and messages are encrypted to the application's PGP public key. In order to read the messages or look at the documents you will need to transfer them to the `Viewing Station`. But first, if you'd like to reply to the source you can fill out the text area and click Submit.

![Sent reply](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/document3.png)

### Moving Documents to Viewing Station

The first step is downloading the documents. Click on a document or message name to save it. In order to protect you from malware, Tor Browser pops up a notice that looks like this every time you try to download a file that can't be opened in Tor Browser itself:

![Load external content](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/document4.png)

Go ahead and click `Launch application` anyway, and save the document to a USB stick.

Boot up the `Viewing Station` to Tails and mount the persistent volume. Once you have logged in, plug in the USB stick that you copied encrypted documents to it.

**Copy these documents to the Persistent folder before decrypting them. This an important step. Otherwise you might accidentally decrypt the documents on the USB stick, and they could be recoverable in the future.**

![Copy files to Persistent](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/viewing1.jpg)

### Decrypting and Working on the Secure Viewing Station

To decrypt documents, double-click on them. It will prompt you for the application PGP key passphrase to decrypt the document.

![Decrypting](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/viewing2.jpg)

When you decrypt the file it will have the same filename, but without the .gpg at the end.

![Decrypted documents](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/viewing3.jpg)

You can double-click on the decrypted document to open it in it's default application.

![Opened document](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/viewing4.jpg)

If you the default application doesn't work, you can right-click on the document and choose "Open with Other Application..." to try opening the document with OpenOffice Writer, or Document Viewer. You can right-click on a file and choose "Rename..." to rename a document and give it a file extension.

### Working with Documents

As long as you're using the latest version of Tails, you should be able to open any document that gets submitted to you without the risk of malicious documents compromising the `Viewing Station`. However, if they do compromise it, Tails is designed so that the next time you reboot the malware will be gone.

Tails comes with lots of applications that will help you securely work with documents, including an office suite, graphics tools, desktop publishing tools, audio tools, and printing and scanning tools. For more information, visit [Work on sensitive documents](https://tails.boum.org/doc/sensitive_documents/index.en.html) on the Tails website.

Tails also comes with the [Metadata Anonymization Toolkit](https://mat.boum.org/) (MAT) that is used to help strip metadata from a variety of types of files, including png, jpg, OpenOffice/LibreOffice documents, Microsoft Office documents, pdf, tar, tar.bz2, tar.gz, zip, mp3, mp2, mp1, mpa, ogg, and flac. You can open MAT by click Applications in the top left corner, Accessories, Metadata Anonymisation Toolkit.

We recommend that you do as much work as you can inside of Tails before copying these documents back to your `Journalist Workstation`, including stripping metadata with MAT.

When you no longer need documents you can right-click on them and choose Wipe to delete them.

![Wiping documents](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/viewing5.jpg)

### Encrypting and Moving Documents to Journalist Workstation

Before you move documents back to the USB stick to copy them to your workstation you should encrypt them to your personal PGP public key that you imported when setting up the `Viewing Station` to begin with.

Right-click on the document you want to encrypt and choose "Encrypt..."

![Encrypting 1](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/viewing6.jpg)

Then choose the public keys of the journalist you want to encrypt the documents to and click OK.

![Encrypting 2](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/viewing7.jpg)

When you are done you will have another document with the same filename but ending in .pgp that is encrypted to the PGP keys you selected. You can copy the encrypted documents to the USB stick to transfer them to your workstation.

![Encrypted document](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/viewing8.jpg)

### Decrypting and Preparing to Publish

Plug the USB stick into your workstation computer and copy the encrypted documents to it. Decrypt them with `gnupg`.

Write articles and blog posts, edit video and audio, and publish. Expose crimes and corruption, and change the world.
