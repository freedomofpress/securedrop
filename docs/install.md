Installing SecureDrop
=====================

This guide outlines the steps required to install [SecureDrop 0.3](https://pressfreedomfoundation.org/securedrop).

When running commands or editing configuration files that include filenames, version numbers, admin or journalist names, make sure it all matches your setup.

## Terminology

A number of terms used in this guide, and in the [SecureDrop workflow diagram](https://pressfreedomfoundation.org/securedrop-files/SecureDrop_complex.png), are specific to SecureDrop. The list below attempts to enumerate and define these terms.

### App Server

The *Application Server* (or *App Server* for short) runs the SecureDrop application. This server hosts both the website that sources access (*Source Interface*) and the website that journalists access (*Document Interface*). You may only connect to this server using Tor.

### Monitor Server

The *Monitor Server* keeps track of the *App Server* and sends out an email alert if something seems wrong. You may only connect to this server using Tor.

### Source Interface

The *Source Interface* is the website that sources will access when submitting documents and communicating with journalists. This site is hosted on the *App Server* and can only be accessed over Tor.

### Document Interface

The *Document Interface* is the website that journalists will access when downloading new documents and communicating with sources. This site is hosted on the *App Server* and can only be accessed over Tor.

### Journalist Workstation

The *Journalist Workstation* is a machine that is online and used together with the Tails operating system on the *online* USB stick. This machine will be used to connect to the *Document Interface*, download documents, and move them to the *Secure Viewing Station* using the *Transfer Device*

### Admin Workstation

The *Admin Workstation* is a machine that the system administrator can use to connect to the *App Server* and the *Monitor Server* using Tor and SSH. The administrator will also need to have an Android or iOS device with the Google Authenticator app installed.

### Secure Viewing Station

The *Secure Viewing Station* is a machine that is kept offline and only ever used together with the Tails operating system on the *offline* USB stick. This machine will be used to generate GPG keys for all journalists with access to SecureDrop, as well as decrypt and view submitted documents.

Since this machine will never touch the Internet or run an operating system other than Tails on a USB, it does not need a hard drive or network device. You may want to consider physically removing the drive and the wireless card from this machine.

### Transfer Device

The *Transfer Device* is the physical media used to transfer encrypted documents from the *Journalist Workstation* to the *Secure Viewing Station*. Examples: a dedicated small sized usb stick, CD-R or SD card.

## Before you begin

The steps in this guide assume you have the following set up:

 * Two servers - called *App* and *Monitor* - with [Ubuntu Server
 * 14.04.1 LTS (Trusty Tahr)](http://www.ubuntu.com/download/server) installed. For a more detailed guide on setting up Ubuntu for SecureDrop, see the [Ubuntu Guide](docs/ubuntu_config.md).
 * An [Ubuntu kernel with Grsecurity](https://github.com/dolanjs/ubuntu-grsec) ready to be installed on the *App* and *Monitor* servers
 * Two USB sticks with [Tails](https://tails.boum.org/download/index.en.html) and [persistent volumes](https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html), mark one *offline* and the other *online*
 * A secure and unique passphrase for the persistent volume on each of the two USB sticks
 * One *Transfer Device* for transferring files, marked *transfer*
 * An Android or iOS device with the [Google Authenticator](https://support.google.com/accounts/answer/1066447?hl=en) app installed *or* a [Yubikey](http://www.yubico.com/products/yubikey-hardware/) One-Time Password authentication dongle
 
Each journalist will also have their own Android or iOS device capable of running [Google Authenticator](https://support.google.com/accounts/answer/1066447?hl=en) *or* a [Yubikey](http://www.yubico.com/products/yubikey-hardware/) dongle, a *Transfer Device* for transferring files between the *Secure Viewing Station* and their *Journalist Workstation*, and a personal GPG key. Make sure you [create a GPG key](/docs/install.md#set-up-journalist-gpg-keys) for journalists who do not already have one. 

It is also recommended that you use an external hard drive to back up encrypted submissions and some form of removable media to back up the GPG keyring on the *App* server.

## Set up the Secure Viewing Station

The *Secure Viewing Station* is a machine that is kept offline and only ever used together with the Tails operating system on the *offline* USB stick. Since this machine will never touch the Internet or run an operating system other than Tails on a USB, it does not need a hard drive or network device. We recommend that you physically remove the hard drive and networking cards, such as wireless and bluetooth, from this machine. If you are unable to remove a card, tape over it or otherwise physically disable it. If you have questions about using an old machine for this purpose, please contact us at securedrop@freedom.press.

### Create a GPG key for the SecureDrop application

When a document is submitted through the *Source Interface* on the *App Server*, the document is immediately encrypted with the SecureDrop application's GPG key. If you have not previously created a GPG key for SecureDrop, follow the steps below to do so now:

 * Open a terminal and run `gpg --gen-key`
 * When it says, `Please select what kind of key you want`, choose `(1) RSA and RSA (default)`
 * When it asks, `What keysize do you want?` type `4096`
 * When it asks, `Key is valid for?` press Enter to keep the default
 * When it asks, `Is this correct?` verify that you've entered everything correctly so far, and type `y`
 * For `Real name` type: `SecureDrop`
* For `Email address`, leave the field blank and press Enter
* For `Comment` type `SecureDrop Application GPG Key`
* Verify that everything is correct so far, and type `o` for `(O)kay`
* It will pop up a box asking you to type a passphrase, but it's safe to click okay without typing one (since your persistent volume is encrypted, this GPG key is stored encrypted on disk)
* Wait for your GPG key to finish generating

To manage GPG keys using the Tails graphical interface, click the clipboard icon in the top right and choose "Manage Keys". You should then see the key that you just generated.

![My Keys](/docs/images/install/keyring.png)

Select the key you just generated and click "File" and "Export". Save the key to the *Transfer Device* as `SecureDrop.asc`, and make sure you change the file type from "PGP keys" to "Armored PGP keys". This is the public key only.

![My Keys](/docs/images/install/exportkey.png)
![My Keys](/docs/images/install/exportkey2.png)

You'll also need to verify the 40 character hexadecimal fingerprint for this new key during the `App Server` installation. Double-click on the new key you just generated and change to the `Details` tab. Write down the 40 digits under `Fingerprint`. (Your GPG key fingerprint will be different than what's in this photo.)

![Fingerprint](/docs/images/install/fingerprint.png)

### Import GPG keys for journalists with access to SecureDrop

While working on a story, journalists may need to transfer some of the documents or notes from the *Secure Viewing Station* to the journalist's work computer on the corporate network. To do this, the journalists need to decrypt the documents using the SecureDrop application's GPG key and re-encrypt them with their own keys. If a journalist does not already have a key, follow the steps above to create one. 

If the journalist does have a key, transfer the public key to the *Secure Viewing Station* using the *Transfer Device*. Open the file manager and double-click on the public key to import it. If the public key is not importing, rename the file to end in ".asc" and try again.

![Importing Journalist GPG Keys](/docs/images/install/importkey.png)

## Set up the App Server

The *App Server* should already have Ubuntu Server 14.04.1 LTS (Trusty Tahr) installed. Before you begin, be sure to have the following information available:

 * The IP address of the *Monitor Server*
 * The SecureDrop application's GPG public key (from the *Transfer Device*)
 * The SecureDrop application's GPG key fingerprint
 * An image to replace the SecureDrop logo on the *Source Interface* and *Document Interface*
 * The first name a journalist who will be using SecureDrop (you can add more later)
 * The username of the system administrator (must have an existing OS account, is most likely the account you are using for the install)

### Add our Debian repository on the App Server

To install SecureDrop on the *App Server*, you will first need to add the Freedom of the Press Foundation's Debian repository. We created a script that will add the signing keys and Debian package repositories for the Tor Project and Freedom of the Press Foundation, and update the package lists from the repositories.

Download the archive with the script, as well as the digital signature.

```
wget https://pressfreedomfoundation.org/securedrop-files/add-repos.tgz
wget https://pressfreedomfoundation.org/securedrop-files/add-repos.tgz.sig
```

Download the SecureDrop signing key and verify the digital signature

```
gpg --keyserver pool.sks-keyservers.net --recv-key 9092EDF6244A1603DCFDC4629A2BE67FBD67D096
gpg --verify add-repos.tgz.sig
```

If the signature is OK, extract the archive with the script, set the execuble flag and run it.

```
tar -xzf add-repos.tgz
chmod +x ./add-repos.sh
sudo ./add-repos.sh
```

### Install SecureDrop on the App Server

When you are ready to install SecureDrop on the App Server, run the command below.

```
sudo apt-get install securedrop-app
```

The installation process will download and install package dependencies and ask you for a few bits of information.

### Set up Google Authenticator for the App Server

As part of the SecureDrop installation process, you will need to set up two factor authentication using the Google Authenticator app.

On the *App Server*, open the *~/.google_authenticator* file and note the value listed on the very first line. Open the Google Authenticator app on your smartphone and follow the steps below for either iOS or Android.

**iOS instructions:**

* Select the pencil in the top-right corner
* Select the plus sign at the bottom to add a new entry
* Select *Manual Entry*
* Under *Account* enter *SecureDrop App*
* Under *Key* enter the value from the *.google_authenticator* file
* Select the option in the top-right corner to save

**Android instructions:**

* Select the menu bar in the top-right corner
* Select *Set up account*
* Select *Enter provided key* under 'Manually add an account'
* Under *Enter account name* enter *SecureDrop App*
* Under *Enter your key* enter the value from the *.google_authenticator* file
* You may leave the default type which is 'Time based'
* Select the *Add* button at the bottom to save

### Finalize the installation on the App Server

To finalize the installation on the *App Server* and also learn the address of the *Source Interface* and the *Document Interface*, as well as the new hostname for the *App Server*, run the command below. Note that the command will ask for your two factor verification code and password.

```
sudo /opt/securedrop/post-install.sh
```

Below is an example output from the post-install script. You will need to record the URL for the *Source Interface*, the *Document Interface*, authentication values for each journalist, Tor configuration file values, and the SSH address for the *App Server*. These values will all be marked in red when you run the script.

The output below assumes that an admin named *Alice* and a journalist named *Bob* are installing SecureDrop.

```
The Source Interface's URL is:
http://ajntehqxzvxubi5h.onion
The Document Interface listens on port 8080
you will need to append :8080 to the URL as shown below
The Document Interface's URL and auth values for each journalist:
bob's URL is http://gu6yn2ml6ns5qupv.onion:8080
bob's TBB torrc config line is:
HidServAuth gu6yn2ml6ns5qupv.onion Us3xMTN85VIj5NOnkNWzW # client: bob
To add more journalists run 'sudo /opt/securedrop/add-journalists.sh NAME' script

The App Server is only accessible through a Tor Authenticated Hidden Service
you will need to use connect-proxy, torify or something similar to proxy SSH through Tor
alice's SSH address is ssh alice@jphhcishih46uvlg.onion
alice's system torrc config line is:
HidServAuth jphhcishih46uvlg.onion WgeZ1VkluV3K//AoEAjewF # client: alice
alice's Google Authenticator secret key is RFULAWMCPKZUHJKB
You will need to run the 'sudo /opt/securedrop/add-admin.sh USERNAME'
to add more admins.
```

## Set up the Monitor Server

The *Monitor Server* should already have Ubuntu Server 14.04.1 LTS (Trusty Tahr) installed. Before you begin, be sure to have the following information available:

 * The IP address of the *App Server*
 * The email address that will receive alerts from OSSEC
 * The GPG public key and fingerprint for the email address that will receive the alerts
 * The username of the system administrator (must have an existing OS account, is most likely the account you are using for the install)
 
### Create GPG key for the address that will receive alerts

The intrustion detection system on the *Monitor Server* will be configured to send out email alerts when the *App Server* is down or when something else is wrong. The steps below will help you create a GPG key so that the server can encrypt the emails it sends you. The GPG key needs to be associated with the same email address as the one that will be configured to receive the alerts. If you already have such a key, you may skip this step.
 
### Add our Debian repository on the Monitor Server

To install SecureDrop on the *Monitor Server*, you will first need to add the Freedom of the Press Foundation's Debian repository. We created a script that will add the signing keys and Debian package repositories for the Tor Project and Freedom of the Press Foundation, and update the package lists from the repositories.

Download the archive with the script, as well as the digital signature.

```
wget https://pressfreedomfoundation.org/securedrop-files/add-repos.tgz
wget https://pressfreedomfoundation.org/securedrop-files/add-repos.tgz.sig
```

Download the SecureDrop signing key and verify the digital signature

```
gpg --keyserver pool.sks-keyservers.net --recv-key 9092EDF6244A1603DCFDC4629A2BE67FBD67D096
gpg --verify add-repos.tgz.sig
```

If the signature is OK, extract the archive with the script, set the execuble flag and run it.

```
tar -xzf add-repos.tgz
chmod +x ./add-repos.sh
sudo ./add-repos.sh
```

### Install SecureDrop on the Monitor Server

When you are ready to install SecureDrop on the *Monitor Server*, run the command below.

```
sudo apt-get install securedrop-monitor
```

The installation process will download and install package dependencies and ask you for a few bits of information.

### Set up Google Authenticator for the Monitor Server

As part of the SecureDrop installation process, you will need to set up two factor authentication using the Google Authenticator app.

On the *Monitor Server*, open the *~/.google_authenticator* file and note the value listed on the very first line. Open the Google Authenticator app on your smartphone and follow the steps below for either iOS or Android.

**iOS instructions:**

* Select the pencil in the top-right corner
* Select the plus sign at the bottom to add a new entry
* Select *Manual Entry*
* Under *Account* enter *SecureDrop Monitor*
* Under *Key* enter the value from the *.google_authenticator* file
* Select the option in the top-right corner to save

**Android instructions:**

* Select the menu bar in the top-right corner
* Select *Set up account*
* Select *Enter provided key* under 'Manually add an account'
* Under *Enter account name* enter *SecureDrop Monitor*
* Under *Enter your key* enter the value from the *.google_authenticator* file
* You may leave the default type which is 'Time based'
* Select the *Add* button at the bottom to save

### Finalize the installation on the Monitor Server

To finalize the installation on the *Monitor Server* and also learn the new hostname for the *Monitor Server*, run the command below. Note that the command will ask for your two factor verification code and password.

```
sudo /opt/securedrop/post-install.sh
```

Below is an example output from the post-install script. You will need to record the Tor configuration file value, and the SSH address for the *Monitor Server*. These values will all be marked in red when you run the script.

The output below assumes that an admin named *Alice* and a journalist named *Bob* are installing SecureDrop.

```
The Monitor Server is only accessible through a Tor Authenticated Hidden Service
you will need to use connect-proxy, torify or something similar to proxy SSH through Tor
alice's SSH address is ssh alice@r73jkrg6w63kq5k4.onion
alice's system torrc config line is:
HidServAuth r73jkrg6w63kq5k4.onion 18xjlI1DwghSSAI2y6sMBB # client: alice
alice's Google Authenticator secret key is GIWTJDPOAWGTSGNB
You will need to run the 'sudo /opt/securedrop/add-admin.sh USERNAME'
to add more admins.
```

### Add OSSEC agent

An OSSEC agent is a small program set up on the system you want to monitor, which in this case means the *App Server*. The agent will collect information in real time and forward it to the manager on the *Monitor Server* for analysis and correlation. Adding the OSSEC agent involves accessing both the *App server* and the *Monitor Server*. In order to make copying pasting the long secret value from the *Monitor Server* to the *App server* you will want to ssh into both servers instead of running the commands from the console.

#### Generate an agent key on the Monitor Server

![Generate agent key](/docs/images/install/monitor-manage-agents.png)

#### Add agent key to App Server

Copy the long secret value from the *Monitor Server* and prepare to paste it into the *App Server*
![Add agent key](/docs/images/install/app-manage-agents.png)

Restart the `App Servers` OSSEC agent by running `service ossec restart`

#### Verify OSSEC agent connectivity

Restart the `Monitor Servers` OSSEC service by running `service ossec restart`

![Verify OSSEC agent](/docs/images/install/monitor-verify-agent.png)

### Configure Postfix
Postfix is used to route the OSSEC alerts to the organizations smtp server. While the bodies of the emails will be encrypted, you should still configure a high secure SMTP relay connection using TLS, Certificate Pinning and SASL authentication. An example for using smtp.gmail.com as the SMTP relay is provided below. If you use smtp.gmail.com you should create a dedicated account to be used for SASL authentication, using an application specific password for SASL authentication no longer works for google. NOTE: google business accounts use a different FQDN than @google.com addresses.

The SMTP TLS certificate's fingerprint was retrieved using this command:
```
openssl s_client -connect smtp.gmail.com:587 -starttls smtp  < /dev/null 2>/dev/null | openssl x509 -fingerprint -noout -in /dev/stdin | cut -d'=' -f2
```

#### Contents of `/etc/postfix/main.cf`
```
# See /usr/share/postfix/main.cf.dist for a commented, more complete version
relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_use_tls=yes
smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache
smtp_tls_CAfile = /etc/postfix/cacert.pem
smtp_tls_security_level = fingerprint
smtp_tls_fingerprint_digest = sha1
smtp_tls_fingerprint_cert_match = 9C:0A:CC:93:1D:E7:51:37:90:61:6B:A1:18:28:67:95:54:C5:69:A8
smtp_tls_ciphers = high
smtp_tls_protocols = TLSv1.2 TLSv1.1 TLSv1 !SSLv3 !SSLv2
myhostname = monitor.securedrop
# Used to setup emailing alerts with gpg
mailbox_command = /usr/bin/procmail
# Disables inbound smtp
inet_interfaces = loopback-only

myorigin = $myhostname
smtpd_banner = $myhostname ESMTP $mail_name (Ubuntu)
biff = no
append_dot_mydomain = no
readme_directory = no
## Steps for setting up the sasl password file https://rtcamp.com/tutorials/linux/ubuntu-postfix-gmail-smtp/
alias_maps = hash:/etc/aliases
alias_database = hash:/etc/aliases
mydestination = $myhostname, localhost.localdomain , localhost
mynetworks = 127.0.0.0/8 [::ffff:127.0.0.0]/104 [::1]/128
mailbox_size_limit = 0
recipient_delimiter = +
```

#### Contents of `/etc/postfix/sasl_passwd`
```
[smtp.gmail.com]:587    USERNAME@DOMAIN:PASSWORD
```

Change `USERNAME` `DOMAIN` and `PASSWORD` to the correct values.

#### Apply settings and restart Postfix
```
sudo chmod 400 /etc/postfix/sasl_passwd
sudo postmap /etc/postfix/sasl_passwd
cat /etc/ssl/certs/Thawte_Premium_Server_CA.pem | sudo tee -a /etc/postfix/cacert.pem
sudo /etc/init.d/postfix reload
```

Once you have completed these steps, the SecureDrop web application should be set up.

## Set up the Admin Workstation

The *Admin Workstation* is a machine that the system administrator can use to connect to the *App Server* and the *Monitor Server* using Tor and SSH. The administrator will also need to have an Android or iOS device with the Google Authenticator app installed.

### Configure SSH to use Tor

When installing SecureDrop on the *App Server* and the *Monitor Server*, SSH will be configured to only allow connections over Tor. The steps below assume that the *Admin Workstation* is running Linux and has *Tor* installed from [Tor Project's repos](https://www.torproject.org/docs/installguide.html.en) Do not use the version that is in the Linux distribution's repos because it is most likely out of date.

Install the *connect-proxy* tool.

```
sudo apt-get install connect-proxy
```

Edit *~/.ssh/config* with the username of the system administrator and the hostnames for the *App Server* and the *Monitor Server*. You can get the hostnames by running the post-install script at */opt/securedrop/post-install.sh* **after** installing SecureDrop.

The names and addresses below are the same as in the example output from the post-install script.

```
Host securedrop-app
HostName jphhcishih46uvlg.onion
User alice
CheckHostIP no
Compression yes
Protocol 2
ProxyCommand connect-proxy -4 -S localhost:9150 $(tor-resolve %h localhost:9150) %p

Host securedrop-monitor
HostName r73jkrg6w63kq5k4.onion
User alice
CheckHostIP no
Compression yes
Protocol 2
ProxyCommand connect-proxy -4 -S localhost:9150 $(tor-resolve %h localhost:9150) %p
```

The configuration above requires that you have the [Tor Browser](https://www.torproject.org/download/download-easy.html.en) up and running before connecting to either of the two servers. If you want to connect to the *App Server*, simply open the terminal and type the following.

```
ssh securedrop-app
```

## Journalist's Workstation Setup

The journalist workstation computer is the laptop that the journalist uses on a daily basis. It can be running Windows, Mac OS X, or GNU/Linux. This computer must have GPG installed.

### Set up journalist GPG keys

Each journalist must have a personal GPG key that they use for encrypting files transferred from the `Secure Viewing Station` to their `Journalist Workstation`. The private key, used for decryption, stays on their `Journalist Workstation`. The public key, used for encryption, gets copied to the `Secure Viewing Station`.

If a journalist does not yet have a GPG key, they can follow these instructions to set one up with GnuPG (GPG).

* [GNU/Linux](https://www.gnupg.org/gph/en/manual.html#AEN26)
* [Windows](http://gpg4win.org/)
* [Mac OS X](https://support.gpgtools.org/kb/how-to/first-steps-where-do-i-start-where-do-i-begin)

### Journalist Logging In

In order to view the `Document Interface`, journalists needs to either 1) install the Tor Browser Bundle and modify it to authenticate to the hidden service, or 2) modify Tor through their Tails operating system to accomplish the same task. The latter is highly recommended since many news organzation's corporate computer systems have been compromised in the past.

**Though the Tails Operating System**

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
