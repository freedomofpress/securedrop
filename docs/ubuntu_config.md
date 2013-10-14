# Preparing Ubuntu servers for installation

`Source Server`, `Document Server`, and `Monitor Server` all require [Ubuntu Server 12.04.3](http://www.ubuntu.com/download/server). Download the ISO, burn it to CDs, and begin installing it on each of these computers. The following setup process is the same for each server.

After booting the the Ubuntu Server CD, select "Install Ubuntu Server".

![Ubuntu Server](https://raw.github.com/freedomofpress/securedrop/master/docs/images/install/ubuntu_server.png)

Follow the steps to choose your language and keyboard, and let the setup continue. When it asks for your hostname choose a name that makes sense. Each server should have its own hostname.  You can choose whatever username and password you would like. There's no need to encrypt home directories. Configure your time zone. When you get to the partition step, choose "Guided - use entire disk and set up LVM". Then wait for base system to finish installing. 

When you get to the configure taskel screen, choose "Install security updates automatically". When you get to the software selection screen, just choose "OpenSSH server". Then wait for the packages to finish installing.

When everything is done, install grub and reboot.

After booting up for the first time, do updates.

    sudo apt-get update
    sudo apt-get upgrade

On each server you also need to add a line to `/etc/resolv.conf`.

    sudo sh -c "echo 'search securedrop' > /etc/resolv.conf"

We also recommend that you patch your kernel with grsecurity in order to harden these servers from attacks. Instuctions for doing this are outside the scope of this installation guide. Visit the official [Grsecurity documentation](http://en.wikibooks.org/wiki/Grsecurity) for more information about [obtaining](http://en.wikibooks.org/wiki/Grsecurity/Obtaining_grsecurity) and [configuring and installing](http://en.wikibooks.org/wiki/Grsecurity/Configuring_and_Installing_grsecurity) the kernel patch.
