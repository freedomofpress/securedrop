# Preparing Ubuntu servers for installation

The *Application Server* and the *Monitor Server* require [Ubuntu Server 14.04.1 LTS (Trusty Tahr)](http://www.ubuntu.com/download/server). SecureDrop is only supported for 64-bit platforms, so make sure you use the 64-bit images, which have a *-amd64* suffix. Download the ISO, burn it to CDs, and begin installing it on each of these computers. The following setup process is the same for each server.

After booting the the Ubuntu Server CD, select *Install Ubuntu Server*.

![Ubuntu Server](/docs/images/install/ubuntu_server.png)

Follow the steps to choose your language and keyboard, and let the setup continue. When it asks for your hostname, choose a name that makes sense. Each server should have its own hostname.  You can choose whatever username and password you would like. There's no need to encrypt home directories. Configure your time zone.

We recommend that you **do not** enable full disk encryption or encrypted home directories. 

Doing so will introduce the need for more passwords and add even more responsibility on the administrator of the system (see [this GitHub issue](https://github.com/freedomofpress/securedrop/issues/511#issuecomment-50823554) for more information). Instead, choose the installation option that says *Guided - use entire disk and set up LVM*. Then wait for base system to finish installing.

When you get to the configure tasksel screen, choose *Install security updates automatically*. When you get to the software selection screen, only choose *OpenSSH server*. Then wait for the packages to finish installing.

When everything is done, install grub and reboot.

After booting up for the first time, do updates.

    sudo apt-get update
    sudo apt-get upgrade
    sudo apt-get dist-upgrade

We strongly recommend that you patch your kernel with Grsecurity in order to harden these servers from attacks.
