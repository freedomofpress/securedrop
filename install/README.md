===========
Deaddrop Environment Install Guide
===========

Deaddrop is a tool for communicating securely with journalists. Please also view the Threat_Model.doc, diagram.jpg, and design.jpg in docs/ for more information. The environment install guide is below the license. 

Copyright (C) 2011-2013 James Dolan

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

##Hardware Requirements
The following equipment will be required:  
1. You will need 3 computers with the hard drives still installed  
2. You will need 1 computer shell (a computer with the hard drive removed)  
3. You will need 3 USB sticks with Tails the Amesic Incognito Live System installed  
4. You will need 2 USB sticks for transfering files  
5. You will need 1 USB stick for storing the applications gpg private key  
6. A USB stick will be needed for each journalist for storing their personnel gpg private keys  

##Clone the Git Repositories and Copy To USB
You must have git installed. Open a terminal and clone the two repositories:

    git clone https://github.com/deaddrop/deaddrop.git
    git clone https://github.com/dolanjs/deaddropEnvironment.git

Then copy these two folders to a USB stick.

##Local Certificate Authority Install  
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

###Generate the openssl certificates  
Insert the USB stick that has the cloned git repos on it into the Tails computer. Copy `deaddropEnvironment/localca.sh` to `/home/amnesia/Persistent/`.

The configuration files, certificates, and revocation lists are saved in the Persistant folder activated with the Personal Data feature of the Tails Persistent Volume Feature.  


        cd /home/amnesia/Persistent/  
        ./localca.sh  
 

At the end of running the localca.sh script you should have two folders in your home directory:  
`/home/amnedia/Persistent/journalist_server/`  
`/home/amnesia/Persistent/journalist_user/`  

##Secure Viewing Station Install
The Secure Viewing Station (SVS) never should be connected to a network. Transfering files to and from the SVS require the sneakernet.  
1. Steps to download, verify and install Tails to a usb stick can be found here:  
     `https://tails.boum.org/download/index.en.html`  
2. Step to configure the Personal Data persistant storage feature to store the config file and root CA certs can be found here: `https://tails.boum.org/doc/first_steps/persistence/index.en.html`     
3. Ensure that Persistent Volume Feature 'Personal Data' is activated  
4. Copy the gengpg.sh script to the secure viewing stations `/home/amnesia/Persistent/` directory

###Run gengpg.sh script

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
 

##Monitor server install
###Download the deaddrop puppet module
Download the deaddrop puppet module to 

        cd ~
        git clone https://github.com/dolanjs/deaddropEnvironment.git  
        
###Gather the required files from the external harddrives  
From the Secure Viewing Station copy the:  
App's pub gpg key ===> `~/environment/modules/deaddrop/files/journalist.asc`  

From the Local Certificate Authority copy the:  
~/Persistent/journalist_server ===> `~/environment/modules/deaddrop/files/journalist_server`  

###Run the `puppet-setup.sh` script
This script will install and run puppet

        cd ~/deaddropEnvironment  
        ./puppet-setup.sh  

##Install the grsec patched ubuntu kernel  

###Install the grsec patched kernel  

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

##Clean up the system and puppet firewall rules  
Once the environment is verified, run the clean up script to purge puppet and other install files


        ./deaddrop_cleanup.sh

##Final State
The final state should look like a,b,c,d....
