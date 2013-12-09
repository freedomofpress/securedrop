SecureDrop Installation Guide
=============================

These instructions are intended for admins setting up SecureDrop for a journalist organization.

## Before you begin

Before installing SecureDrop, you should make sure you've got the environment properly set up.

* You must have two servers — called the `App Server` and the `Monitor Server`, with [Ubuntu Server installed](/docs/ubuntu_config.md).

* You must have a DVD configured as a Live DVD for the [Tails operating system](/docs/install.md#download-install-and-configure-tails).

* You must have a device capable of running the Google Authenticator app. Google Authenticator is an app for producing one-time passwords for two-factor authentication. You can find download instructions [here](https://support.google.com/accounts/answer/1066447?hl=en).

* You will need 2 USB sticks — one will be used for transferring files and the other for their Tails OS [persistent storage](https://tails.boum.org/doc/first_steps/persistence/).

* Each journalist must have a device capable of running the Google Authenticator app and 1 USB stick for transferring files from the `Secure Viewing Station` to their `Journalist Workstation`.

* Each journalist must have a personal GPG key. See [this section](/docs/install.md#set-up-journalist-pgp-keys) for instructions to set one up for journalists who don't have already have a key. 

* We suggest that you have an external hard drive for backing up encrypted submitted documents and some form of removable media for backing up the application's GPG keyring.

* Finally, you should have selected two secure passphrases: one for the Tails persistent volume on the `Secure Viewing Station` and one for the application's GPG keypair. If your organization doesn't yet have a good password policy, [you really should have one](http://howto.wired.com/wiki/Choose_a_Strong_Password).

## Secure Viewing Station

The `Secure Viewing Station` will be air-gapped (never connected to the Internet) and will run the [Tails operating system](https://tails.boum.org/). Because Tails is a live GNU/Linux distribution that runs off of removable media, this computer does not need a hard drive.

You will need to create a GPG keypair for the SecureDrop application. When sources upload documents, they get encrypted to this public key. Journalists use this secret key to decrypt these documents on the `Secure Viewing Station`. Additionally, you will add the personal GPG public keys for each journalist to this computer. After a journalist is done viewing documents and ready to move them to their `Journalist Workstation` to finish work before publication, you will encrypt the documents with the journalist's personal public key.

### Remove Hard Drive

Turn off the laptop you want to use for the `Secure Viewing Station`. Physically open up the laptop to remove the hard drive. The directions are different depending on the make and model of the laptop you're using, but in general it requires using a small phillips head screwdriver. Once you have removed the hard drive, re-assemble the laptop.

### Download, Install and Configure Tails

If you already have a Tails Live USB, you can skip to the fourth step, where you configure the persistent volume.

* Visit [the Tails website](https://tails.boum.org/download/index.en.html) for instruction on downloading, verifying, and burning a Tails DVD.
* After burning Tails to a DVD, boot to it on the `Secure Viewing Station` laptop. If this laptop does not have a DVD drive, use an external DVD drive.
* Once you've booted into the Live DVD, you should create a Live USB stick with the USB drive set aside for Tails. Reboot the `Secure Viewing Station` laptop into that Live USB drive.
* Configure a Persistent Volume. Use the Persistent Volume passphrase that you generated at the beginning of the installation process. Make sure that the Persistent Volume includes "Personal Data" and "GnuPG". Tails offers [instructions for configuring the Persistent Volume](https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html).

Reboot the `Secure Viewing Station` laptop and boot into the Tails Live USB again to continue with the setup.

### Generate GPG Key and Import Journalist Public Keys

In order to avoid transferring plaintext files between the `Secure Viewing Station` and `Journalist Workstations`, each journalist should have their [own personal GPG key](/docs/install.md#set-up-journalist-pgp-keys). Start by copying all of the journalists' public keys to a USB stick. Plug this into the `Secure Viewing Station` running Tails and open the file manager. Double-click on each public key to import it. If the public key isn't importing, try renaming it to end in ".asc".

![Importing Journalist GPG Keys](/images/install/viewing1.jpg)

To generate the application GPG key, click in the clipboard icon in the top right and choose `Manage Keys`. A program called `Passwords and Encryption Keys` will open. You can click on the `Other Keys` tab to manage the keys that you just imported.

![Tails GPG Clipboard](/images/install/viewing2.jpg)

Click `File`, `New`. Choose `PGP Key`, and click Continue.

![New...](/images/install/viewing3.jpg)

Put these values in:

* `Full Name`: SecureDrop
* `Email Address`: (blank)
* `Comment`: SecureDrop Application GPG Key

Click the arrow to expand `Advanced key options`. Change the `Key Strength` from 2048 to 4096. Then click Create.

![New GPG Key](/images/install/viewing4.jpg)

Type in the GPG passphrase that you came up with earlier twice and click OK. Then wait while your key is being generated. 

![Set Passphrase](/images/install/viewing5.jpg)
![Key Generation](/images/install/viewing6.jpg)

When it's done, you should see your key in the `My Personal Keys` tab.

![My Keys](/images/install/viewing7.jpg)

Right-click on the key you just generated and click `Export`. Save it to your USB stick as `SecureDrop.asc`. This is the public key only.

![My Keys](/images/install/viewing8.jpg)

You'll also need to verify the 40 character hex fingerprint for this new key during the `App Server` installation. Double-click on the new key you just generated and change to the `Details` tab. Write down the 40 digits under `Fingerprint`. (Your GPG key fingerprint will be different than what's in this photo.)

![Fingerprint](/images/install/viewing9.jpg)

## Server Installation

Both the `App Server` and `Monitor Server` should already have Ubuntu Server installed. To follow these instructions you should know how to navigate the command line.

Download the latest version of SecureDrop to your workstation by downloading the latest tar.gz file from https://pressfreedomfoundation.org/securedrop and extracting it. 

The setup script needs the application GPG public key you created earlier, `SecureDrop.asc`. Plug in the USB stick that you copied `SecureDrop.asc` to and copy it to securedrop/install_files/

Then scp the `securedrop` folder to the home directory on the `Monitor Server` and `App Server`, doing something like this:

    scp -r securedrop user@MONITOR_IP:~/
    scp -r securedrop user@APP_IP:~/

Now SSH to the `Monitor Server`. When you're in, enter your environment details in the CONFIG_OPTIONS file and run the installation script:

    cd ~/securedrop
    nano CONFIG_OPTIONS

Fill out all of the global and `Monitor Server` options. Here are descriptions of the items you should fill out:

* `ROLE`: This is either "monitor" or "app". Since both servers share the same codebase, the installation script need to know which server it's running on. For now, enter "monitor".
* `APP_IP`: The IP address of the `App Server` that you have set up.
* `MONITOR_IP`: The IP address of the `Monitor Server` that you have set up (the one you are SSHed into).
* `SSH_USERS`: A list of Linux users that will SSH into this server. Note that the installation script will disable SSHing as the root account, so you must have a non-root account set up on the server that you plan on using to administer this server.
* `SMTP_SERVER`: The `Monitor Server` can send email updates. This is the hostname of your external SMTP server. At the moment SMTP authentication isn't supported.
* `EMAIL_DISTRO`: The email address to send email alerts to.
* `EMAIL_FROM`: The "From" address of email alerts.

Fill out the relevant options, save and exit. Then run the production script.

    sudo ./production_installation.sh

Wait for the script to run. When it's done, it should say this:

    Start the installation on app server.
    After installation on the app server is complete
    enter 'Y' to continue: (Y|N): Y

Leave that window open and go SSH into the `App Server` and edit CONFIG_OPTIONS:

    cd ~/securedrop
    nano CONFIG_OPTIONS

This time edit the global and `App Server` settings. Here are descriptions of the items you should fill out:

* `ROLE`: This should be "app".
* `APP_IP` and `MONITOR_IP` should be the same as they were on the `Monitor Server`.
* `SSH_USERS`: A list of Linux users that will SSH into this server.
* `JOURNALIST_USERS`: Make up a username for each journalist that will be using this SecureDrop instance.
* `KEY`: The filename that contains the application GPG public key you created on the `Secure Viewing Station`. It's probably `SecureDrop.asc`.
* `SOURCE_SCRIPTS`: You can leave this blank.
* `DOCUMENT_SCRIPTS`: You can leave this blank.

Save and exit. When you're done, run the production script:

    sudo ./production_installation.sh

A Google Authenticator code will be generated for the identified SSH_USERS in the CONFIG_OPTIONS file.

Follow the instructions for adding your secret key to your Google Authenticator app

At the end of a successful `App Server` installation the script will output the `Source Interface`'s onion URL, the `Document Interface`'s onion URL and auth codes, the `App Server`'s SSH onion address and auth code.

    The Source Interface's onion URL is:
    bh33efgmt5ai32te.onion
    The Document Interface's onion URL and auth value are:
    b6ferdazsj2v6agu.onion AHgaX9YrO/zanQmSJnILvB # client: journalist1
    kx7bdewk4x4wait2.onion qpTMeWZSTdld7gWrB72RtR # client: journalist2
    The App Server's SSH onion address and auth values are:
    sz3yuv5hdipt2icy.onion PKZ8sKjp5Z08AGq5BB7BKx # admin1
    oz4ezuhym2zfugjn.onion xCQf9IrFAXuoo7KfrMURzB # admin2
    The App Server's installation is complete.
    Please finsish the installation on the Monitor Server

This lists the Tor hidden service URLs for the `Source Interface`, the two journalists on the `Document Interface`, and the onion addresses for SSH access. It also lists the auth value for each journalist and admin. Save those lines because the journalists and admins will need them to access the `Document Interface` and `App Server`.

In this case:
* The `Source Interface`'s Tor hidden service URL is http://bh33efgmt5ai32te.onion/.
* The `Document Interface`'s Tor hidden service URL for the first journalist is: http://b6ferdazsj2v6agu.onion/
* The `Document Interface`'s Tor hidden service Auth value for the first journalist is: AHgaX9YrO/zanQmSJnILvB
* The `Document Interface`'s Tor hidden service URL for the second journalist is: http://kx7bdewk4x4wait2.onion/
* The `Document Interface`'s Tor hidden service Auth value for the first journalist is: qpTMeWZSTdld7gWrB72RtR
* The `App Server`'s Tor hidden service SSH address for the first admin is: sz3yuv5hdipt2icy.onion
* The `App Server`'s Tor hidden service SSH Auth value for the first admin is: PKZ8sKjp5Z08AGq5BB7BKx

Once the `App Server`'s installation is successfully completed. Go back to the SSH session for the `Monitor Server` and enter `Y` to continue.

A Google Authenticator code will be generated for the identified SSH_USERS in the CONFIG_OPTIONS file.

Follow the instructions for adding your secret key to your mobile Google Authenticator app.

At the end of a successful `Monitor Server` installation the script will output the `Monitor Server` SSH onion address.

Once you have completed these steps, the SecureDrop web application should be set up.

## Journalist's Workstation Setup

The journalist workstation computer is the laptop that the journalist uses on a daily basis. It can be running Windows, Mac OS X, or GNU/Linux. At minimum, this computer must have GPG and the Tor Browser Bundle installed. 

### Set up journalist GPG keys

Each journalist must have a personal GPG key that they use for encrypting files transferred from the `Secure Viewing Station` to their `Journalist Workstation`. The private key, used for decryption, stays on their `Journalist Workstation`. The public key, used for encryption, gets copied to the `Secure Viewing Station`.

If a journalist does not yet have a GPG key, they can follow these instructions to set one up with GnuPG (GPG).

* [GNU/Linux](http://www.gnupg.org/gph/en/manual.html#AEN26)
* [Windows](http://gpg4win.org/)
* [Mac OS X](http://support.gpgtools.org/kb/how-to/first-steps-where-do-i-start-where-do-i-begin)

### Set up the Tor Browser Bundle

In order to connect to the `App Server`, the journalist needs to install the Tor Browser Bundle and modify it to authenticate their hidden service. Each journalist gets their own hidden service URL.

You will have to do the following steps on each laptop that will be able to connect to the `Document Interface` running on the `App Server`. If you want to give a new journalist access to the `Document Interface` you will need to do these steps again for that new journalist.

* On the `Journalist Workstation`, [download and install the Tor Browser Bundle](https://www.torproject.org/download/download-easy.html.en). Extract Tor Browser Bundle to somewhere you will find it, such as your desktop.

* Navigate to the Tor Browser Directory
* Open the `torrc` file which should be located in `tor-browser_en-US/Data/Tor/torrc`
* Add a line that begins with `HidServAuth` followed by the journalist's Document Interface URL and Auth value that was outputed at the end of the App Server installation

In this case the `torrc` file for the first journalist should look something like:

    # If non-zero, try to write to disk less frequently than we would otherwise.
    AvoidDiskWrites 1
    # Store working data, state, keys, and caches here.
    DataDirectory ./Data/Tor
    GeoIPFile ./Data/Tor/geoip
    # Where to send logging messages.  Format is minSeverity[-maxSeverity]
    # (stderr|stdout|syslog|file FILENAME).
    Log notice stdout
    # Bind to this address to listen to connections from SOCKS-speaking
    # applications.
    SocksListenAddress 127.0.0.1
    SocksPort 9150
    ControlPort 9151
    HidServAuth b6ferdazsj2v6agu.onion AHgaX9YrO/zanQmSJnILvB # client: journalist1

And the `torrc` file for the second journalist should look like something this:

    # If non-zero, try to write to disk less frequently than we would otherwise.
    AvoidDiskWrites 1
    # Store working data, state, keys, and caches here.
    DataDirectory ./Data/Tor
    GeoIPFile ./Data/Tor/geoip
    # Where to send logging messages.  Format is minSeverity[-maxSeverity]
    # (stderr|stdout|syslog|file FILENAME).
    Log notice stdout
    # Bind to this address to listen to connections from SOCKS-speaking
    # applications.
    SocksListenAddress 127.0.0.1
    SocksPort 9150
    ControlPort 9151
    HidServAuth kx7bdewk4x4wait2.onion qpTMeWZSTdld7gWrB72RtR # client: journalist2

* Open the Tor Browser Bundle and navigate to the journalist's unique Document Interface URL without the Auth value

![Journalist_workstation1](/images/install/journalist_workstation1.png)

## Test It

Once it's installed, test it out. See [How to Use SecureDrop](/docs/user_manual.md).
