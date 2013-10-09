# Preparing Ubuntu servers for installation

`Source Server`, `Document Server`, and `Monitor Server` all require [Ubuntu Server 12.04.3](http://www.ubuntu.com/download/server). Download the ISO, burn it to CDs, and begin installing it on each of these computers. The following setup process is the same for each server.

After booting the the Ubuntu Server CD, select "Install Ubuntu Server".

![Ubuntu Server](https://raw.github.com/freedomofpress/securedrop/master/docs/images/ubuntu_server.png)

Follow the steps to choose your language and keyboard, and let the setup continue. When it asks for your hostname choose a name that makes sense. Each server should have its own hostname.  You can choose whatever username and password you would like. There's no need to encrypt home directories. Configure your time zone. When you get to the partition step, choose "Guided - use entire disk and set up LVM". Then wait for base system to finish installing. 

When you get to the configure taskel screen, choose "Install security updates automatically". When you get to the software selection screen, just choose "OpenSSH server". Then wait for the packages to finish installing.

When everything is done, install grub and reboot.

After booting up for the first time, do updates.

    sudo apt-get update
    sudo apt-get upgrade
    exit

At this point it's easier to follow the rest of the instructions by sshing into these three servers from over the network.

# Install the grsec-Patched Ubuntu Kernel

The grsec patch increases the security of the `Source Server`, `Document Server`, and `Monitor Server`. See the [grsecurity wikibook](https://en.wikibooks.org/wiki/Grsecurity) for more details.

The following instructions will help you compile a new kernel that includes the grsec patch. If your servers all use the same hardware, you can do these steps on just one server (such as the `Monitor Server`) and then scp the .deb to install on the other servers (`Source Server` and `Document Server`). If your hardware is different, then apply these steps to each server. We will assume that the hardware is the same.

## Gather files and packages needed for the ubuntu overlay

On the `Monitor Server`, run these commands.

    cd ~  
    mkdir grsec  
    cd grsec  
    sudo apt-get install libncurses5-dev build-essential  kernel-package git-core -y  
    git clone git://kernel.ubuntu.com/ubuntu/ubuntu-precise.git  
    cp -a /usr/share/kernel-package ubuntu-package  
    cp ubuntu-precise/debian/control-scripts/p* ubuntu-package/pkg/image/  
    cp -a /usr/share/kernel-package ubuntu-package  
    cp ubuntu-precise/debian/control-scripts/p* ubuntu-package/pkg/image/  
    cp ubuntu-precise/debian/control-scripts/headers-postinst ubuntu-package/pkg/headers/  

Install `gcc-4.6.-plugin-dev`.

    sudo apt-get install gcc-4.6-plugin-dev -y    

Download the kernel and grsecurity patch (see [Obtaining grsecurity](http://en.wikibooks.org/wiki/Grsecurity/Obtaining_grsecurity#Downloading_grsecurity) for more information).

    wget https://www.kernel.org/pub/linux/kernel/v3.x/linux-3.2.36.tar.bz2  
    wget https://www.kernel.org/pub/linux/kernel/v3.x/linux-3.2.36.tar.sign  
    wget https://grsecurity.net/spender-gpg-key.asc  
    wget https://grsecurity.net/stable/grsecurity-2.9.1-3.2.51-201309281102.patch
    wget https://grsecurity.net/stable/grsecurity-2.9.1-3.2.51-201309281102.patch.sig

Verify the packages:

    gpg --import spender-gpg-key.asc
    gpg --verify grsecurity-2.9.1-3.2.36-201301032034.patch.sig
    gpg --recv-keys 6092693E
    bunzip2 linux-3.2.36.tar.bz2
    gpg --verify linux-3.2.36.tar.sign

##  Apply the patch to the kernel and make the grsec kernel

    tar -xf linux-3.2.36.tar
    cd linux-3.2.36
    patch -p1 <../grsecurity-2.9.1-3.2.36-201301032034.patch

Apply the old hardware config to ensure that the correct options are retained.

    yes "" | make oldconfig
    make menuconfig

In the GUI:

* navigate to 'Security options'
* navigate to 'Grsecurity'
* enable the ‘Grsecurity’ option
* Set ‘Configuration Method’ to ‘Automatic’
* Set ‘Usage Type’ to ‘Server’
* Set ‘Virtualization Type’ to ‘None’
* Set ‘Required Priorities’ to ‘Security’
* navigate to ‘Customize Configuration’
* navigate to ‘Sysctl Support’ and enable ‘Sysctl support’
* exit and save changes

    make-kpkg clean  
    make-kpkg --initrd --overlay-dir=../ubuntu-package kernel_image kernel_headers  

Grab a cup of coffee. When the package is complete scp the .deb files to the `Source Server` and `Document Server`.

Follow the rest of this guide on all three servers.

## Resolve PAX grub issues

    apt-get install paxctl -y  
    paxctl -Cpm /usr/sbin/grub-probe  
    paxctl -Cpm /usr/sbin/grub-mkdevicemap  
    paxctl -Cpm /usr/sbin/grub-setup  
    paxctl -Cpm /usr/bin/grub-script-check  
    paxctl -Cpm /usr/bin/grub-mount  
    update-grub  

## Install the grsec patched kernel

    sudo dpkg -i *.deb  

Review boot menu and boot into new kernel. Verify that `/boot/grub/menu.lst` has the correct values. Make adjustments as necessary. 

    sudo reboot 

After the reboot check that you booted into the correct kernel. It should end in '-grsec'.

    uname -r  

After finishing installing the ensure the grsec sysctl configs are applied and locked.

    sysctl -p  
    sysctl -w kernel.grsecurity.grsec_lock = 1  

Visit the official [Grsecurity documentation](http://en.wikibooks.org/wiki/Grsecurity) for more information about [obtaining](http://en.wikibooks.org/wiki/Grsecurity/Obtaining_grsecurity) and [configuring and installing](http://en.wikibooks.org/wiki/Grsecurity/Configuring_and_Installing_grsecurity) the kernel patch.
