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

Connect the Admin Workstation's Ethernet port to the shared firewall. Boot the Admin Workstation with the Admin Tails USB that we created earlier. Make sure to type the password in for your persistence drive, but before clicking enter, also click 'yes' for more options. Click 'forward.'

You will be prompted to enter a root password. This is a one-time session password, so you will only be creating it for this one session. 

Open a terminal (click the terminal icon in the top menu).

First, you need to update your package manager's package lists to be sure you get the latest version of Ansible. It should take a couple minutes.

    $ sudo apt-get update

Now, install Ansible by entering this command:

    $ sudo apt-get install ansible

Next, you will need to clone the SecureDrop repository:

**TODO** verify the git repo (signed tags?)

    $ git clone https://github.com/freedomofpress/securedrop.git

Before proceeding, double check to make sure what branch you are in. You should be in the master branch, but it's possible you will also be in develop. Makesure to check out master by running this command:

    $ cd securedrop 
    $ git checkout master

Next, you will have to change into the ansible-base directory:

    $ cd install_files/ansible-base

Now that you're in the right directory, you'll want to create an SSH key on the admin workstation. To do so, run this command:

    $ ssh-keygen -t rsa -b 4096

You'll be asked to "enter file in which to save the key." Here you can just keep the default and click enter. You can also just click enter when it asks you to create a passphrase (since this will be protected by the persistence passphrase anyways). 

Here is where you will have to copy the SSH public key to both servers. Use the user name and password that you set up during Ubuntu installation. First do the 'Application Server' then do the 'Monitor Server.'

**TODO** This will ask us to verify the SSH fingerprints of each server. Do we want to verify these? The way to do it would be to add a step when installing Ubuntu on each server where we log in and do ssh-keygen -l -f /etc/ssh/ssh_host_rsa_key, then record that value to compare here.

    $ ssh-copy-id <username>@<App IP address>
    $ ssh-copy-id <username>@<Mon IP address>

Verify that you are able to log in to both servers (without a password):

    $ ssh <username>@<app_ip_address>
    $ ssh <username>@<mon_ip_address>

Once you've verified that you are able to log in to each server, you can log out of each by typing this:

    $ logout # or Ctrl-D

Gather the required info for the installation:

Copy the following required files to `securedrop/install_files/ansible-base`:

* Application GPG public key file
* Admin GPG public key file (for encrypting OSSEC alerts)
* Custom header image file (.jpg or .png, size should be as small as possible)

It will depend what the file location of your USB stick is, but, for an example, if you are already in the ansible-base directory, you can just run: 

    $ cp /media/[USB folder]/SecureDrop.asc .

Then repeat the same step for the Admin GPG key and custom header image.

Next, you're going to edit the inventory file and replace the default IP addresses with the ones you chose for app and mon. First, run the below command. Here, `editor` refers to your preferred text editor (nano, vim, emacs, etc.).

    $ editor inventory

After changing the IP addresses, save the changes to the inventory file and quit the editor.

Then, fill out prod-specific.yml with the Application Server IP and hostname, along with the same information for the Monitor Server (you should have had this information saved from when you installed Ubuntu).

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

