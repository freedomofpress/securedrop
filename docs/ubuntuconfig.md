Preparing Ubuntu servers for installation
=========================================

`Source Server`, `Document Server`, and `Monitor Server` all require [Ubuntu Server 12.04.3](http://www.ubuntu.com/download/server). Download the ISO, burn it to CDs, and begin installing it on each of these computers. The following setup process is the same for each server.

After booting the the Ubuntu Server CD, select "Install Ubuntu Server".

(screenshot)

Follow the steps to choose your language and keyboard, and let the setup continue. When it asks for your hostname choose a name that makes sense. Each server should have its own hostname.

(screenshot)

You can choose whatever username and password you would like.

(screenshot)

There's no need to encrypt home directories. Configure your time zone. When you get to the partition step, choose "Guided - use entire disk and set up LVM". Then wait for base system to finish installing. 

When you get to the configure taskel screen, choose "Install security updates automatically". When you get to the software selection screen, just choose "OpenSSH server". Then wait for the packages to finish installing.

When everything is done, install grub and reboot.

After booting up for the first time, do updates.

    sudo apt-get update
    sudo apt-get upgrade

Install the grsec-Patched Ubuntu Kernel
=======================================

The grsec patch increases the security of the Source, Document, and Monitor servers. For now, you have to patch the kernel yourself and make sure that it will boot alright.

        cd ..  
        dpkg -i *.deb  

### Before You Get Started

(Todo: Explain that the patched kernel has only been tested on specific hardware, and list that hardware.)
        
### Obtaining the Patch

(Todo: Explain how to obtain the patch, somewhere in the install script?)

### Configuring and Installing the Patch

(Todo: More detail about what you need to do before you can reboot.)

### Rebooting

Review boot menu and boot into the new kernel. Verify that `/boot/grub/menu.lst` has the correct values. Make adjustments as necessary.

        sudo reboot 

After the reboot check that you booted into the correct kernel.   

        uname -r  

It should end in '-grsec'  

After finishing installing the patch, ensure the grsec sysctl configs are applied and locked.

        sysctl -p  
        sysctl -w kernel.grsecurity.grsec_lock = 1  
        sysctl -p 
        
Visit the official [Grsecurity documentation](http://en.wikibooks.org/wiki/Grsecurity) for more information about [obtaining](http://en.wikibooks.org/wiki/Grsecurity/Obtaining_grsecurity) and [configuring and installing](http://en.wikibooks.org/wiki/Grsecurity/Configuring_and_Installing_grsecurity) the kernel patch.
