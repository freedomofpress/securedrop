# Preparing Ubuntu servers for installation

The `App Server` and `Monitor Server` require [Ubuntu Server 12.04.5 LTS (Precise Pangolin)](http://releases.ubuntu.com/12.04/). SecureDrop is only supported for 64-bit platforms, so make sure you use the 64-bit images, which have a `-amd64` suffix. Download the ISO, burn it to CDs, and begin installing it on each of these computers. The following setup process is the same for each server.

After booting the the Ubuntu Server CD, select "Install Ubuntu Server".

![Ubuntu Server](/docs/images/install/ubuntu_server.png)

Follow the steps to choose your language and keyboard, and let the setup continue. When it asks for your hostname choose a name that makes sense. Each server should have its own hostname.  You can choose whatever username and password you would like. There's no need to encrypt home directories. Configure your time zone.

We recommend that you enable [full disk encryption](https://www.eff.org/deeplinks/2012/11/privacy-ubuntu-1210-full-disk-encryption) with LUKS. During the disk partitioning step, select "Guided - use entire disk and set up encrypted LVM". Write the changes to disk. Follow the recommendations as to choosing a strong password. **Important**: this password will need to be entered at every boot, and during reboots after installing security updates. As the administrator, you will be responsible for keeping this passphrase safe. Write it down somewhere and memorize it if you can. If inadvertently lost it could result in total loss of the SecureDrop system.

**Warning**: Enabling encrypted disks along with unattended-upgrades means that SecureDrop will become unreachable after an automatic reboot. An administrator should be on hand to enter the password in order to mount the disks. We recommend that the servers be integrated with a monitoring solution that so that you receive an alert when the system becomes unavailable.

![Encrypted LVM](/docs/images/install/ubuntu_encrypt.png)

If you wish to opt out of full disk encryption at your own risk, then choose "Guided - use entire disk and set up LVM" instead. Then wait for base system to finish installing. 

**Warning** Enabling encrypted home directories will break the default 2 factor authentication. If you wish to enable encrypted home directories, you will need to change the default locations of the google-authenticator file to outisde of the users encrypted home directory and update the google authenticator pam module to reflect the new location.

When you get to the configure tasksel screen, choose "Install security updates automatically". When you get to the software selection screen, only choose "OpenSSH server". Then wait for the packages to finish installing.

When everything is done, install grub and reboot.

After booting up for the first time, do updates.

    sudo apt-get update
    sudo apt-get upgrade

We also recommend that you patch your kernel with grsecurity in order to harden these servers from attacks. Instuctions for doing this are outside the scope of this installation guide. Visit the official [Grsecurity documentation](http://en.wikibooks.org/wiki/Grsecurity) for more information about [obtaining](http://en.wikibooks.org/wiki/Grsecurity/Obtaining_grsecurity) and [configuring and installing](http://en.wikibooks.org/wiki/Grsecurity/Configuring_and_Installing_grsecurity) the kernel patch.
