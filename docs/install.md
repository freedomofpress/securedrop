Installing SecureDrop
=====================

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](https://github.com/thlorenz/doctoc)*

- [Before you begin](#before-you-begin)
  - [Set up Tails USB sticks](#set-up-tails-usb-sticks)
    - [Installing Tails](#installing-tails)
    - [Enabling Persistence Storage on Tails](#enabling-persistence-storage-on-tails)
- [Set up the Secure Viewing Station](#set-up-the-secure-viewing-station)
  - [Create a GPG key for the SecureDrop application](#create-a-gpg-key-for-the-securedrop-application)
  - [Import GPG keys for journalists with access to SecureDrop](#import-gpg-keys-for-journalists-with-access-to-securedrop)
- [Set up Admin Tails USB and Workstation](#set-up-admin-tails-usb-and-workstation)
  - [Start Tails and enable the persistent volume](#start-tails-and-enable-the-persistent-volume)
  - [Download the SecureDrop repository](#download-the-securedrop-repository)
  - [Passphrase Database](#passphrase-database)
- [Set up the Network Firewall](#set-up-the-network-firewall)
- [Set up the Servers](#set-up-the-servers)
- [Install the SecureDrop application](#install-the-securedrop-application)
  - [Install Ansible](#install-ansible)
  - [Set up SSH keys for the Admin](#set-up-ssh-keys-for-the-admin)
  - [Gather the required information](#gather-the-required-information)
  - [Install SecureDrop](#install-securedrop)
  - [Set up access to the authenticated hidden services](#set-up-access-to-the-authenticated-hidden-services)
  - [Set up SSH host aliases](#set-up-ssh-host-aliases)
  - [Set up two-factor authentication for the Admin](#set-up-two-factor-authentication-for-the-admin)
  - [Create users for the web application](#create-users-for-the-web-application)
- [Finalizing the Installation](#finalizing-the-installation)
  - [Test the web application and connectivity](#test-the-web-application-and-connectivity)
  - [Additional testing](#additional-testing)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

This guide outlines the steps required to install SecureDrop 0.3.x. If you are looking to upgrade from version 0.2.1, please use the [migration scripts](/migration_scripts/0.3) we have created.

## Before you begin

When running commands or editing configuration files that include filenames, version numbers, userames, and hostnames or IP addresses, make sure it all matches your setup. This guide contains several words and phrases associated with SecureDrop that you may not be familiar with. A basic familiarity with Linux, the GNU core utilities and Bash shell is highly advantageous. It's recommended that you read our [Terminology Guide](/docs/terminology.md) once before starting and keep it open in another tab to refer back to.

You will also need the inventory of hardware items for the installation listed in our [Hardware Guide](/docs/hardware.md).
	
### Set up Tails USB sticks

Before installing the SecureDrop application, the first thing you need to do is set up several USB sticks with the Tails operating system. Tails is a privacy-enhancing live operating system that runs on removable media, such as a DVD or a USB stick. It sends all your Internet traffic through Tor, does not touch your computer's hard drive, and securely wipes unsaved work on shutdown.

You'll need to install Tails onto at least four USB sticks and enable persistent storage, which is an encrypted volume that allows you to save information even when Tails securely wipes everything else:

1. *offline Tails USB*
	
2. *admin Tails USB*

3. *journalist Tails USB*.

4. *long-term storage Tails USB*

You will need one Tails USB for each journalist, so if you have more than one journalist checking SecureDrop, you'll need to create even more. It's a good idea to label or color-code these in order to tell them apart.

#### Installing Tails

We recommend creating an initial Tails Live DVD or USB, and then using that to create additional Tails Live USBs with the *Tails Installer*, a special program that is only available from inside Tails. *You will only be able to create persistent volumes on USB sticks that had Tails installed via the Tails Installer*.

The [Tails website](https://tails.boum.org/) has detailed and up-to-date instructions on how to download and verify Tails, and how to create a bootable Tails USB stick. Follow the instructions at these links and then return to this page:

* [Download and verify the Tails .iso](https://tails.boum.org/download/index.en.html)
* [Install onto a USB stick or SD card](https://tails.boum.org/doc/first_steps/installation/index.en.html)

Note that this process will take some time because once you have one copy of Tails, you have to create each additional Tails USB, shut down, and boot into each one to complete the next step.

Also, you should be aware that Tails doesn't always completely shut down and reboot properly when you click "restart", so if you notice a signficant delay, you may have to manually power off and restart your computer for it to work properly.

#### Enabling Persistence Storage on Tails

Creating an encrypted persistent volume will allow you to securely save information and settings in the free space that is left on your Tails USB. This information will remain available to you even if you reboot Tails. (Tails securely erases all other data on every shutdown.)

You will need to create a persistent storage on each Tails USB, with a unique password for each.

Please use the instructions on the [Tails website](https://tails.boum.org/doc/first_steps/persistence/index.en.html) to make the persistent volume on each Tails USB stick you create.

When creating the persistence volume, you will be asked to select from a list of features, such as 'Personal Data'. We recommend that you enable **all** features.

Some other things to keep in mind:

* You will want to create a persistent volume for all three main Tails USBs: the *offline Tails USB*, the *admin Tails USB*, and the *journalist Tails USB*.

* The admin and the journalist should create separate passwords for their own USBs.

* Only the journalist should have access to the *offline Tails USB password*, though during the initial installation, often the admin will create their own password to facilitate setup and then the journalist can change it afterwards.

* Unlike many of the other passphrases for SecureDrop, the persistence volume passwords must be remembered by the admin and journalist. So after creating each passphrase, you should write it down until you can memorize it, and then destroy the paper you wrote it on.

NOTE: Make sure that you never use the *offline Tails USB* on a computer connected to the Internet or a local network. This USB will be used on the air-gapped *Secure Viewing Station* only.

## Set up the Secure Viewing Station

The *Secure Viewing Station (SVS)* is a computer that is kept offline and only ever used together with the *offline Tails USB*. Since this machine will never touch the Internet or run an operating system other than Tails on a USB, it does not need a hard drive or network device.

We recommend that you physically remove the hard drive and networking cards, such as wireless and Bluetooth, from this machine. If you are unable to remove a card, place tape over the port or otherwise physically disable it. If you have questions about using an older machine for this purpose, please contact us at securedrop@freedom.press.

At this point, you should have created a Tails Live USB with persistence on the *offline Tails USB*. If you haven't, follow the instructions in the first half of our [Tails Guide](/docs/tails_guide.md).

Boot your *offline Tails USB* on the *Secure Viewing Station*.

After it loads, you should see a "Welcome to Tails" screen with two options. Select *Yes* to enable the persistent volume and enter your password, but do NOT click Login yet. Under 'More Options,' select *Yes* and click *Forward*.

Enter an *Administration password* for use with this specific Tails session and click *Login*. (NOTE: the *Administration password* is a one-time password. It will reset every time you shut down Tails.)

### Create a GPG key for the SecureDrop application

When a document or message is submitted to SecureDrop by a source, it is automatically encrypted with the SecureDrop Application GPG key. You will need to create that key now before you continue with the installation.

After booting up Tails, you will need to manually set the system time before you create the GPG key. To set the system time, right-click the time in the top menu bar and select *Adjust Date & Time.*

Click *Unlock* in the top-right corner of the dialog window and enter your *Administration password.* Set the correct time, region and city.

Then click *Lock*, enter your password one more time and wait for the system time to update in the top panel.

Once that's done, follow the steps below to create a GPG key.

* Open a terminal ![Terminal](images/terminal.png) and run `gpg --gen-key`
* When it says, `Please select what kind of key you want`, choose `(1) RSA and RSA (default)`
* When it asks, `What keysize do you want?` type **`4096`**
* When it asks, `Key is valid for?` press Enter to keep the default
* When it asks, `Is this correct?` verify that you've entered everything correctly so far, and type `y`
* For `Real name` type: `SecureDrop`
* For `Email address`, leave the field blank and press Enter
* For `Comment` type `[Your Organization's Name] SecureDrop Application GPG Key`
* Verify that everything is correct so far, and type `o` for `(O)kay`
* It will pop up a box asking you to type a passphrase, but it's safe to click okay without typing one (since your persistent volume is encrypted, this GPG key is already protected)
* Wait for your GPG key to finish generating

To manage GPG keys using the graphical interface (a program called Seahorse), click the clipboard icon ![gpgApplet](images/gpgapplet.png) in the top right corner and select "Manage Keys". You should see the key that you just generated under "GnuPG Keys."

![My Keys](images/install/keyring.png)

Select the key you just generated and click "File" then "Export". Save the key to the *Transfer Device* as `SecureDrop.pgp`, and make sure you change the file type from "PGP keys" to "Armored PGP keys" which can be switched right above the 'Export' button. Click the 'Export' button after switching to armored keys.

NOTE: This is the public key only.

![My Keys](images/install/exportkey.png)
![My Keys](images/install/exportkey2.png)

You'll need to verify the fingerprint for this new key during the `App Server` installation. Double-click on the newly generated key and change to the `Details` tab. Write down the 40 hexadecimal digits under `Fingerprint`. (Your GPG key fingerprint will be different than what's in this photo.)

![Fingerprint](images/install/fingerprint.png)

### Import GPG keys for journalists with access to SecureDrop

While working on a story, journalists may need to transfer some documents or notes from the *Secure Viewing Station* to the journalist's work computer on the corporate network. To do this, the journalists should re-encrypt them with their own keys. If a journalist does not already have a personal GPG key, he or she can follow the same steps above to create one. The journalist should store the private key somewhere safe; the public key should be stored on the *Secure Viewing Station*.

If the journalist does have a key, transfer their public key from wherever it is located to the *Secure Viewing Station*, using the *Transfer Device*. Open the file manager ![Nautilus](images/nautilus.png) and double-click on the public key to import it. If the public key is not importing, rename the file to end in ".asc" and try again.

![Importing Journalist GPG Keys](images/install/importkey.png)

At this point, you are done with the *Secure Viewing Station* for now. You can shut down Tails, grab the *admin Tails USB* and move over to your regular workstation.

## Set up Admin Tails USB and Workstation

Earlier, you should have created the *admin Tails USB* along with a persistence volume for it. Now, we are going to add a couple more features to the *admin Tails USB* to facilitate SecureDrop's setup.

If you have not switched to and booted the *admin Tails USB* on your regular workstation, do so now.

### Start Tails and enable the persistent volume

After you boot the *admin Tails USB* on your normal workstation, you should see a *Welcome to Tails* screen with two options. Select *Yes* to enable the persistent volume and enter your password, but do NOT click Login yet. Under 'More Options," select *Yes* and click *Forward*.

Enter an *Administration password* for use with this specific Tails session and click *Login*. (NOTE: the *Administration password* is a one-time password. It will reset every time you shut down Tails.)

After Tails is fully booted, make sure you're connected to the Internet ![Network](images/network-wired.png) and that the Tor's Vidalia indicator onion ![Vidalia](images/vidalia.png) is green, using the icons in the upper right corner.

### Download the SecureDrop repository

The rest of the SecureDrop-specific configuration is assisted by files stored in the SecureDrop Git repository. We're going to be using this again once SecureDrop is installed, but you should download it now. To get started, open a terminal ![Terminal](images/terminal.png). You will use this Terminal throughout the rest of the install process.

Start by running the following commands to download the git repository.

NOTE: Since the repository is fairly large and Tor can be slow, this may take a few minutes.

```sh
cd ~/Persistent
git clone https://github.com/freedomofpress/securedrop.git
```

Before proceeding, verify the signed git tag for this release.

First, download the *Freedom of the Press Foundation Master Signing Key* and verify the fingerprint.

    gpg --keyserver pool.sks-keyservers.net --recv-key B89A29DB2128160B8E4B1B4CBADDE0C7FC9F6818
    gpg --fingerprint B89A29DB2128160B8E4B1B4CBADDE0C7FC9F6818

The Freedom of the Press Foundation Master Signing Key should have a fingerprint of "B89A 29DB 2128 160B 8E4B  1B4C BADD E0C7 FC9F 6818". If the fingerprint does not match, fingerprint verification has failed and you *should not* proceed with the installation. If this happens, please contact us at securedrop@freedom.press.

Verify that the current release tag was signed with the master signing key.

    cd securedrop/
    git checkout 0.3.2
    git tag -v 0.3.2

You should see 'Good signature from "Freedom of the Press Foundation Master Signing Key"' in the output of `git tag`. If you do not, signature verification has failed and you *should not* proceed with the installation. If this happens, please contact us at securedrop@freedom.press.

### Passphrase Database

We provide a KeePassX password database template to make it easier for admins and journalists to generate strong, unique passphrases and store them securely. Once you have set up Tails with persistence and have cloned the repo, you can set up your personal password database using this template.

You can find the template in `/Persistent/securedrop/tails_files/securedrop-keepassx.xml` within the SecureDrop repository. Note that you will not be able to access your passwords if you forget the master password or the location of the key file used to protect the database.

To use the template:

 * Open the KeePassX program ![KeePassX](images/keepassx.png) which is already installed on Tails
 * Select `File`, `Import from...`, and `KeePassX XML (*.xml)`
 * Navigate to the location of `securedrop-keepassx.xml`, select it, and click `Open`
 * Set a strong master password to protect the password database (you will have to write this down/memorize it)
 * Click `File` and `Save Database As`
 * Save the database in the Persistent folder

## Set up the Network Firewall

Now that you've set up your password manager, you can move on to setting up the Network Firewall. You should stay logged in to your *admin Tails USB*, but please go to our [Network Firewall Guide](/docs/network_firewall.md) for instructions for setting up the Network Firewall. When you are done, you will be sent back here to continue with the next section.

## Set up the Servers

Now that the firewall is set up, you can plug the *Application Server* and the *Monitor Server* into the firewall. If you are using a setup where there is a switch on the LAN port, plug the *Application Server* into the switch and plug the *Monitor Server* into the OPT1 port.

Install Ubuntu Server 14.04 (Trusty) on both servers. For detailed instructions on installing and configuring Ubuntu for use with SecureDrop, see our [Ubuntu Install Guide](/docs/ubuntu_config.md). When you are done, make sure you save the following information:

* The IP address of the App Server
* The IP address of the Monitor Server
* The non-root user's name and password on each server.

Before continuing, you'll also want to make sure you can connect to the App and Monitor servers. You should still have the Admin Workstation connected to the firewall from the firewall setup step. In the terminal, verify that you can SSH into both servers, authenticating with your password:

```sh
ssh <username>@<App IP address> hostname
ssh <username>@<Monitor IP address> hostname
```

Once you have verified that you can connect, continue with the installation. If you cannot connect, check the firewall logs.

## Install the SecureDrop application

### Install Ansible

You should still be on your admin workstation with your *admin Tails USB*.

Next you need to install Ansible. To do this, you first need to update your package manager's package lists to be sure you get the latest version of Ansible. It should take a couple minutes.

    sudo apt-get update

Now, install Ansible by entering this command:

    sudo apt-get install ansible

### Set up SSH keys for the Admin

Now that you've verified the code that's needed for installation, you need to create an SSH key on the Admin Workstation. Initially, Ubuntu has SSH configured to authenticate users with their password. This new key will be copied to the *Application Server* and the *Monitor Server*, and will replace the use of the password for authentication. Since the Admin Live USB was set up with [SSH Client persistence](https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html#index3h2), this key will be saved on the Admin Live USB and can be used in the future to authenticate to the servers in order to perform administrative tasks.

First, generate the new SSH keypair:

    $ ssh-keygen -t rsa -b 4096

You'll be asked to "enter file in which to save the key." Here you can just keep the default, so type enter. Choose a strong passphrase to protect the SSH private key.

You should save this passphrase in your KeePassX password manager. You can also generate the passphrase using KeePassX as well.

Once the key has finished generating, you need to copy the public key to both servers. Use `ssh-copy-id` to copy the public key to each server in turn. Use the user name and password that you set up during Ubuntu installation.

    $ ssh-copy-id <username>@<App IP address>
    $ ssh-copy-id <username>@<Mon IP address>

Verify that you are able to authenticate to both servers by running the below commands (you will be prompted for the SSH password you just created).

```sh
ssh <username>@<App IP address> hostname
ssh <username>@<Montior IP address> hostname
```
Make sure to run the 'exit' command after testing each one.

### Gather the required information

Make sure you have the following information and files before continuing:

* The *App Server* IP address
* The *Monitor Server* IP address
* The SecureDrop application's GPG public key (from the *Transfer Device*)
* The SecureDrop application's GPG key fingerprint
* The email address that will receive alerts from OSSEC
* The GPG public key and fingerprint for the email address that will receive the alerts
* Connection information for the SMTP relay that handles OSSEC alerts. For more information, see the [OSSEC Alerts Guide](/docs/ossec_alerts.md).
* The first username of a journalist who will be using SecureDrop (you can add more later)
* The username of the system administrator* (Optional) An image to replace the SecureDrop logo on the *Source Interface* and *Document Interface*
    * Recommended size: `500px x 450px`
    * Recommended format: PNG

### Install SecureDrop

From the base of the SecureDrop repo, change into the `ansible-base` directory:

    $ cd install_files/ansible-base

You will have to copy the following required files to `install_files/ansible-base`:

* SecureDrop Application GPG public key file
* Admin GPG public key file (for encrypting OSSEC alerts)
* (Optional) Custom header image file

The SecureDrop application GPG key should be located on your *Transfer Device* from earlier. It will depend on the location where the USB stick is mounted, but for example, if you are already in the ansible-base directory, you can just run:

    $ cp /media/[USB folder]/SecureDrop.asc .

Or you may use the copy and paste capabilities of the file manager. Repeat this step for the Admin GPG key and custom header image.

Now you must edit a couple configuration files. You can do so using gedit, vim, or nano. Double-clicking will suffice to open them.

Edit the inventory file, `inventory`, and update the default IP addresses with the ones you chose for app and mon. When you're done, save the file.

Edit the file `prod-specific.yml` and fill it out with values that match your environment. At a minimum, you will need to provide the following:

 * User allowed to connect to both servers with SSH: `ssh_users`
 * IP address of the Monitor Server: `monitor_ip`
 * Hostname of the Monitor Server: `monitor_hostname`
 * Hostname of the Application Server: `app_hostname`
 * IP address of the Application Server: `app_ip`
 * The SecureDrop application's GPG public key: `securedrop_app_gpg_public_key`
 * The SecureDrop application's GPG key fingerprint: `securedrop_app_gpg_fingerprint`
 * GPG public key used when encrypting OSSEC alerts: `ossec_alert_gpg_public_key`
 * Fingerprint for key used when encrypting OSSEC alerts: `ossec_gpg_fpr`
 * The email address that will receive alerts from OSSEC: `ossec_alert_email`
 * The reachable hostname of your SMTP relay: `smtp_relay`
 * The secure SMTP port of your SMTP relay: `smtp_relay_port` (typically 25, 587, or 465. Must support TLS encryption)
 * Email username to authenticate to the SMTP relay: `sasl_username`
 * Domain name of the email used to send OSSEC alerts: `sasl_domain`
 * Password of the email used to send OSSEC alerts: `sasl_password`
 * The fingerprint of your SMTP relay (optional): `smtp_relay_fingerprint`

When you're done, save the file and quit the editor.

Now you are ready to run the playbook! This will automatically configure the servers and install SecureDrop and all of its dependencies. `<username>` below is the user you created during the Ubuntu installation, and should be the same user you copied the SSH public keys to.

    $ ansible-playbook -i inventory -u <username> -K --sudo securedrop-prod.yml

You will be prompted to enter the sudo password for the app and monitor servers (which should be the same).

The Ansible playbook will run, installing SecureDrop plus configuring and hardening the servers. This will take some time, and it will return the terminal to you when it is complete. If an error occurs while running the playbook, please submit a detailed [GitHub issue](https://github.com/freedomofpress/securedrop/issues/new) or send an email to securedrop@freedom.press.

Once the installation is complete, the addresses for each Tor Hidden Service will be available in the following files in `install_files/ansible-base`:

* `app-source-ths`: This is the .onion address of the Source Interface
* `app-document-aths`: This is the `HidServAuth` configuration line for the Document Interface. During a later step, this will be automatically added to your Tor configuration file in order to exclusively connect to the hidden service.
* `app-ssh-aths`: Same as above, for SSH access to the Application Server.
* `mon-ssh-aths`: Same as above, for SSH access to the Monitor Server.

Update the inventory, replacing the IP addresses with the corresponding onion addresses from `app-ssh-aths` and `mon-ssh-aths`. This will allow you to re-run the Ansible playbooks in the future, even though part of SecureDrop's hardening restricts SSH to only being over the specific authenticated Tor Hidden Services.

### Set up access to the authenticated hidden services

To complete setup of the Admin Workstation, we recommend using the scripts in `tails_files` to easily and persistently configure Tor to access these hidden services.

Navigate to the directory with these scripts and type these commands into the terminal:

```
cd ~/Persistent/securedrop/tails_files/
sudo ./install.sh
```

Type the administration password that you selected when starting Tails and hit enter. The installation process will download additional software and then open a text editor with a file called *torrc_additions*.

Edit this file, inserting the *HidServAuth* information for the three authenticated hidden services that you just received. You can double-click or use the 'cat' command to read the values from `app-document-aths`, `app-ssh-aths` and `mon-ssh-aths`. This information includes the address of the Document Interface, each server's SSH daemon and your personal authentication strings, like in the example below:

```
# add HidServAuth lines here
HidServAuth gu6yn2ml6ns5qupv.onion Us3xMTN85VIj5NOnkNWzW # client: user
HidServAuth fsrrszf5qw7z2kjh.onion xW538OvHlDUo5n4LGpQTNh # client: admin
HidServAuth yt4j52ajfvbmvtc7.onion vNN33wepGtGCFd5HHPiY1h # client: admin
```

When you are done, click *Save* and **close** the text editor. The script will finish running soon thereafter.

Running `install.sh` sets up an initialization script that automatically updates Tor's configuration to work with the authenticated hidden services every time you login to Tails. As long as Tails is booted with the persistent volume enabled then you can open the Tor Browser and reach the Document Interface as normal, as well as connect to both servers via secure shell. Tor's [hidden service authentication](https://www.torproject.org/docs/tor-manual.html.en#HiddenServiceAuthorizeClient) restricts access to only those who have the 'HidServAuth' values.

### Set up SSH host aliases

This step is optional but makes it much easier to connect to and administer the servers. Create the file `/home/amnesia/.ssh/config` and add a configuration following the scheme below, but replace `Hostname` and `User` with the values specific to your setup:

```
Host app
  Hostname fsrrszf5qw7z2kjh.onion
  User <ssh_user>
Host mon
  Hostname yt4j52ajfvbmvtc7.onion
  User <ssh_user>
```

Now you can simply use `ssh app` and `ssh mon` to connect to each server, and it will be stored in the Tails Dotfiles persistence.

### Set up two-factor authentication for the Admin

As part of the SecureDrop installation process, you will need to set up two-factor authentication on the App Server and Monitor Server using the Google Authenticator mobile app.

After your torrc has been updated with the HidServAuth values, connect to the App Server using `ssh` and run `google-authenticator`. Follow the instructions in [our Google Authenticator guide](/docs/google_authenticator.md) to set up the app on your Android or iOS device.

To disconnect enter the command `exit`. Now do the same thing on the Monitor Server. You'll end up with an account for each server in the Google Authenticator app that generates two-factor codes needed for logging in.

### Create users for the web application

Now SSH to the App Server, `sudo su`, cd to /var/www/securedrop, and run `./manage.py add_admin` to create the first admin user for yourself. Make a password and store it in your KeePassX database. This admin user is for the SecureDrop Admin + Document Interface and will allow you to create accounts for the journalists.

The `add_admin` command will require you to keep another two-factor authentication code. Once that's done, you should open the Tor Browser ![TorBrowser](images/torbrowser.png) and navigate to the Document Interface's .onion address.

For adding journalist users, please refer now to our [Admin Interface Guide](/docs/admin_interface.md).

## Finalizing the Installation

Some of the final configuration is included in these testing steps, so *do not skip them!*

### Test the web application and connectivity

1. SSH to both servers over Tor
 * As an admin running Tails with the proper HidServAuth values in your `/etc/torrc` file, you should be able to SSH directly to the App Server and Monitor Server.
 * Post-install you can now SSH _only_ over Tor, so use the onion URLs from app-ssh-aths and mon-ssh-aths and the user created during the Ubuntu installation i.e. `ssh <username>@m5apx3p7eazqj3fp.onion`.
2. Make sure the Source Interface is available, and that you can make a submission.
 * Do this by opening the Tor Browser and navigating to the onion URL from `app-source-ths`. Proceed through the codename generation (copy this down somewhere) and you can submit a message or attach any random unimportant file.
 * Usage of the Source Interface is covered by our [Source User Manual](/docs/source_user_manual.md).
3. Test that you can access the Document Interface, and that you can log in as the admin user you just created.
 * Open the Tor Browser and navigate to the onion URL from app-document-aths. Enter your password and two-factor authentication code to log in.
 * If you have problems logging in to the Admin/Document Interface, SSH to the App Server and restart the ntp daemon to synchronize the time: `sudo service ntp restart`. Also check that your smartphone's time is accurate and set to network time in its device settings.
4. Test replying to the test submission.
 * While logged in as an admin, you can send a reply to the test source submission you made earlier.
 * Usage of the Document Interface is covered by our [Journalist User Manual](/docs/journalist_user_manual.md).
5. Test that the source received the reply.
 * Within Tor Browser, navigate back to the app-source-ths URL and use your previous test source codename to log in (or reload the page if it's still open) and check that the reply you just made is present.
6. We highly recommend that you create persistent bookmarks for the Source and Document Interface addresses within Tor Browser.
7. Remove the test submissions you made prior to putting SecureDrop to real use. On the main Document Interface page, select all sources and click 'Delete selected'.

Once you've tested the installation and verified that everything is working, see [How to Use SecureDrop](/docs/journalist_user_manual.md).

### Additional testing

1. On each server, check that you can execute privileged commands by running `sudo su`.
2. Run `uname -r` to verify you are booted into grsecurity kernel. The string `grsec` should be in the output.
3. Check the AppArmor status on each server with `sudo aa-status`. On a production instance all profiles should be in enforce mode.
4. Check the current applied iptables rules with `iptables-save`. It should output *approximately* 50 lines.
5. You should have received an email alert from OSSEC when it first started. If not, review our [OSSEC Alerts Guide](/docs/ossec_alerts.md).

If you have any feedback on the installation process, please let us know! We're always looking for ways to improve, automate and make things easier.
