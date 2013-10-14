# How to Use SecureDrop

## SecureDrop Depends on the Tor Browser

Sources who submit documents and journalists who download these documents must connect to the SecureDrop website using the Tor network. The easiest and most secure way to use Tor is to download the Tor Browser Bundle from https://www.torproject.org/.

Once you have the Tor Browser installed you can access Tor hidden service URLs that have domain names that end in .onion. Media organizations must link to the .onion URL for their instance of SecureDrop from their website. Each journalist that uses SecureDrop has their own personal .onion URL that they use to connect.

## As a Source

Open the Tor Browser and visit the hidden service for the SecureDrop website you're visiting.

![Source website](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source1.png)

If this is the first time you're using SecureDrop with this organization, click the "Submit Documents" button.

![Generating code name](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source2.png)

SecureDrop will create a code name for you to use. In the preview screenshot the codename that was generated was `ridge rene alton lw chit fl sob euler`. You must either memorize this or write it down in a safe place. After you submit documents, you must know this code name in order to login and check for responses.

You can choose the length of your code name. Longer code names are more secure but harder to memorize, and shorter code names are less secure but easier to memorize, so use your discretion. Once you have generated a code name, click Continue.

![Generating code name](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source3.png)

You can then choose to upload a document and/or enter a message to send to the journalists. When you are done, click Submit.

todo: what happens after you upload a document?

If you have already submitted a document and you would like to check for a response, click the "Check for a Response" button instead. Enter the code name that you already know and click Continue.

![Check for response](https://raw.github.com/freedomofpress/securedrop/master/docs/images/manual/source4.png)

You will be able to upload more documents, send more messages, and check for responses from the journalists.

## As a Journalist

### Connecting to the Document Server

### Interacting With Sources

### Moving Documents to Viewing Station

All documents that you download from the `Document Server` are encrypted to the application's PGP public key. The secret key is in the persistent volume on the `Viewing Station`, which means you won't have access to the actual documents until you transfer them there.

Plug in a USB stick and copy the encrypted documents to it.

Boot up the `Viewing Station` to Tails and mount the persistent volume. Once you have logged in, plug in the USB stick that you copied encrypted documents to it.

**Copy these documents to the Persistent folder before decrypting them. This an important step. Otherwise you might accidentally decrypt the documents on the USB stick, and they could be recoverable in the future.**

### Decrypting and Working on the Secure Viewing Station

### Encrypting and Moving Documents to Journalist Workstation

### Decrypting and Preparing to Publish

