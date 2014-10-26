# Requirements

You will need the following hardware items for this installation. For details on specific hardware recommendations, see [the Hardware Guide](hardware.md).

* Application Server
* Monitor Server
* Admin Workstation (any spare computer that can be connected to the firewall and can run Tails)
* 4 USB sticks:
    * Ubuntu Live USB (to install Ubuntu on the servers)
    * Tails Live USB (to set up other Tails Live USB's with persistence)
    * Admin Live USB
    * Admin Transfer USB

We recommend labeling and/or color-coding the USB sticks to help you keep track of them.

You will additionally need to gather the following files and pieces of information:

* Application GPG public key file
* Application GPG public key fingerprint
* Admin GPG public key file (for encrypting OSSEC alerts)
* Admin GPG public key fingerprint
* Custom header image file (.jpg or .png, size should be as small as possible)
* OSSEC alert info (**TODO**: how best to determine this?)

If you have a GPG public key file, you can get the fingerprint easily with `gpg --with-fingerprint path/to/keyfile`.

# Tails setup

*Tested with Tails 1.2 released October 16, 2014*

**TODO**: dd'ing the live USB on Mac using the instructions on the Tails website is incredibly slow. There should be something we can do with the flags to dd to speed it up.

## Admin Live USB

In this section we will set up the Admin Live USB, a Tails Live USB with persistence.

Start by booting the Admin Workstation from the Tails Live USB. To do this, insert the Tails Live USB and boot the machine. On reboot, open the boot menu and select the Tails Live USB from the menu. On the NUCs, to reboot you should first press the power button to trigger shutdown. Once the machine has shut down, press the power button again to boot it. As it boots, hold F10 to get the boot menu.

At the *Welcome to Tails* dialog, choose **No** for *More options?* and click **Login**. Once the desktop environment has loaded, insert the spare USB that will become a Tails live USB with persistence for the Admin Workstation.

Click the *Applications* menu in the top left corner of the screen, and open *Applications > Tails > Tails Installer*. Choose **Clone & Install** and select the USB stick you inserted as the Target Device. In my testing, it was automatically selected because it was the only other USB device inserted at the time. Click **Install Tails** and click **Yes** to continue. When the installer is done, click **OK** to close the program.

You will be able to set up persistence on this new Tails USB because it was created with the Tails Installer. Shut down the running Tails instance by clicking the power button icon in the top right corner of the screen and choosing **Shut down immediately**. Remove the original Tails USB, leaving the new Admin Live USB, and boot the Admin Workstation.

"Welcome to Tails", "More Options?" choose *No* and click *Forward*

Open the Persistence Wizard - click OK, configure the volume, select all options for storage, restart.

# Server setup

Start by plugging the NUCs into a shared firewall. Their static network configuration will need to be stable for Ansible to work.

Install Ubuntu 14.04 (Trusty) on both NUCs. For detailed information on installing and configuring Ubuntu for use with SecureDrop, see the [Ubuntu Install Guide](docs/ubuntu_config.md).

# Installing Securedrop from the Admin Workstation

**Note**: everything currently in `docs/install.md` looks good up to "## Set up the App Server".

Connect the Admin Workstation's Ethernet port to the shared firewall. Boot the Admin Workstation with the Admin Live USB that we created earlier.

Open a terminal (click the terminal icon in the top menu).

Update your packages and install ansible:

    $ sudo apt-get update
    $ sudo apt-get install ansible

Clone the SecureDrop repository.

**TODO** verify the git repo (signed tags?)

**TODO** when the release is cut, make sure you checkout master. Until then you want to use develop.

    $ git clone https://github.com/freedomofpress/securedrop.git

Change into the ansible-base directory:

    $ cd securedrop/install_files/ansible-base

Create an SSH key on the admin workstation

**TODO** no passphrase? passphrase? I've been testing with no passphrase (since it's stored on an encrypted volume).

    $ ssh-keygen -t rsa -b 4096

Copy the SSH public key to both servers. Use the user name and password that you set up during Ubuntu installation.

**TODO** This will ask us to verify the SSH fingerprints of each server. Do we want to verify these? The way to do it would be to add a step when installing Ubuntu on each server where we log in and do ssh-keygen -l -f /etc/ssh/ssh_host_rsa_key, then record that value to compare here.

    $ ssh-copy-id <username>@<app_ip_address>
    $ ssh-copy-id <username>@<mon_ip_address>

Verify that you are able to log in to both servers (without a password):

    $ ssh-copy-id <username>@<app_ip_address>
    $ ssh-copy-id <username>@<mon_ip_address>

Once you've verified that you are able to log in to each server, log out of both serves:

    $ logout # or Ctrl-D

Gather the required info for the installation:

Copy the following required files to `securedrop/install_files/ansible-base`:

* Application GPG public key file
* Admin GPG public key file (for encrypting OSSEC alerts)
* Custom header image file (.jpg or .png, size should be as small as possible)

Edit the inventory file and replace the default IP addresses with the ones you chose for app and mon. Here, `editor` refers to your preferred text editor (nano, vim, emacs, etc.)

    $ editor inventory

Fill out prod-specific.yml with the values from the required info.

    $ editor prod-specific.yml

Run the playbook. You will be prompted to enter the sudo password for each server. `<username>` is the user you created during the Ubuntu installation, and should be the same user you copied the ssh public keys to.

    $ ansible-playbook -i inventory -u <username> -K --sudo site.yml

The ansible playbook will run, installing SecureDrop and configuring and hardening the servers. This will take some time, and will return the Terminal to you when it is complete. If an error occurs while running the playbook, please submit a detailed [Github issue](https://github.com/freedomofpress/securedrop/issues/new) or send an email to securedrop@freedom.press.

**TODO:** we're working on automating these final steps with Ansible

Use the values fetched from the app and monitor servers with Micah's Tails_files program.

* app-source-ths
* app-document-aths
* app-ssh-aths
* mon-ssh-aths

Update inventory replacing the ip addresses with the onion addresses:

    $ editor inventory

Reboot both servers so they will boot in the grsec kernel:

    $ ssh USERNAME@<app ssh>.onion sudo shutdown -r now
    $ ssh USERNAME@<mon ssh>.onion sudo shutdown -r now

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

