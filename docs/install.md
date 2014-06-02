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

In addition to the requirements above, each journalist will also have their own device capable of running Google Authenticator, a USB stick for transferring files between the `Secure Viewing Station` and their `Journalist Workstation`, and a personal GPG key. See [this section](/docs/install.md#set-up-journalist-gpg-keys) for instructions to set one up for journalists who don't have already have a key. 

We also suggest that you have an external hard drive for backing up encrypted submitted documents and some form of removable media for backing up the application's GPG keyring.

## Secure Viewing Station

The `Secure Viewing Station` will be air-gapped (never connected to the Internet) and will always boot from your air-gapped Tails USB stick. Because of this, you don't need a hard drive or network device. You may want to consider physically opening this computer and removing the hard drive and wifi card, but doing this is outside the scope of this manual.

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

## Generate GPG key used to encrypt OSSEC alerts
TODO add steps email address set in key needs to match the email address to be used

## Server Installation

Both the `App Server` and `Monitor Server` should already have Ubuntu Server installed. To follow these instructions you should know how to navigate the command line.

### Admin's SSH Client
In order to SSH over Tor to access the servers after the install is completed you will need to install and configure a proxy tool to proxy you ssh connection over tor.
Torify and connect-proxy are two tools that can be used to proxy ssh connections over tor.

### App Server
#### Required Information
* The Application's GPG key
* The Application's GPG key fingerprint
* A branded image to replace the large SecureDrop image on the Source and Document Interface
* A journalist's first name
* An admin's username with an existing OS account (most likely the account you are using for the install)
* The Monitor Server's IP address

#### To install from apt repo run the following block of commands
```
wget https://pressfreedomfoundation.org/securedrop-files/add-repos.tgz && \
tar -xzf add-repos.tgz && \
sudo chmod +x ./add-repos.sh && \
sudo ./add-repos.sh && \
sudo apt-get -y install securedrop-app && \
sudo /opt/securedrop/post-install.sh
```
Record the values displayed in red from the post install script

### Monitor Server
####Required Information
* An admin's username with an existing OS account (most likely the account you are using for the install)
* The `App Server`'s IP address
* The destination email address for the ossec alerts
* The gpg key that has the same email address set as the destination email address for the OSSEC alerts
* The OSSEC alert email address GPG key's fingerprint

#### To install from apt repo run the following block of commands
```
wget https://pressfreedomfoundation.org/securedrop-files/add-repos.tgz && \
tar -xzf add-repos.tgz && \
sudo chmod +x ./add-repos.sh && \
sudo ./add-repos.sh && \
sudo apt-get install securedrop-monitor -y && \
sudo /opt/securedrop/post-install.sh
```
Record the values displayed in red from the post install script

### Add OSSEC Agent
Adding the OSSEC agent requires taking a long hash value outputed on the `Monitor Server` and entering it into the `App Server`
You should wait until you have ssh'd through tor to both boxes so you can copy and paste from one window to the other.
This will require you to switch between the 'Monitor Server' to the 'App Server' then back to the 'Monitor Server'.

Monitor Server (TODO add screenshot of /var/ossec/bin/manage-agents and restart ossec)

App Server (TODO add screenshot of importing hash value and restart ossec)

Monitor Server (TODO add screenshot of /var/ossec/bin/list_agents -a to show agent connected)

### Configure Postfix
Postfix is used to route the OSSEC alerts to the organizations smtp server. While the bodies of the emails will be encrypted, you should still configure a high secure smtp relay connection using STARTTLS (port 587) and Certificate Pinning and sasl authentication. An example for using smtp.gmail.com as the smtp relay is provided below. If you use smtp.gmail.com you should create an [Application Specific Password](http://www.youtube.com/watch?v=zMabEyrtPRg&t=2m13s) to use for the sasl authentication.

The smtp STARTTLS certificate's fingerprint was retieved using
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
smtp_tls_fingerprint_cert_match = 10:75:E1:8C:DF:93:15:3B:A1:8F:CD:FE:D3:11:79:D5:16:43:77:BC
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

Change `USERNAME` `DOMAIN` and `PASSWORD` to the correct values

#### Apply settings and restart postfix
```
sudo chmod 400 /etc/postfix/sasl_passwd && \
sudo postmap /etc/postfix/sasl_passwd && \
cat /etc/ssl/certs/Thawte_Premium_Server_CA.pem | sudo tee -a /etc/postfix/cacert.pem && \
sudo /etc/init.d/postfix reload
```

Once you have completed these steps, the SecureDrop web application should be set up.

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
