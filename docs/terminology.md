## Terminology

A number of terms used in this guide, and in the [SecureDrop workflow diagram](https://freedom.press/securedrop-files/SecureDrop_complex.png), are specific to SecureDrop. The list below attempts to enumerate and define these terms.

### App Server

The *Application Server* (or *App Server* for short) runs the SecureDrop application. This server hosts both the website that sources access (*Source Interface*) and the website that journalists access (*Document Interface*). You may only connect to this server using Tor.

### Monitor Server

The *Monitor Server* keeps track of the *App Server* and sends out an email alert if something seems wrong. You may only connect to this server using Tor.

### Source Interface

The *Source Interface* is the website that sources will access when submitting documents and communicating with journalists. This site is hosted on the *App Server* and can only be accessed over Tor.

### Document Interface

The *Document Interface* is the website that journalists will access when downloading new documents and communicating with sources. This site is hosted on the *App Server* and can only be accessed over Tor.

### Journalist Workstation

The *Journalist Workstation* is a machine that is online and used together with the Tails operating system on the *online* USB stick. This machine will be used to connect to the *Document Interface*, download documents, and move them to the *Secure Viewing Station* using the *Transfer Device*.

### Admin Workstation

The *Admin Workstation* is a machine that the system administrator can use to connect to the *App Server* and the *Monitor Server* using Tor and SSH. The administrator will also need to have an Android or iOS device with the Google Authenticator app installed.

### Secure Viewing Station

The *Secure Viewing Station* (or *SVS* for short) is a machine that is kept offline and only ever used together with the Tails operating system on the *offline* USB stick. This machine will be used to generate GPG keys for all journalists with access to SecureDrop, as well as to decrypt and view submitted documents.

Since this machine will never touch the Internet or run an operating system other than Tails on a USB, it does not need a hard drive or network device. We recommend physically removing the drive and any networking cards (wireless, Bluetooth, etc.) from this machine.

### Two-Factor Authenticator

There are several places in the SecureDrop architecture where two-factor authentication is used to protect access to sensitive information or systems. These instances use the standard TOTP and/or HOTP algorithms, and so a variety of devices can be used to provide two factor authentication for devices. We recommend using one of:

* An Android or iOS device with [Google Authenticator](https://support.google.com/accounts/answer/1066447?hl=en) installed
* A [Yubikey](http://www.yubico.com/products/yubikey-hardware/)

### Transfer Device

The *Transfer Device* is the physical media used to transfer encrypted documents from the *Journalist Workstation* to the *Secure Viewing Station*. Examples: a dedicated USB stick, CD-R, DVD-R, or SD card.

If you use a USB stick for the transfer device, we recommend using a small one (4GB or less). You will want to securely wipe the entire device at times, and this process takes longer for larger devices.

Depending on your threat model, you may wish to only use one-time use media (such as CD-R or DVD-R) for transferring files to and from the SVS. While doing so is cumbersome, it reduces the risk of malware (that could be run simply by opening a malicious submission) exfiltrating sensitive data, such as the private key used to decrypt submissions or the content of decrypted submissions.

### Computers

* Application Server
* Monitor Server
* Admin Workstation (any spare computer that can be connected to the firewall and can run Tails)
* Firewall

### USBs/DVDs/CDs

 * CD, DVD, or USB to use when [installing Ubuntu on the Application Server and the Monitor Server](/docs/ubuntu_config.md).
 * CD, DVD, or USB to use when [setting up Tails Live with persistence](/docs/tails_guide.md).
 * Brand new USB, marked *transfer*, to use as the *Transfer Device*.

Additionally, you will need a minimum of 4 USB sticks which will become Tails Live USB's with persistence. You should mark two *offline*, one *online*, and one *admin*. This is enough to set up a system with one admin and one journalist (note that the same person can perform both of these roles). To add more administrators or journalists, you will need more USB sticks.

Finally, each user, whether admin or journalist, will need a *Two-Factor Authenticator*.

Each journalist will also need a *Transfer Device* for transferring files between the *Secure Viewing Station* and their *Journalist Workstation*, and a personal GPG key. Make sure you [create GPG keys](/docs/install.md#set-up-journalist-gpg-keys) for journalists who do not already have one.

The second *offline* Tails Live USB with persistence will be used as the encrypted offline backup. This device will be a copy of the main *SVS* Tails Live USB with persistence.

### Passphrases

A SecureDrop installation will require at least two roles, an admin and a journalist, and each role will require a number of strong, unique passphrases. The Secure Viewing Station, which will be used by the journalist, also requires secure and unique passphrases. The list below is meant to be an overview of the accounts, passphrases and two-factor secrets that are required by SecureDrop.

We have created a KeePassX password database template that both the admin and the journalist can use on Tails to ensure they not only generate strong passphrases, but also store them safely. By using KeePassX to generate strong, unique passphrases, you will be able to achieve excellent security while also maintaining usability, since you will only have to personally memorize a small number of strong passphrases. More information about using the password database template on Tails is included in the [Tails Setup Guide](/docs/tails_guide.md#passphrase-database).

#### Admin

The admin will be using the *Admin Workstation* with Tails to connect to the App Server and the Monitor Server using Tor and SSH. The tasks performed by the admin will require the following set of passphrases:

 * A password for the persistent volume on the Admin Live USB.
 * A master password for the KeePassX password manager, which unlocks passphrases to:
     * The App Server and the Monitor Server (required to be the same).
     * The network firewall.
     * The SSH private key and, if set, the key's passphrase.
     * The GPG key that OSSEC will encrypt alerts to.
     * The admin's personal GPG key.
     * The credentials for the email account that OSSEC will send alerts to.
     * The Hidden Services values required to connect to the App and Monitor Server.
 
The admin will also need to have an Android or iOS device with the Google Authenticator app installed. This means the admin will also have the following two credentials:

 * The secret code for the App Server's two-factor authentication.
 * The secret code for the Monitor Server's two-factor authentication.
 
#### Journalist

The journalist will be using the *Journalist Workstation* with Tails to connect to the Document Interface. The tasks performed by the journalist will require the following set of passphrases:

 * A master password for the persistent volume on the Tails device.
 * A master password for the KeePassX password manager, which unlocks passphrases to:
     * The Hidden Service value required to connect to the Document Interface.
     * The Document Interface.
     * The journalist's personal GPG key.
     
The journalist will also need to have a two-factor authenticator, such as an Android or iOS device with Google Authenticator installed, or a YubiKey. This means the journalist will also have the following credential:

 * The secret code for the Document Interface's two-factor authentication.
 
#### Secure Viewing Station

The journalist will be using the *Secure Viewing Station* with Tails to decrypt and view submitted documents. The tasks performed by the journalist will require the following set of passphrases:

 * A master password for the persistent volume on the Tails device.

The backup that is created during the installation of SecureDrop is also encrypted with the application's GPG key. The backup is stored on the persistent volume of the Admin Live USB.
