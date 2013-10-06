SecureDrop Installation Guide
=============================

Before installing SecureDrop, you should make sure you've got the environment properly set up. 

* You must have 3 servers -- called the `Source Server`, the `Document Server`, and the `Monitor` -- with [Ubuntu configured](https://github.com/freedomofpress/securedrop/blob/master/docs/ubuntuconfig.md) and [grsec patches installed](https://github.com/freedomofpress/securedrop/blob/master/docs/grsec.md).

* You must have 3 USB sticks -- 2 that will be used for for transferring files, and 1 that will be used to run the Tails operating system on the `Viewing` Station.

* Finally, you should have generated 3 secure passphrases for different components of the `Viewing` Station.

## Copy SecureDrop Code to USB Stick
You will need one more USB stick to facilitate installation. Download the latest version of SecureDrop and extract it to this USB stick. For example, cd to the USB stick and run:

    git clone https://github.com/freedomofpress/securedrop.git

## Source Server Installation

## Document Server Installation

## Viewing Station Installation

The `Viewing` computer will be air-gapped (never connected to the Internet) and will run the (Tails)[https://tails.boum.org/] operating system. Because Tails is a live GNU/Linux distribution that runs off of removable media, this computer does not need a hard drive.

This computer will have two sets of crypto keys on it as well:

* SSL keys. You will create a local Certificate Authority on this computer, as well as a user certificate for each journalist that will be accessing the `Document Server`. 

* OpenPGP keys. You will need to create a PGP keypair for the SecureDrop application. When sources upload documents, they get encrypted to this public key. Journalists use this secret key to decrypt these documents on the `Viewing` station. Additionally, you will add the personal PGP public keys for each journalist to this computer. After a journalist is done viewing documents and ready to move them to their `Journalist Workstation` to finish work before publication, you will encrypt the documents with the journalist's public key.

### Remove Hard Drive

Turn off the laptop you want to use for the `Viewing` station. Physically open up the laptop to remove the hard drive. The directions are different depending on the make and model of the laptop you're using, but in general it requires using a small phillips head screwdriver. Once you have removed the hard drive, re-assemble the laptop.

### Download, Install and Configure Tails

* Visit https://tails.boum.org/download/index.en.html for instruction on downloading, verifying, and burning a Tails DVD.
* After burning Tails to a DVD, boot to it on the `Viewing` station laptop. If this laptop does not have a DVD drive, use an external DVD drive.
* Configure a Persistent Volume. Use the Persistent Volume passphrase that you generated at the beginning of the installation process. Make sure that the Persistent Volume includes "Personal Data" and "GnuPG". Instructions for configuring the Persistent Volume are here: https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html
* Reboot the `Viewing` laptop and boot into Tails again.

### Copy SecureDrop Code to Viewing Station

Plug in the USB stick with the SecureDrop code, and copy the securedrop directory to the `/home/amnesia/Persistent/` directory. You'll need to run scripts inside this code to set up the `Viewing` station.

### Local Certificate Authority

You'll need to generate a local SSL certificate authority and then generate a user certificate for each journalist that needs to access the `Document Server`. User certificates should be revoked when journalists no longer require access.

To install everything, you need to run the localca.sh script. In Tails, open the Terminal program and type:

    cd ~/Persistent/securedrop/install 
    ./localca.sh  
 
At the end of running the localca.sh script you should have two folders in your home directory:  

    /home/amnesia/Persistent/journalist_server/  
    /home/amnesia/Persistent/journalist_user/

tktktktk: explain how to make user certificates

### Generate the OpenPGP key

    ./gengpg.sh  
       
The script will generate the application gpg key pair and save the application's public key `journalist.asc` in `/home/amnesia/Persistent/` directory  
Generate the gpg v2 keys  

	gpg2 --homedir  /home/amnesia/Persistent/ --gen-key  
	
>(1) RSA and RSA (default)  
>key size: 4096  
>real name: Journalist  

Only the two selected journalist's should know the app's GPG keypair's passphrase. Follow your organization's password policy. http://howto.wired.com/wiki/Choose_a_Strong_Password  

Export the Journalist's gpg public key  

    gpg2 --export --output journalist.asc --armor Journalist  

Determine and record the application's gpg key's fingerprint  

    gpg --homedir /home/amnesia/Persistent/ --list-keys --with-fingerprint  
    
tktktktk explain this, too

## Journalist Workstation Setup

The journalist workstation computer is the laptop that the journalist uses on a daily basis. It can be running Windows, Mac OS X, or GNU/Linux. In order to connect to the `Document Server` they need to install the Tor Browser Bundle, and then they need to install an SSL client certificate into the Tor Browser.

You will have to do the following steps on each laptop that will be able to connect to the `Document Server`. If you want to give a new journalist access to the `Document Server` you will need to do these steps again for that new journalist.

* Turn on the `Viewing` station and mount the persistent volume. Copy the user certificate that you created for the current journalist to a USB stick (a .p12 file). 

* On the `Journalist Workstation`, download and install the Tor Browser Bundle. Visit https://www.torproject.org/download/download-easy.html.en to find the download link. Extract Tor Browser Bundle to somewhere you will find it, such as your desktop.

* Start the Tor Browser. When it has loaded, click Edit > Preferences. Go to the Advanced section at the top, and then switch to the Encryption tab. Click the View Certificates button, and switch to the Your Certificates tab. Click Import and navigate to the .p12 file to import it. When you are done with this step, the client certificate should be installed.

* If you ever re-install Tor Browser Bundle, you'll need to repeat the previous step.

![Installing client certificate in Tor Browser](https://raw.github.com/freedomofpress/deaddrop/install/images/torbrowser.png)

## Monitor Server Installation

### Download the deaddrop puppet module
Puppet is a tool to manage server configurations. SecureDrop uses a puppet module to set up the `Monitor` server. Download the that puppet module to the home directory of the server:

        cd ~
        git clone https://github.com/freedomofpress/securedrop.git  
        
### Gather the required files from the external harddrives  
The `Monitor` server needs a copy of the journalist's public GPG key and the certificates on the `Viewing` Station generated by the Local Certificate Authority. Those files are prepared by the `localca.sh` script run earlier on the `Viewing` Station and should be copied from there to a USB stick. Those are located on the `Viewing` Station in these locations:

		tktktktktktk
		tktktktktktk
		
Copy those from the `Viewing` Station to a USB stick, and then to the `Monitor`. Unzip those files:

		tktktktktktk
		tktktktktktk

<!--

From the Secure Viewing Station copy the public GPG key to `~/environment/modules/deaddrop/files/journalist.asc`  

From the Local Certificate Authority copy the:  
~/Persistent/journalist_server ===> `~/environment/modules/deaddrop/files/journalist_server`

-->

### Run the `puppet-setup.sh` script
This script will install and run puppet

        cd ~/deaddropEnvironment  
        ./puppet-setup.sh  


## Clean up the system and puppet firewall rules  
Once the environment is verified, run the clean up script to purge puppet and other install files


        ./deaddrop_cleanup.sh

## Final State
The final state should look like a,b,c,d....