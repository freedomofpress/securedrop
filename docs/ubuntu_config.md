# Preparing Ubuntu servers for installation

The *Application Server* and the *Monitor Server* require [Ubuntu Server 14.04.1 LTS (Trusty Tahr)](http://www.ubuntu.com/download/server). SecureDrop is only supported for 64-bit platforms, so make sure you use the 64-bit images, which have a *-amd64* suffix. Download the ISO, burn it to CDs, and begin installing it on each of these computers. Optionally, you can create a bootable USB stick from which you can install the operating system (see instructions for doing this on [OS X](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-mac-osx), [Ubuntu](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-ubuntu) and [Windows](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-windows)).

 The following setup process is the same for each server.

After booting the the Ubuntu Server CD, select *Install Ubuntu Server*.

![Ubuntu Server](/docs/images/install/ubuntu_server.png)

Follow the steps to choose your language and keyboard, and let the setup continue. When it asks for your hostname, choose a name that makes sense. Each server should have its own hostname.  You can choose whatever username and password you would like. There's no need to encrypt home directories. Configure your time zone.

Before continuing with the installation process, you will need to decide if you would like to enable [*Full Disk Encryption (FDE)*](https://www.eff.org/deeplinks/2012/11/privacy-ubuntu-1210-full-disk-encryption). If the servers are ever powered down, FDE will ensure all of the information on them stay private in case they are seized or stolen. 

While FDE can be useful in some cases, we currently do not recommend that you enable it. Doing so will introduce the need for more passwords and add even more responsibility on the administrator of the system (see [this GitHub issue](https://github.com/freedomofpress/securedrop/issues/511#issuecomment-50823554) for more information). Instead, choose the installation option that says *Guided - use entire disk and set up LVM*.

If you decide to go ahead and enable FDE, please note that doing so means SecureDrop will become unreachable after an automatic reboot. An administrator will need to be on hand to enter the password in order to mount the disks and complete the startup process. We recommend that the servers be integrated with a monitoring solution that so that you receive an alert when the system becomes unavailable.

To enable FDE, select *Guided - use entire disk and set up encrypted LVM* during the disk partitioning step and write the changes to disk. Follow the recommendations as to choosing a strong password. As the administrator, you will be responsible for keeping this passphrase safe. Write it down somewhere and memorize it if you can. If inadvertently lost it could result in total loss of the SecureDrop system.

Wait for the base system to finish installing. When you get to the configure tasksel screen, choose *Install security updates automatically*. When you get to the software selection screen, only choose *OpenSSH server*. Then wait for the packages to finish installing.

When everything is done, install grub and reboot.

After booting up for the first time, do updates.

```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get dist-upgrade
```
