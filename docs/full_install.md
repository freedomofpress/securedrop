**TODO**: split or merge into existing docs as appropriate

This is the full set of instructions for a complete run-through of installing SecureDrop 0.3.


# Requirements

* 3 Intel NUCs
  1. Application Server
  2. Monitor Server
  3. SVS
* **TODO**: clarify NUC dependencies (power cords, RAM, hard disks, display cables) and setup process
* Admin Workstation (any spare computer that can be connected to the firewall and can run Tails)
* 5 blank USB sticks:
  * Ubuntu 14.04.1 Live USB (to install Ubuntu on the servers)
    * [link to .iso](http://releases.ubuntu.com/14.04/ubuntu-14.04.1-server-amd64.iso)
    * live usb instructions: [windows](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-windows) | [mac](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-mac-osx) | [linux](http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-ubuntu)
  * Tails Live USB (to set up other Tails Live USB's with persistence)
    * [instructions](https://tails.boum.org/download/index.en.html)
  * SVS USB
  * Admin USB
  * Transfer USB (will become the transfer device)


## Notes on the NUCs

There is a variety of available NUCs, and each different model supports different hardware specs and peripheral connectors. For this test, I am using:


### D34010WYK

[Amazon link w/ picture](http://www.amazon.com/Intel-Computing-BOXD34010WYK1-Black-White/dp/B00H3YT886/ref=sr_1_3?ie=UTF8&qid=1413905126&sr=8-3&keywords=NUC+D34010WYK)

I have two of these: one for the Secure Viewing Station (SVS), which is air-gapped and never connected to the Internet, and one for the Admin Workstation, which is Internet-connected and is used to run the Ansible playbooks. You could also use an admin's existing workstation, or a recycled machine, for this purpose.

**TODO** what are the concerns about security from existing hardware in newsrooms? The Admin Workstation runs Tails, so the primary concerns would be hardware implants.

This machine has USB 3.0, which is nice for booting live USB quickly and for transferring large files. It has two available display connectors: Mini-HDMI and DisplayPort.


### DC3217IYE

[Amazon link w/ picture](http://www.amazon.com/Intel-Computing-Gigabit-i3-3217U-DC3217IYE/dp/B0093LINVK)

I am using these for the Application and Monitor servers (app and mon). They only have USB 2.0, which is not so bad because the Linux installation using live USB is a one-time process and you rarely transfer files directly from the servers. They also only have one available display connector: HDMI.


# Tails setup

*Tested with: Tails 1.2 released October 16, 2014*

**TODO**: dd'ing the live USB on Mac using the instructions on the Tails website is incredibly slow. There should be something we can do with the flags to dd to speed it up.


## SVS

**TODO**: This should be relatively unchanged from our current docs in `install.md`.


## Admin Workstation

In this section we will set up the Tails Live USB with persistence for the Admin Workstation. Start by booting the Admin Workstation from the Tails Live USB.

*Note: on the NUCs, you reboot by holding the power button down for a few seconds until it triggers the reboot. Once it reboots, hold F10 to get the boot menu. The transition from when you have a chance to hit F10 to when the NUC boots the default OS is very quick!*

At the "Welcome to Tails" dialog, choose "No" for "More options?" and click *Login*. Once the desktop environment has loaded, insert the spare USB that will become a Tails live USB with persistence for the Admin Workstation.

In the top left corner, choose "Applications > Tails > Tails Installer". Choose "Clone & Install" and select the USB stick you inserted as the Target Device. In my testing, it was automatically selected because it was the only other USB device inserted at the time. Click "Install Tails" and click "Yes" to continue. When the installer is done, click "OK" to close the program.

You will be able to set up persistence on this new Tails USB because it was created with the Tails Installer. Shut down the running Tails instance (top right > power button > *Shut down immediately*). Remove the original Tails USB, leaving the new Tails USB, and boot the Admin Workstation from the new Tails live USB.

"Welcome to Tails", "More Options?" choose *No* and click *Forward*

Open the Persistence Wizard - click OK, configure the volume, select all options for storage, restart.

# Server setup

Start by plugging the NUCs into a shared firewall. Their static network configuration will need to be stable for Ansible install to work.

Install Ubuntu 14.04 (Trusty) on both NUCs. The install process is the same as we have outlined in `ubuntu_config.md`, except:

* When the network autoconfiguration starts, hit Enter to cancel it. You may have to hit Enter several times to cancel various stages of the autoconfiguration. Don't worry if it completes, you can always go back and configure manually by hitting "Cancel" on a subsequent dialog boxes.
* Once you've cancelled network autoconfiguration, choose "Configure network manually".
  * You can choose whatever IP you want, just make sure they are unique on the firewall's network and you remember them for later running the Ansible playbook. I've been using 192.168.1.50 for app and 192.168.1.51 for mon.
  * Netmask default is fine (255.255.255.0)
  * Gateway default is fine (192.168.1.1)
  * For DNS, I've been using Google's name servers (8.8.8.8)
  * Hostname should be "app" or "mon"
  * Domain name should be left blank

**TODO**: Should we use the local time zone or UTC for these servers? For now, I'm using the local time zone as auto-detected by the installer.

* We've been choosing "No automatic updates" instead of "Security updates only" since Ansible will handle setting up unattended-upgrades.
* It seems that Ubuntu now auto-detects if other operating systems are present, and if none are, automatically installs the bootloader to the MBR. This is a change from the instructions for 12.04, where you always had to confirm to install the bootloader.

# Installing Securedrop from the Admin Workstation

**Note**: everything currently in `docs/install.md` looks good up to "## Set up the App Server".

Boot the Admin Workstation for the Tails Live USB that we created earlier for the Admin Workstation.

Open a terminal.

```
$ sudo apt-get update
$ sudo apt-get install ansible
$ git clone https://github.com/freedomofpress/securedrop.git

# TODO verify the git repo (signed tags?)
# TODO when the release is cut, make sure you checkout master. Until then you want to use develop.

# Change into the ansible-base directory
$ cd securedrop/install_files/ansible-base

# Create SSH key on the admin workstation
# TODO no passphrase? passphrase? I've been testing with no passphrase
# (since it's stored on an encrypted volume).
$ ssh-keygen -t rsa -b 4096

# Copy the keyfile to both servers
# TODO This will ask us to verify the SSH fingerprints of each server. Do we
# want to verify these? The way to do it would be to add a step when installing
# Ubuntu on each server where we log in and do ssh-keygen -l -f
# /etc/ssh/ssh_host_rsa_key, then record that value to compare here.
ssh-copy-id username@IP_address


# Verify that you are able to log in to both servers (without a password)
ssh username@IP_address

# Once you've verified that you are able to log in to each server, log out
$ logout # or Ctrl-D
```

Gather the required info for the installation:

* Application GPG public key file
* Application GPG public key fingerprint
* Admin GPG public key file (for encrypting OSSEC alerts)
* Admin GPG public key fingerprint
* Custom header image file (.jpg or .png, size should be as small as possible)
* OSSEC alert info (TODO: how best to determine this?)

Copy the required files to `securedrop/install_files/ansible-base`.

```
# Replace the IP addresses in the default inventory file with the ones you chose for app and mon
nano inventory

# Fill out prod-specific.yml with the values from the required info
nano prod-specific.yml

# Run the playbook. You will be prompted to enter the sudo password for each server.
# USERNAME is the user to log in as on app and mon. It should be whatever user you copied the ssh keys to.
ansible-playbook -i inventory -u USERNAME -K --sudo site.yml

# Use the values fetched from the app and monitor servers with Micah's Tails_files program
app-document-aths
app-ssh-aths
mon-ssh-aths

# There is also a app-source-ths

# Update inventory replacing the ip addresses with the onion addresses
nano inventory

# Reboot both servers so they will boot in the grsec kernel
ssh USERNAME@<app ssh>.onion sudo shutdown -r now
ssh USERNAME@<mon ssh>.onion sudo shutdown -r now
```


# Testing the installation

## Test connectivity

* ssh over tor into both servers
* sudo as root
* both web interfaces are available over tor
* OSSEC alert about OSSEC starting after reboot is received.
* run 'unattended-upgrades' reboot and run again
* run `uname -r` verify you are booted into grsec kernel
* `aa-status` shows the apparmor status
* `iptables-save` shows the current applied iptable rules

## Test web application

1. Configure your torrc with the values with app-document-aths, app-ssh-aths, and mon-ssh-aths, and reload your Tor.
2. Make sure the source interface is available, and that you can make a submission.
3. SSH to the app server, `sudo su`, cd to /var/www/securedrop, and run `./manage.py add_admin` to create a test admin user.
4. Test that you can access the document interface, and that you can log in as the admin user you just created.
5. Test replying to the test submission.
6. Test that the source received the reply.
7. **TODO** More testing...

