SecureDrop Environment Install Guide
====================================

SecureDrop is a tool for sources communicating securely with journalists. The SecureDrop application environment uses four dedicated computers:

* `Source Server`: Ubuntu server running a Tor hidden service that sources use to send messages and documents to journalists.
* `Document Server`: Ubuntu server running a Tor hidden service that journalists use to download encrypted documents and respond to sources.
* `Monitor`: Ubuntu server that monitors the `Source` and `Document` servers and sends email alerts.
* `Viewing`: An airgapped computer without a hard drive running Tails from a USB stick that journalists use to decrypt and view submitted documents.

In addition to these computers, journalists use normal workstation computers:

* `Journalist Workstations`: The every-day laptops that journalists use. They will use this computer to connect to the `Document Server` to respond to sources and download encrypted documents to copy to the `Viewing` station. They will also copy encrypted documents back from the `Viewing` station to this computer to do final work before publication.

These computers should all physically be in your organization's office. You will need a total of three USB sticks:

* USB stick with Tails for the `Viewing` computer
* USB stick for transfering files between the `Admin Workstation` and the `Viewing` computer
* USB stick for transfering files between the `Viewing` computer and `Journalist Workstations`

## Copy Installation Scripts to USB Stick
You will need one more USB stick to facilitate installation. Download the latest version of SecureDrop and extract it to this USB stick. For example, cd to the USB stick and run:

    git clone https://github.com/freedomofpress/deaddrop.git

## Source Server Installation

## Document Server Installation

## Viewing Station Installation

The `Viewing` computer will be air-gapped (never connected to the Internet) and will run the (Tails)[https://tails.boum.org/] operating system. Because Tails is a live GNU/Linux distribution that runs off of removable media, this computer does not need a hard drive.

This computer will have two sets of crypto keys on it as well:

* SSL keys.  

* OpenPGP keys.

* Local Certificate Authority. Journalists access the `Document` server using both a username and password and also a special SSL certificate that's installed in their browser. 

## Journalist Workstation Setup

The journalist workstation computer is the laptop that the journalist uses on a daily basis. It can be running Windows, Mac OS X, or GNU/Linux. In order to connect to the `Document Server` they need to install the Tor Browser Bundle, and then they need to install an SSL client certificate into the Tor Browser.

You will have to do the following steps on each laptop that will be able to connect to the `Document Server`. If you want to give a new journalist access to the `Document Server` you will need to do these steps again for that new journalist.

* Turn on the `Viewing` station and mount the persistent volume. Copy the user certificate that you created for the current journalist to a USB stick (a .p12 file). 

* On the `Journalist Workstation`, download and install the Tor Browser Bundle. Visit https://www.torproject.org/download/download-easy.html.en to find the download link. Extract Tor Browser Bundle to somewhere you will find it, such as your desktop.

* Start the Tor Browser. When it has loaded, click Edit > Preferences. Go to the Advanced section at the top, and then switch to the Encryption tab. Click the View Certificates button, and switch to the Your Certificates tab. Click Import and navigate to the .p12 file to import it. When you are done with this step, the client certificate should be installed.

* If you ever re-install Tor Browser Bundle, you'll need to repeat the previous step.

![Installing client certificate in Tor Browser](https://raw.github.com/freedomofpress/deaddrop/install/images/torbrowser.png)

## Local Certificate Authority Install  
The journalist's interface uses ssl certificates for transport encryption and authentication that will be generated on the Local CA USB stick.  
1. Steps to download, verify and install Tails to a usb stick can be found here `https://tails.boum.org/download/index.en.html`  
2. Step to configure the Personal Data persistant storage feature to store the config file and root CA certs can be found here:
        `https://tails.boum.org/doc/first_steps/persistence/index.en.html`   
3. Ensure that Persistent Volume Feature 'Personal Data' is activated  
4. The Local CA never needs to be connected to a network to generate the needed certificates, keys and revocation lists  
5. The USB stick that the Local CA is installed on should be stored securely when not in use  
6. The USB stick that the Local CA is installed on should be clearly labeled to avoid confusion with other USB sticks  
7. User certificates should only be generated for approved journalists that require access to the journalist interface  
8. Unique user certificates should be generated for each approved journalist  
9. User certificates should be securely transported to the approved journalist  
10. Server and user certificates should be set to expire to your organization's policy  
11. A User certificate should be revoked if the journalist no longer requires access  

### Generate the openssl certificates  
Insert the USB stick that has the cloned git repos on it into the Tails computer. Copy `deaddropEnvironment/localca.sh` to `/home/amnesia/Persistent/`.

The configuration files, certificates, and revocation lists are saved in the Persistant folder activated with the Personal Data feature of the Tails Persistent Volume Feature.  


        cd /home/amnesia/Persistent/  
        ./localca.sh  
 

At the end of running the localca.sh script you should have two folders in your home directory:  
`/home/amnedia/Persistent/journalist_server/`  
`/home/amnesia/Persistent/journalist_user/`  

## Secure Viewing Station Install
The Secure Viewing Station (SVS) never should be connected to a network. Transfering files to and from the SVS require the sneakernet.  
1. Steps to download, verify and install Tails to a usb stick can be found here:  
     `https://tails.boum.org/download/index.en.html`  
2. Step to configure the Personal Data persistant storage feature to store the config file and root CA certs can be found here: `https://tails.boum.org/doc/first_steps/persistence/index.en.html`     
3. Ensure that Persistent Volume Feature 'Personal Data' is activated  
4. Copy the gengpg.sh script to the secure viewing stations `/home/amnesia/Persistent/` directory

### Run gengpg.sh script

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
 

## Monitor Server Installation

### Download the deaddrop puppet module
Puppet is a tool to manage server configurations. SecureDrop uses a puppet module to set up the `Monitor` server. Download the that puppet module to the home directory of the server:

        cd ~
        git clone https://github.com/freedomofpress/deaddropEnvironment.git  
        
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



## Install the grsec patched ubuntu kernel  

### Install the grsec patched kernel  

        cd ..  
        dpkg -i *.deb  


Review boot menu and boot into new kernel  
Verify that `/boot/grub/menu.lst` has the correct values. Make adjustments as necessary.  

        sudo reboot 

After the reboot check that you booted into the correct kernel.   

        uname -r  

It should end in '-grsec'  

After finishing installing the ensure the grsec sysctl configs are applied and locked

        sysctl -p  
        sysctl -w kernel.grsecurity.grsec_lock = 1  
        sysctl -p 

## Clean up the system and puppet firewall rules  
Once the environment is verified, run the clean up script to purge puppet and other install files


        ./deaddrop_cleanup.sh

## Final State
The final state should look like a,b,c,d....
