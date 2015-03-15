Installing SecureDrop
=====================

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Terminology](#terminology)
  - [App Server](#app-server)
  - [Monitor Server](#monitor-server)
  - [Source Interface](#source-interface)
  - [Document Interface](#document-interface)
  - [Journalist Workstation](#journalist-workstation)
  - [Admin Workstation](#admin-workstation)
  - [Secure Viewing Station](#secure-viewing-station)
  - [Two-Factor Authenticator](#two-factor-authenticator)
  - [Transfer Device](#transfer-device)
- [Before you begin](#before-you-begin)
  - [Computers](#computers)
  - [USBs/DVDs/CDs](#usbsdvdscds)
  - [Passphrases](#passphrases)
    - [Admin](#admin)
    - [Journalist](#journalist)
    - [Secure Viewing Station](#secure-viewing-station-1)
- [Set up the Secure Viewing Station](#set-up-the-secure-viewing-station)
  - [Create a GPG key for the SecureDrop application](#create-a-gpg-key-for-the-securedrop-application)
  - [Import GPG keys for journalists with access to SecureDrop](#import-gpg-keys-for-journalists-with-access-to-securedrop)
- [Set up the Admin USB](#set-up-the-admin-usb)
- [Set up the Network Firewall](#set-up-the-network-firewall)
- [Set up the Servers](#set-up-the-servers)
- [Install SecureDrop](#install-securedrop)
  - [Install Ansible](#install-ansible)
  - [Clone and verify the release code](#clone-and-verify-the-release-code)
  - [Set up SSH keys for the Admin](#set-up-ssh-keys-for-the-admin)
  - [Gather the required information](#gather-the-required-information)
  - [Install SecureDrop](#install-securedrop-1)
  - [Set up two-factor authentication for the Admin](#set-up-two-factor-authentication-for-the-admin)
- [Testing the Installation](#testing-the-installation)
  - [Test the web application and connectivity](#test-the-web-application-and-connectivity)
  - [Additional testing](#additional-testing)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

This guide outlines the steps required to install SecureDrop 0.3. If you are looking to upgrade from version 0.2.1, please use the [migration scripts](https://github.com/freedomofpress/securedrop/tree/develop/migration_scripts/0.3) we have created.

## Before you begin

When running commands or editing configuration files that include filenames, version numbers, admin or journalist names, make sure it all matches your setup. This guide contains several words and phrases associated with SecureDrop that you may not be familiar with. It's recommended you read over our [Terminology Guide](terminology.md) once before starting and keep it open in another tab to refer back to.

You will also need the inventory of hardware items for the installation located [Hardware Guide](hardware.md).
	
### Set up Tails USB sticks

Before installing the SecureDrop application, the first thing you need to do is set up several USB sticks with the Tails operating system. Tails is a secure operating system that is run from removable media, such as a DVD or a USB stick. It sends all your Internet traffic through Tor, does not touch your computer's hard drive, and securely wipes unsaved work on shutdown. 

You'll need to install Tails onto at least three USB sticks and enable persistent storage: one *offline Tails USB*, one *admin Tails USB*, and at least one *journalist Tails USB*. (You'll need one Tails USB for each journalist, so if you have more than one journalist checking SecureDrop, you'll need to create more)

#### Installing Tails

We recommend creating an initial Tails Live DVD or USB, and then using that to create additional Tails Live USBs with the *Tails Installer*, a special program that is only available from inside Tails. *You will only be able to create persistent volumes on USB sticks that had Tails installed via the Tails Installer*.

The [Tails website](https://tails.boum.org/) has detailed and up-to-date instructions on how to download and verify Tails, and how to create a Tails USB stick. Follow the instructions at these links and then return to this page:

* [Download and verify the Tails .iso](https://tails.boum.org/download/index.en.html)
* [Install onto a USB stick or SD card](https://tails.boum.org/doc/first_steps/installation/index.en.html)

Note that this process will take a little while because once you have one version of Tails, you have to create each Tails USB, shutdown, and boot into the new USB to complete the next step.

#### Enabling Persistence Storage on Tails

Creating an encrypted persistent volume will allow you to securely save information in the free space that is left on your Tails USB. This information will remain available to you even if you reboot Tails. (Tails securely wipes all other data on every shutdown.)

Instructions on how to create and use this volume can be found on the [Tails website](https://tails.boum.org/doc/first_steps/persistence/index.en.html). When creating the persistence volume, you will be asked to select from a list of persistence features, such as 'personal data.' We recommend that you enable **all** features.

--You will want to create a persistent volume for all three main Tails USBs: the *offline Tails USB*, the *admin Tails USB*, and the *journalist Tails USB*. 

--The admin and the journalist should create separate passwords for their own USBs. 

--Only the journalist should have access to the *offline Tails USB password*, though during the initial installation, often the admin will create their own password to facilitate set-up and then the journalist can go back in and change it afterwards.

--Unlike many of the other passwords for SecureDrop, the persistence volume passwords must be remembered by the admin and jouranlist. So after creating them, you should write it down until you can memorize it, and then destroy the paper you wrote it on.

NOTE: Make sure that you never connect the *offline Tails USB* to the Internet. This USB will be used on the airgapped *Secure Viewing Station* only.

## Set up the Secure Viewing Station

The *Secure Viewing Station (SVS)* is a computer that is kept offline and only ever used together with the *offline Tails USB*. Since this machine will never touch the Internet or run an operating system other than Tails on a USB, it does not need a hard drive or network device.

We recommend that you physically remove the hard drive and networking cards, such as wireless and bluetooth, from this machine. If you are unable to remove a card, tape over it or otherwise physically disable it. If you have questions about using an old machine for this purpose, please contact us at securedrop@freedom.press.

At this point, you should have created a Tails Live USB with persistence on the *offline Tails USB*. If you haven't, follow the instructions in the [Tails Guide](tails_guide.md). 

Boot your *offline Tails USB* with the persistent volume enabled on the *Secure Viewing Station*.

When starting Tails, you should see a *Welcome to Tails*-screen with two options. Select *Yes* to enable the persistent volume and enter your password. Select *Yes* to show more options and click *Forward*. Enter an *Administration password* for use with this current Tails session and click *Login*. (NOTE: the *Administration password* is a one time password. It will reset every time you shut down Tails.)

### Create a GPG key for the SecureDrop application

When a document is submitted through the *Source Interface* on the *App Server*, the document is automatically encrypted with the SecureDrop Application GPG key. If you have not previously created a GPG key for SecureDrop, you will need to create one now before you continue with the installation. 

After booting up Tails, you will need to manually set the system time before you create the GPG key. To set the system time, right-click the time in the top menu bar and select *Adjust Date & Time.* 

Click *Unlock* in the top-right corner of the dialog window and enter your *Administration password.* Set the correct time, and region. Then click *Lock*, enter your password one more time and wait for the system time to update in the top menu bar. 

Once that's done, follow the steps below to create a GPG key.

* Open a terminal and run `gpg --gen-key`
* When it says, `Please select what kind of key you want`, choose `(1) RSA and RSA (default)`
* When it asks, `What keysize do you want?` type `4096`
* When it asks, `Key is valid for?` press Enter to keep the default
* When it asks, `Is this correct?` verify that you've entered everything correctly so far, and type `y`
* For `Real name` type: `SecureDrop`
* For `Email address`, leave the field blank and press Enter
* For `Comment` type `[Your News Org] SecureDrop Application GPG Key`
* Verify that everything is correct so far, and type `o` for `(O)kay`
* It will pop up a box asking you to type a passphrase, but it's safe to click okay without typing one (since your persistent volume is encrypted, this GPG key is stored encrypted on disk)
* Wait for your GPG key to finish generating

To manage GPG keys using the Tails graphical interface, click the clipboard icon in the top right and choose "Manage Keys". You should see the key that you just generated.

![My Keys](images/install/keyring.png)

Select the key you just generated and click "File" and "Export". Save the key to the *Transfer Device* as `SecureDrop.asc`, and make sure you change the file type from "PGP keys" to "Armored PGP keys," which can be switched right above the 'export' button. This is the public key only.

![My Keys](images/install/exportkey.png)
![My Keys](images/install/exportkey2.png)

You'll need to verify the fingerprint for this new key during the `App Server` installation. Double-click on the new key you just generated and change to the `Details` tab. Write down the 40 hexadecimal digits under `Fingerprint`. (Your GPG key fingerprint will be different than what's in this photo.)

![Fingerprint](images/install/fingerprint.png)

### Import GPG keys for journalists with access to SecureDrop

While working on a story, journalists may need to transfer some of the documents or notes from the *Secure Viewing Station* to the journalist's work computer on the corporate network. To do this, the journalists should re-encrypt them with their own keys. If a journalist does not already have a personal GPG key, he or she follow the steps above to create one. The journalist should store the private key somewhere safe, the public key should be stored on the *Secure Viewing Station*.

If the journalist does have a key, transfer the public key from wherever it is located to the *Secure Viewing Station*, using the *Transfer Device*. Open the file manager and double-click on the public key to import it. If the public key is not importing, rename the file to end in ".asc" and try again.

![Importing Journalist GPG Keys](images/install/importkey.png)

At this point, you are done with the *Secure Viewing Station* for now. You can shutdown Tails, grab the *admin Tails USB* and move over to your regular workstation.

## Set up the Network Firewall

If you have not switched over and booted up to the *admin Tails USB* on your regular workstation, do so now. When starting Tails, you should see a *Welcome to Tails*-screen with two options. Select *Yes* to enable the persistent volume and enter your password. Select *Yes* to show more options and click *Forward*. Enter an *Administration password* for use with this current Tails session and click *Login*. (NOTE: the *Administration password* is a one time password. It will reset every time you shut down Tails.)

Now, go to our [Network Firewall Guide](/docs/network_firewall.md) for instructions for setting up the Network Firewall. When you are done, you will be sent back here to continue with the next section.

## Set up the Servers

You should still be on your *admin Tails USB* on your admin work station, connected to the Internet. Start by plugging the *Application Server* and the *Monitor Server* into the firewall. If you are using a setup where there is a switch on the LAN port, plug the *Application Server* into the switch and plug the *Monitor Server* into the OPT1 port.

Install Ubuntu 14.04.1 (Trusty) on both servers. For detailed information on installing and configuring Ubuntu for use with SecureDrop, see the [Ubuntu Install Guide](/docs/ubuntu_config.md). When you are done, make sure you have the following information before continuing:

* The IP address of the App Server
* The IP address of the Monitor Server
* The non-root user's name and password on each server.

Before continuing, make sure you can connect to the App and Monitor servers. You should still have the admin Workstation connected to the firewall from the firewall set up step. Open a terminal and verify that you can SSH into both servers, authenticating with your password:

```sh
ssh <username>@<App IP address> hostname
ssh <username>@<Montior IP address> hostname
```

Once you have verified that you can connect, continue with the installation. If you cannot connect, check the firewall logs.

## Install the SecureDrop application

### Download the repository and verify the release code

You should still be on the *admin Tails USB* on the admin work station. 

The rest of the SecureDrop-specific configuration is assisted by files stored in the SecureDrop git repository. To get started, open a terminal and run the following commands to download the git repository. Note that since the repository is fairly large and Tor can be slow, this may take a few minutes.

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
    git checkout 0.3
    git tag -v 0.3

You should see 'Good signature from "Freedom of the Press Foundation Master Signing Key"' in the output of `git tag`. If you do not, signature verification has failed and you *should not* proceed with the installation. If this happens, please contact us at securedrop@freedom.press.

### Install Ansible

Next you need to install Ansible. To do this, you first need to update your package manager's package lists to be sure you get the latest version of Ansible. It should take a couple minutes.

    sudo apt-get update

Now, install Ansible by entering this command:

    sudo apt-get install ansible

### Set up SSH keys for the Admin

Now that you've verified the code that's needed for installation, you need to create an SSH key on the Admin Workstation. Initially, Ubuntu has SSH configured to authenticate users with their password. This new key will be copied to the *Application Server* and the *Monitor Server*, and will replace the use of the password for authentication. Since the Admin Live USB was set up with [SSH Client persistence](https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html#index3h2), this key will be saved on the Admin Live USB and can be used in the future to authenticate to the servers in order to perform administrative tasks.

First, generate the new SSH keypair:

    $ ssh-keygen -t rsa -b 4096

You'll be asked to "enter file in which to save the key." Here you can just keep the default, so type enter. Choose a strong passphrase to protect the SSH private key. 

Once the key has finished generating, you need to copy the public key to both servers. Use `ssh-copy-id` to copy the public key to each server in turn. Use the user name and password that you set up during Ubuntu installation.

    $ ssh-copy-id <username>@<App IP address>
    $ ssh-copy-id <username>@<Mon IP address>

Verify that you are able to authenticate to both servers without being prompted for a password by running the below commands. 

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
* Connection information for the SMTP relay that handles OSSEC alerts. For more information, see the [OSSEC Alerts Guide](ossec_alerts.md).
* The first name a journalist who will be using SecureDrop (you can add more later)
* The username of the system administrator
* (Optional) An image to replace the SecureDrop logo on the *Source Interface* and *Document Interface*
    * Recommended size: `500px x 450px`
    * Recommended format: PNG

### Install SecureDrop

Change into the `ansible-base` directory of the SecureDrop repo that you cloned earlier:

    $ cd securedrop/install_files/ansible-base

Copy the following required files to `securedrop/install_files/ansible-base`:

* SecureDrop Application GPG public key file
* Admin GPG public key file (for encrypting OSSEC alerts)
* (Optional) Custom header image file

The SecureDrop application GPG key should be located on your *Transfer Device* from earlier. It will depend what the file location of your USB stick is, but, for an example, if you are already in the ansible-base directory, you can just run: 

    $ cp /media/[USB folder]/SecureDrop.asc .

Repeat the same step for the Admin GPG key and custom header image.

Edit the inventory file, `inventory`, and update the default IP addresses with the ones you chose for app and mon. When you're done, save the file and exit the editor.

Fill out `prod-specific.yml` with values that match your environment. At a minimum, you will need to provide the following:

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
 * Email settings required to send alerts from OSSEC: `smtp_relay`
 * Email settings required to send alerts from OSSEC: `smtp_relay_port`
 * Email settings required to send alerts from OSSEC: `sasl_username`
 * Email settings required to send alerts from OSSEC: `sasl_domain`
 * Email settings required to send alerts from OSSEC: `sasl_password`
 * The fingerprint of your SMTP relay (optional): `smtp_relay_fingerprint`

When you're done, save the file and exit the editor. 

Now you are ready to run the playbook! This will automatically configure the servers and install SecureDrop and all of its dependencies. `<username>` is the user you created during the Ubuntu installation, and should be the same user you copied the SSH public keys to.

    $ ansible-playbook -i inventory -u <username> -K --sudo site.yml

You will be prompted to enter the sudo password for each server.

The ansible playbook will run, installing SecureDrop and configuring and hardening the servers. This will take some time, and will return the Terminal to you when it is complete. If an error occurs while running the playbook, please submit a detailed [Github issue](https://github.com/freedomofpress/securedrop/issues/new) or send an email to securedrop@freedom.press.

Once the installation is complete, the addresses for each Tor Hidden Service will be available in the following files in `install_files/ansible-base`:

* `app-source-ths`: This is the .onion address of the Source Interface
* `app-document-aths`: This is the `HidServAuth` configuration line for the Document Interface. You need to add this line to your torrc and restart Tor in order to connect to the hidden service address included in the line.
* `app-ssh-aths`: Same as above, for SSH access to the Application Server.
* `mon-ssh-aths`: Same as above, for SSH access to the Monitor Server.

Update the inventory, replacing the IP addresses with the corresponding onion addresses from `app-ssh-aths` and `mon-ssh-aths`. This will allow you to re-run the Ansible playbooks in the future, even though part of SecureDrop's hardening restricts SSH to only being over the specific authenticated Tor Hidden Services.

### Set up two-factor authentication for the Admin

As part of the SecureDrop installation process, you will need to set up two factor authentication on the App Server using the Google Authenticator mobile app.

Connect to the App Server's hidden service address using `ssh` and run `google-authenticator`. Follow the instructions in [our Google Authenticator guide](/docs/google_authenticator.md) to set up the app on your Android or iOS device.

## Testing the Installation

Some of the final configuration is included in these testing steps, so *do not skip them!*

### Test the web application and connectivity

On your Admin Workstation running Tails:

1. Configure your torrc with the values in app-document-aths, app-ssh-aths, and mon-ssh-aths, and reload the Tor service.
 * The values listed after the .onion addresses allow access to the authenticated Tor hidden services for the App Server, Mon Server, and Admin/Document Interface. Only clients who have them configured using the HidServAuth directive in their Tor configuration can access these through Tor.
 * We have a setup script for Tails that helps you add the values and creates a launcher on the desktop to open the Admin/Document Interface. The launcher automatically reloads Tor.
 * See the 'Download and run the setup scripts' section of [Tails for the Admin and Journalist Workstation](/tails_files/README.md) and follow the instructions.
2. SSH to both servers over Tor
 * As an admin running Tails with the proper HidServAuth values in your `/etc/torrc` file, you should be able to SSH directly to the App Server and Monitor Server.
 * Post-install you can now SSH _only_ over Tor, so use the onion URLs from app-ssh-aths and mon-ssh-aths and the user created during the Ubuntu installation i.e. `ssh admin@m5apx3p7eazqj3fp.onion`.
3. Make sure the Source Interface is available, and that you can make a submission.
 * Do this by opening the Tor Browser and navigating to the onion URL from app-source-ths. Proceed through the codename generation (copy this down somewhere) and you can submit a message or attach any random unimportant file.
 * Usage of the Source Interface is covered by our [Source User Manual](/docs/source_user_manual.md).
4. SSH to the App Server, `sudo su`, cd to /var/www/securedrop, and run `./manage.py add_admin` to create the first admin user for yourself. Use a strong password that you can remember. This user is only relevant to the web application.
5. Test that you can access the Document Interface, and that you can log in as the admin user you just created.
 * Open the Tor Browser and navigate to the onion URL from app-document-aths. Enter your password and two-factor authentication code to log in.
 * If you have problems logging in to the Admin/Document Interface, SSH to the App Server and restart the ntp daemon to synchronize the time: `sudo service ntp restart`. Also check that your smartphone's time is accurate and set to network time in its device settings.
6. Test replying to the test submission.
 * While logged in as an admin, you can send a reply to the test source submission you made earlier.
 * Usage of the Document Interface is covered by our [Journalist User Manual](/docs/journalist_user_manual.md).
7. Test that the source received the reply.
 * Within Tor Browser, navigate back to the app-source-ths URL and use your previous test source codename to log in (or reload the page if it's still open) and check that the reply you just made is present.
8. Remove the test submissions you made prior to putting SecureDrop to real use. On the main Document Interface page, select all sources and click 'Delete selected'.

Once you've tested the installation and verified that everything is working, see [How to Use SecureDrop](/docs/journalist_user_manual.md).

### Additional testing

1. On each server, check that you can execute privileged commands by running `sudo su`.
2. Run `uname -r` to verify you are booted into Grsecurity kernel. The string `grsec` should be in the output.
3. Check the AppArmor status on each server with `sudo aa-status`. On a production instance all profiles should be in enforce mode.
4. Check the current applied iptables rules with `iptables-save`. It should output approximately 50 lines.
5. You should have received an email alert from OSSEC when it first started.

