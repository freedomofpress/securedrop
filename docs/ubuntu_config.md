# Ubuntu Install Guide

## Creating the Ubuntu installation media

The *Application Server* and the *Monitor Server* require [Ubuntu Server 14.04.1 LTS (Trusty Tahr)](http://www.ubuntu.com/download/server). SecureDrop is only supported for 64-bit platforms, so make sure you use the 64-bit images, which have a *-amd64* suffix.

Download the ISO, burn it to CDs, and begin installing it on each of these computers. Optionally, you can create a bootable USB stick from which you can install the operating system (see instructions for doing this on [OS X](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-mac-osx), [Ubuntu](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-ubuntu) and [Windows](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-windows)).

## Installing Ubuntu

The following setup process is the same for each server.

After booting the the Ubuntu Server CD, select **Install Ubuntu Server**.

![Ubuntu Server](/docs/images/install/ubuntu_server.png)

Follow the steps to choose your language and keyboard, and let the setup continue.

### Configuring the network manually

The Ubuntu installer will try to autoconfigure networking for the server you are setting up; however, SecureDrop 0.3 requires manual network configuration. You can hit **Cancel** at any point during network autoconfiguration to be given the choice to *Configure the network manually*. If network autoconfiguration completes before you can do this, the next window will ask for your hostname. Click **Cancel** and choose **Configure the network** from the menu of installation steps.

For production install with pfsense network firewall in place, the app and monitor servers are on separate networks. The network segment information on the network firewall needs to agree with the network information entered on the servers.

If you know what you are doing, you may choose your own network settings at this point, but remember to propogate your choices through the rest of the installation process. You can choose whatever IPs and hostnames you want, just make sure they are unique on the firewall's network and you remember them for running the Ansible playbook later.

*We recommend using the following configuration:*

Use (192.168.1.0/24) for the app network segment and (192.168.2.0/24) for the monitor network segment.

* App server:
    * Server IP address: 192.168.1.51
    * Netmask default is fine (255.255.255.0)
    * Gateway default is fine (192.168.1.1)
    * For DNS, use Google's name servers: 8.8.8.8
    * Hostname: app
    * Domain name should be left blank
* Monitor server:
    * Server IP address: 192.168.2.52
    * Netmask default is fine (255.255.255.0)
    * Gateway default is fine (192.168.1.1)
    * For DNS, use Google's name servers: 8.8.8.8
    * Hostname: mon
    * Domain name should be left blank

### Continuing the installation

You can choose whatever username and password you would like. There's no need to encrypt home directories. Configure your time zone.

### Partioning the disks

Before setting up the server's disk partitions and filesystems, you will need to decide if you would like to enable [*Full Disk Encryption (FDE)*](https://www.eff.org/deeplinks/2012/11/privacy-ubuntu-1210-full-disk-encryption). If the servers are ever powered down, FDE will ensure all of the information on them stay private in case they are seized or stolen. 

While FDE can be useful in some cases, we currently do not recommend that you enable it. Doing so will introduce the need for more passwords and add even more responsibility on the administrator of the system (see [this GitHub issue](https://github.com/freedomofpress/securedrop/issues/511#issuecomment-50823554) for more information). Instead, choose the installation option that says *Guided - use entire disk and set up LVM*.

If you decide to go ahead and enable FDE, please note that doing so means SecureDrop will become unreachable after an automatic reboot. An administrator will need to be on hand to enter the password in order to decrypt the disks and complete the startup process. We recommend that the servers be integrated with a monitoring solution that so that you receive an alert when the system becomes unavailable.

To enable FDE, select *Guided - use entire disk and set up encrypted LVM* during the disk partitioning step and write the changes to disk. Follow the recommendations as to choosing a strong password. As the administrator, you will be responsible for keeping this passphrase safe. Write it down somewhere and memorize it if you can. If inadvertently lost it could result in total loss of the SecureDrop system.

### Finishing the installation

Wait for the base system to finish installing. When you get to the *Configure tasksel* screen, choose **Don't install updates automatically**. When you get to the software selection screen, only choose **OpenSSH server** and continue. Then wait for the packages to finish installing.

When the packages are finished installing, Ubuntu will automatically install the bootloader (grub). If it asks to install the bootloader to the Master Boot Record, choose **Yes**. When everything is done, reboot.

