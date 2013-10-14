SecureDrop Installation Guide
=============================

Before installing SecureDrop, you should make sure you've got the environment properly set up. 

* You must have three servers — called the `Source Server`, the `Document Server`, and the `Monitor Server` with [Ubuntu Server installed](https://github.com/freedomofpress/securedrop/blob/master/docs/ubuntu_config.md).

* You must have a DVD configured as a Live DVD for the Tails operating system. You will only have to use this DVD once: After the first run from a Live DVD you can create a Live USB to boot from instead. If you already have a Tails Live USB, you may skip this requirement.

* You must have three USB sticks — two that will be used for for transferring files, and one that will be used to run the Tails operating system on the `Viewing Station`.

* Finally, you should have selected two secure passphrases for different components of the `Viewing Station`: one for the persistent volume and one for the PGP keypair. If your organization doesn't yet have a good password policy, [you really should have one](http://howto.wired.com/wiki/Choose_a_Strong_Password).

## Viewing Station

The `Viewing Station` will be air-gapped (never connected to the Internet) and will run the [Tails operating system](https://tails.boum.org/). Because Tails is a live GNU/Linux distribution that runs off of removable media, this computer does not need a hard drive.

You will need to create an PGP keypair for the SecureDrop application. When sources upload documents, they get encrypted to this public key. Journalists use this secret key to decrypt these documents on the `Viewing Station`. Additionally, you will add the personal PGP public keys for each journalist to this computer. After a journalist is done viewing documents and ready to move them to their `Journalist Workstation` to finish work before publication, you will encrypt the documents with the journalist's public key.

### Remove Hard Drive

Turn off the laptop you want to use for the `Viewing Station`. Physically open up the laptop to remove the hard drive. The directions are different depending on the make and model of the laptop you're using, but in general it requires using a small phillips head screwdriver. Once you have removed the hard drive, re-assemble the laptop.

### Download, Install and Configure Tails

If you already have a Tails Live USB, you can skip to the fourth step, where you configure the persistent volume.

* Visit [the Tails website](https://tails.boum.org/download/index.en.html) for instruction on downloading, verifying, and burning a Tails DVD.
* After burning Tails to a DVD, boot to it on the `Viewing Station` laptop. If this laptop does not have a DVD drive, use an external DVD drive.
* Once you've booted into the Live DVD, you should create a Live USB stick with the USB drive set aside for Tails. Reboot the `Viewing Station` laptop into that Live USB drive.
* Configure a Persistent Volume. Use the Persistent Volume passphrase that you generated at the beginning of the installation process. Make sure that the Persistent Volume includes "Personal Data" and "GnuPG". Tails offers [instructions for configuring the Persistent Volume](https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html).

Reboot the `Viewing Station` laptop and boot into the Tails Live USB again to continue with the setup.

### Generate PGP Key and Import Journalist Public Keys

In order to avoid transfering plaintext files between the `Viewing Station` and `Journalist Workstations`, each journalist should have their own personal PGP key. Start by copying all of the journalists' public keys to a USB stick. Plug this into the `Viewing Station` running Tails and open the file manager. Double-click on each public key to import it. If the public key isn't importing, try renaming it to end in ".asc".

![Importing Journalist PGP Keys](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing1.jpg)

To generate the application PGP key, click in the clipboard icon in the top right and choose `Manage Keys`. A program called `Passwords and Encryption Keys` will open. You can click on the `Other Keys` tab to manage the keys that you just imported.

![Tails PGP Clipboard](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing2.jpg)

Click `File`, `New`. Choose `PGP Key`, and click Continue.

![New...](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing3.jpg)

Put these values in:

* `Full Name`: SecureDrop
* `Email Address`: (blank)
* `Comment`: SecureDrop Application PGP Key

Click the arrow to expland `Advanced key options`. Change the `Key Strength` from 2048 to 4096. Then click Create.

![New PGP Key](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing4.jpg)

Type in the PGP passphrase that you came up with earlier twice and click OK. Then wait while your key is being generated. 

![Set Passphrase](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing5.jpg)
![Key Generation](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing6.jpg)

When it's done, you should see your key in the `My Personal Keys` tab.

![My Keys](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing7.jpg)

Right-click on the key you just generated and click `Export`. Save it to your USB stick as `SecureDrop.asc`.

![My Keys](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing8.jpg)

You'll also need to write down the 40 character hex fingerprint for this new key for the next step. Double-click on the new key you just generated and change to the `Details` tab. Write down the 40 digits under `Fingerprint`. (Your PGP key fingerprint will be different than what's in this photo.)

![Fingerprint](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/viewing9.jpg)

## Server Installation

All three servers should already have Ubuntu Server installed.

SSH to the `Monitor Server` and download the latest version of SecureDrop. You can either get it from our git repository with `git clone https://github.com/freedomofpress/securedrop.git`, or you can use `wget` to download the latest tar.gz file from https://pressfreedomfoundation.org/securedrop.

The setup script needs the application PGP public key you created earlier, `securedrop.asc`. Plug in the USB stick that you copied it to into your workstation and copy it to the home directory of the `Monitor Server` using `scp`.

The run the setup script:

    cd ~/securedrop
    sudo ./server_setup.sh

Do steps 1 through 6, and then choose 0 to exit when you are done.

* Step 1: Install puppetmaster. This installs puppetmaster and other dependencies, helps you download the [OSSEC](http://www.ossec.net/) binary, and lets you verify the location of `securedrop.asc`.
* Step 2: Enter environment information. Enter the IP addresses, hostnames, and other environment information.
* Step 3: Install puppet agent on source and document servers. This connects to the `Source Server` and the `Document Server` and installs required packages.
* Step 4: Sign agent certs.
* Step 5: Run puppet manifests.

At the end of this step it should display something like this:

    The source server's Tor URL is: 
    username@192.168.0.108's password: 
    [sudo] password for username: 
    bh33efgmt5ai32te.onion
    Connection to 192.168.0.108 closed.
    The document server's Tor URL for the journalists are:
    username@192.168.0.109's password: 
    [sudo] password for username: 
    b6ferdazsj2v6agu.onion AHgaX9YrO/zanQmSJnILvB # client: journalist1
    kx7bdewk4x4wait2.onion qpTMeWZSTdld7gWrB72RtR # client: journalist2
    Connection to 192.168.0.109 closed.

This lists the Tor hidden service URLs for the `Source Server` as well for the two journalists on the `Document Server`. It also lists the auth value for each journalist. Save those lines because you'll need them when setting up the `Journalist Workstations`.

In this case, the `Source Server`'s Tor hidden service URL is http://bh33efgmt5ai32te.onion/.
The Tor hidden service URL for the first journalist is: http://b6ferdazsj2v6agu.onion/
The Tor hidden service URL for the second journalist is: http://kx7bdewk4x4wait2.onion/

* Step 6: Clean up puppet and install files.

Then choose 0 to quit. When you are done, you then need to run some commands to help start the `sshfs` connection between the `Source Server` and the `Document Server`. SSH into the `Source Server` and run:

    sudo -u www-data ssh journalist exit

This tried to SSH into the `Document Server`. If the fingerprint is correct accept it. Then start `sshfs`.

    sudo /etc/network/if-up.d/mountsshfs

Once you have completed these steps, the SecureDrop web application should be setup.

## Journalist Workstation Setup

The journalist workstation computer is the laptop that the journalist uses on a daily basis. It can be running Windows, Mac OS X, or GNU/Linux. In order to connect to the `Document Server` they need to install the Tor Browser Bundle, and then they need to install an SSL client certificate into the Tor Browser.

You will have to do the following steps on each laptop that will be able to connect to the `Document Server`. If you want to give a new journalist access to the `Document Server` you will need to do these steps again for that new journalist.

* On the `Journalist Workstation`, [download and install the Tor Browser Bundle](https://www.torproject.org/download/download-easy.html.en). Extract Tor Browser Bundle to somewhere you will find it, such as your desktop.

* On the `Viewing Station`, mount the Persistent volume. Copy the user certificate that you created for the current journalist, a .pk12 file named after the journalist, to a USB stick. 

* Start the Tor Browser. When it has loaded, click Edit > Preferences. Go to the Advanced section at the top, and then switch to the Encryption tab. Click the View Certificates button, and switch to the Your Certificates tab. Click Import and navigate to the .p12 file to import it. When you are done with this step, the client certificate should be installed.

* If you ever re-install Tor Browser Bundle, you'll need to repeat the previous step.

![Installing client certificate in Tor Browser](https://raw.github.com/freedomofpress/securedrop/install/images/torbrowser.png)

## Test It

Once it's installed, test it out. See [How to Use SecureDrop](https://github.com/freedomofpress/securedrop/blob/master/docs/user_manual.md).
