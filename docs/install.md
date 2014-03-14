SecureDrop Installation Guide
=============================

These instructions are intended for admins setting up SecureDrop for a journalist organization.

## Before you begin

Before installing SecureDrop, you should make sure you have everything you need.

* You must have two servers — called the `App Server` and the `Monitor Server`, with [Ubuntu Server installed](/docs/ubuntu_config.md).

* You must have two USB sticks with [Tails installed on them](/docs/tails_config.md) and persistent storage enabled. One will be air-gapped, the other will be used to connect to the internet. Make sure to label them.

* You need an extra USB stick for transferring files.

* You must have a device capable of running the Google Authenticator app, such an Android or iOS device. Google Authenticator is an app for producing one-time passwords for two-factor authentication. You can find download instructions [here](https://support.google.com/accounts/answer/1066447?hl=en).

* Finally, you should have selected two secure passphrases: one for the persistent volume on the internet-connected Tails, and one for the persistent volume on the air-gapped Tails. If your organization doesn't yet have a good password policy, [you really should have one](http://howto.wired.com/wiki/Choose_a_Strong_Password).

In addition to the requirements above, each journalist will also their own device capable of running Google Authenticator, a USB stick for transferring files between the `Secure Viewing Station` and their `Journalist Workstation`, and a personal GPG key. See [this section](/docs/install.md#set-up-journalist-gpg-keys) for instructions to set one up for journalists who don't have already have a key. 

We also suggest that you have an external hard drive for backing up encrypted submitted documents and some form of removable media for backing up the application's GPG keyring.

## Secure Viewing Station

The `Secure Viewing Station` will be air-gapped (never connected to the Internet) and will always boot from your air-gapped Tails USB stick. Because of this, you don't need a hard drive or network devices. You may want to consider physically opening this computer and removing the hard drive and wifi card, but doing this is outside the scope of this manual.

### Generate GPG Key and Import Journalist Public Keys

In order to avoid transferring plaintext files between the `Secure Viewing Station` and `Journalist Workstations`, each journalist should have their [own personal GPG key](/docs/install.md#set-up-journalist-gpg-keys). Start by copying all of the journalists' public keys to a USB stick. Plug this into the `Secure Viewing Station` running Tails and open the file manager. Double-click on each public key to import it. If the public key isn't importing, try renaming it to end in ".asc".

![Importing Journalist GPG Keys](/docs/images/install/viewing1.jpg)

To generate the application GPG key:

* Open a terminal and run `gpg --gen-key`
* When it says, `Please select what kind of key you want`, choose `(1) RSA and RSA (default)`
* When it asks, `What keysize do you want?` type `4096`
* When it asks, `Key is valid for?` press enter to keep the default
* When it asks, `Is this correct?` verify that you've entered everything correctly so far, and type `y`
* For `Real name` type: `SecureDrop`
* For `Email address`, leave the field blank and press enter
* For `Comment` type `SecureDrop Application GPG Key`
* Verify that everything is correct so far, and type `o` for `(O)kay`
* It will pop up a box asking you to type a passphrase, but it's safe to click okay with typing one (since your persistent volume is encrypted, this GPG key is stored encrypted on disk)
* Wait for your GPG key to finish generating

To manage GPG keys using the Tails graphical interface, click the clipboard icon in the top right and choose "Manage Keys". If you switch to the "My Personal Keys" tab you can see the key that you just generated.

![My Keys](/docs/images/install/viewing7.jpg)

Right-click on the key you just generated and click `Export`. Save it to your USB stick as `SecureDrop.asc`. This is the public key only.

![My Keys](/docs/images/install/viewing8.jpg)

You'll also need to verify the 40 character hex fingerprint for this new key during the `App Server` installation. Double-click on the new key you just generated and change to the `Details` tab. Write down the 40 digits under `Fingerprint`. (Your GPG key fingerprint will be different than what's in this photo.)

![Fingerprint](/docs/images/install/viewing9.jpg)

## Server Installation

All packages require that Tor's repo was already added to the system. The `securedrop/install_files/scripts/add_repo.sh` will do this. 

### Creating the securedrop deb packages:
For development and testing you can create the deb packages by running `securedrop/build_deb_packages.sh` in the base of the securedrop repo.
This will create 4 packages

####securedrop-monitor
* Location: `securedrop/monitor-VERSION.deb`
* This package hardens the host system and install the OSSEC manager binary.
Min Required Info: App server's IP address, destination email address, smtp relay, admin username 

####securedrop-app
* Location: `securedrop/app-VERSION.deb`
* This package hardens the host system and configures 2 chroot jails that the interfaces will be installed in
Min Reuqired Info: Monitor Server's IP address, application's gpg key, 1 journalist name, 1 admin username 

####securedrop-source
* Location: `securedrop/source-VERSION.deb`
* This package installs the source interface. This package shares the `securedrop/store`, `securedrop/keys`, and `securedrop/db` directories with the document interface.

####securedrop-document
* Location: `securedrop/document-VERSION.deb`
* This package installs the source interface web application This package shares the `securedrop/store`, `securedrop/keys`, and `securedrop/db` directories with the source interface.

### Installing locally create deb packages
If you are using the included Vagrantfile for managing vm's there is an included `vagrant-app-preinstall.sh` and `vagrant-monitor-preinstall.sh` scripts that will preseed the debconf questions for a development environment.

#### Development App Server using the included `Vagrantfile`
* Clone the SecureDrop repo `git clone https://github.com/freedomofpress/securedrop.git` 
* Change directory into the base of the securedrop repo `cd securedrop/`
* Run `./build_deb_packages.sh` to create the deb packages.
* Run `vagrant precise-app-gdebi up` to start the App Server virtual machine.
* Run `vagrant ssh precise-app-gdebi` to SSH to the app server. The vagrant provisioner generates an error using the gdebi command.
* Run `sudo /vagrant/install_files/scripts/vagrant-app-preinstall.sh`. This will add the tor repo, install gdebi, and install the securedrop-app package using the included preseed question based on the Vagrantfile.
* Run `sudo /opt/securedrop/scripts/display_tor_urls.sh`

#### Development Monitor Server using the inlcuded `Vagrantfile`
* Clone the SecureDrop repo `git clone https://github.com/freedomofpress/securedrop.git`
* Change directory into the base of the securedrop repo `cd securedrop/`
* Run `./build_deb_packages.sh` to create the deb packages.
* Run `vagrant precise-monitor-gdebi up` to start the App Server virtual machine.
* Run `vagrant ssh precise-monitor-gdebi` to SSH to the app server. The vagrant provisioner generates an error using the gdebi command.
* Run `sudo /vagrant/install_files/scripts/vagrant-monitor-preinstall.sh`. This will add the tor repo, install gdebi and install the securedrop-monitor package using the included preseed questions based on the Vagrantfile.
* Run `sudo /opt/securedrop/scripts/display_tor_urls.sh`

#### Production App Server
```
wget URL_TO_SCRIPT_TO_INSTALL_TOR_REPO
sudo ./add-repo.sh
sudo apt-get install securedrop-app
sudo /opt/securedrop/scripts/display_tor_urls.sh
```

#### Production Monitor Server
```
wget URL_TO_SCRIPT_TO_INSTALL_TOR_REPO
sudo ./add-repo.sh
sudo apt-get install securedrop-app
sudo /opt/securedrop/scripts/display_tor_urls.sh
```

#### Add OSSEC agent
On both servers run `/var/ossec/bin/manage-agents`
TODO add screenshots of process on both servers
Restart the ossec agent on the App Server `/var/ossec/bin/ossec-control restart`
Wait a few seconds for the agent to connect then
Restart the ossec agent on the Monitor Server `/var/ossec/bin/ossec-control restart`
To verify agent connected `/var/ossec/bin/list_agents -c`

## Journalist's Workstation Setup

The journalist workstation computer is the laptop that the journalist uses on a daily basis. It can be running Windows, Mac OS X, or GNU/Linux. This computer must have GPG installed.

### Set up journalist GPG keys

Each journalist must have a personal GPG key that they use for encrypting files transferred from the `Secure Viewing Station` to their `Journalist Workstation`. The private key, used for decryption, stays on their `Journalist Workstation`. The public key, used for encryption, gets copied to the `Secure Viewing Station`.

If a journalist does not yet have a GPG key, they can follow these instructions to set one up with GnuPG (GPG).

* [GNU/Linux](http://www.gnupg.org/gph/en/manual.html#AEN26)
* [Windows](http://gpg4win.org/)
* [Mac OS X](http://support.gpgtools.org/kb/how-to/first-steps-where-do-i-start-where-do-i-begin)

### Journalist Logging In

In order to view the `Document Interface`, journalists needs to either 1) install the Tor Browser Bundle and modify it to authenticate their hidden service, or 2) modify Tor through their Tails operating system to accomplish the same task. The latter is highly recommended since many news organzation's corporate computer systems have been compromised in the past.

**Through the Tails Operating System**

Each journalist that will be using Tails to connect to the `Document Interface` will need to install a persistent script onto their Tails USB stick. Follow [these instructions](/tails_files/README.md) to continue.

In order to follow those instructions you'll need the HidServAuth string that you had previously created (a different one for each journalist's Tails USB stick), which looks something like this:

    HidServAuth b6ferdazsj2v6agu.onion AHgaX9YrO/zanQmSJnILvB # client: journalist1

Once you have installed this script, the journalist will have to run it each time they boot Tails and connect to the Tor network in order to login to the `Journalist Interface`.

**Through the Tor Browser Bundle**

* On the `Journalist Workstation`, [download and install the Tor Browser Bundle](https://www.torproject.org/download/download-easy.html.en). Extract Tor Browser Bundle to somewhere you will find it, such as your desktop.

* Navigate to the Tor Browser Directory
* Open the `torrc-defaults` file which should be located in `tor-browser_en-US/Data/Tor/torrc-defaults`
* Add a line that begins with `HidServAuth` followed by the journalist's Document Interface URL and Auth value that was output at the end of the App Server installation

In this case the `torrc-defaults` file for the first journalist should look something like:

    # If non-zero, try to write to disk less frequently than we would otherwise.
    AvoidDiskWrites 1
    # Where to send logging messages.  Format is minSeverity[-maxSeverity]
    # (stderr|stdout|syslog|file FILENAME).
    Log notice stdout
    # Bind to this address to listen to connections from SOCKS-speaking
    # applications.
    SocksListenAddress 127.0.0.1
    SocksPort 9150
    ControlPort 9151
    CookieAuthentication 1
    HidServAuth b6ferdazsj2v6agu.onion AHgaX9YrO/zanQmSJnILvB # client: journalist1

And the `torrc-defaults` file for the second journalist should look like something this:

    # If non-zero, try to write to disk less frequently than we would otherwise.
    AvoidDiskWrites 1
    # Where to send logging messages.  Format is minSeverity[-maxSeverity]
    # (stderr|stdout|syslog|file FILENAME).
    Log notice stdout
    # Bind to this address to listen to connections from SOCKS-speaking
    # applications.
    SocksListenAddress 127.0.0.1
    SocksPort 9150
    ControlPort 9151
    CookieAuthentication 1
    HidServAuth kx7bdewk4x4wait2.onion qpTMeWZSTdld7gWrB72RtR # client: journalist2

* Open the Tor Browser Bundle and navigate to the journalist's unique Document Interface URL without the Auth value

![Journalist_workstation1](/docs/images/install/journalist_workstation1.png)

## Test It

Once it's installed, test it out. See [How to Use SecureDrop](/docs/user_manual.md).
