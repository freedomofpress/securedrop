SecureDrop Installation Guide
=============================

Before installing SecureDrop, you should make sure you've got the environment properly set up. 

* You must have three servers — called the `Source Server`, the `Document Server`, and the `Monitor` — with [Ubuntu configured and grsec patches installed](https://github.com/freedomofpress/securedrop/blob/master/docs/ubuntuconfig.md).

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

### Copy SecureDrop Code to the Viewing Station

On your regular workstation computer, download the latest version of SecureDrop. You can either get it from our git repository with `git clone https://github.com/freedomofpress/securedrop.git`, or you can download the latest tar.gz file from https://pressfreedomfoundation.org/securedrop.

Copy the securedrop folder to one of the USB sticks. Plug it into the `Viewing Station` and copy the securedrop folder into the `/home/amnesia/Persistent` directory.

### Generate PGP Key and Import Journalist Public Keys

In order to avoid transfering plaintext files between the `Viewing Station` and `Journalist Workstations`, each journalist should have their own personal PGP key. Start by copying all of the journalists' public keys to a USB stick. Plug this into the `Viewing Station` running Tails and open the file manager. Double-click on each public key to import it. If the public key isn't importing, try renaming it to end in ".asc".

To generate the application PGP key, open the Terminal program and type:

    /home/amnesia/Persistent/securedrop/viewing_setup.sh

It will ask you: `Create new gpg keypair for the application? (y/n)`. Press enter to select `y`. It will pop up box that says "Enter passphrase". Enter the PGP passphrase that you generated earlier, click OK, and enter it a second time. Then wait for the key to generate.

When it's done it will place your new PGP public key in /home/amnesia/Persistent/securedrop.asc. Copy that file to the USB stick.

## Journalist Workstation Setup

The journalist workstation computer is the laptop that the journalist uses on a daily basis. It can be running Windows, Mac OS X, or GNU/Linux. In order to connect to the `Document Server` they need to install the Tor Browser Bundle, and then they need to install an SSL client certificate into the Tor Browser.

You will have to do the following steps on each laptop that will be able to connect to the `Document Server`. If you want to give a new journalist access to the `Document Server` you will need to do these steps again for that new journalist.

* On the `Journalist Workstation`, [download and install the Tor Browser Bundle](https://www.torproject.org/download/download-easy.html.en). Extract Tor Browser Bundle to somewhere you will find it, such as your desktop.

* On the `Viewing Station`, mount the Persistent volume. Copy the user certificate that you created for the current journalist, a .pk12 file named after the journalist, to a USB stick. 

* Start the Tor Browser. When it has loaded, click Edit > Preferences. Go to the Advanced section at the top, and then switch to the Encryption tab. Click the View Certificates button, and switch to the Your Certificates tab. Click Import and navigate to the .p12 file to import it. When you are done with this step, the client certificate should be installed.

* If you ever re-install Tor Browser Bundle, you'll need to repeat the previous step.

![Installing client certificate in Tor Browser](https://raw.github.com/freedomofpress/securedrop/install/images/torbrowser.png)

## Server Installation

All 3 servers should already have Ubuntu Server installed and the grsec kernel patches in place.

### Download the SecureDrop configuration script

Puppet is a tool to manage server configurations. SecureDrop uses a puppet module on the `Monitor` server to set up the other two servers: the `Document Server`, and the `Source Server`. From the `Monitor` server, download that puppet module to the home directory:

        cd ~
        git clone https://github.com/freedomofpress/securedrop.git 
        
### Gather the required files from the Viewing Station
  
The `Monitor` server needs a file containing the journalist's public GPG key and the certificates on the `Viewing Station` generated by the Local Certificate Authority. That file is prepared by the `viewingSetup.sh` script run earlier on the `Viewing Station` and should be copied from there to a USB stick. It is located on the `Viewing Station` in this locations:

		~/Persistent/certs.tgz

Copy that file from the `Viewing Station` to a USB stick, and then to the home directory on the `Monitor`.

### Run the `serverSetup.sh` script

With the `certs.tgz` file in place, you're ready to run the setup script:

        cd ~/securedrop  
        ./serverSetup.sh
        
Follow the onscreen prompts, providing the required information about your configuration. These prompts will asks for server IP addresses, hostnames, internal VPN IP address, the application's GPG fingerprint, and the location of `certs.tgz`.

## Final State
