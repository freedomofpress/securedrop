![SecureDrop](https://raw.github.com/freedomofpress/securedrop/master/docs/images/logo.png)

You may be confused right now, but don't worry. Stay tuned for a big announcement. ;)

SecureDrop Environment Install Guide
====================================

SecureDrop is a tool for sources to communicate securely with journalists. The SecureDrop application environment consists of four dedicated computers:

* `Viewing Station`: An airgapped laptop running Tails from a USB stick that journalists use to decrypt and view submitted documents. (If this laptop does not have a DVD drive, buy an external DVD drive you can use with it.)
* `Source Server`: Ubuntu server running a Tor hidden service that sources use to send messages and documents to journalists.
* `Document Server`: Ubuntu server running a Tor hidden service that journalists use to download encrypted documents and respond to sources.
* `Monitor`: Ubuntu server that monitors the `Source` and `Document` servers and sends email alerts.

In addition to these computers, journalists use normal workstation computers:

* `Journalist Workstations`: The every-day laptops that journalists use. They will use this computer to connect to the `Document Server` to respond to sources and download encrypted documents to copy to the `Viewing Station`. They will also copy encrypted documents back from the `Viewing Station` station to this computer to do final work before publication.

These computers should all physically be in your organization's office. 

## Before You Begin

Before beginning installation, you should have three servers running Ubuntu Server 12.04.3 LTS, each with the grsec kernel patches installed. If you don't yet have those computers configured, see additional documentation for [Preparing Ubuntu servers for installation](https://github.com/freedomofpress/securedrop/blob/master/docs/ubuntuconfig.md).

You will need a DVD with the latest version of the [Tails](https://tails.boum.org/download/index.en.html) operating system burned to it. You will only have to use this DVD once: After the first run from a Live DVD you can create a Live USB to boot from instead. If you already have a Tails Live USB, you may skip this requirement.

You will also need a total of three USB sticks:
* USB stick with Tails for the `Viewing Station`
* USB stick for transfering files from the `Journalist Workstations` to the `Viewing Station`
* USB stick for transfering files from the `Viewing Station` to the `Journalist Workstations`

Finally, you will also need to come up with and memorize a series of passphrases. The best way to generate secure passphrases is to follow the [Diceware method](http://world.std.com/~reinhold/diceware.html). Generating secure passphrase takes time, so we recommend you generate these at the beginning of the installation process. You will need passphrases for:

* `Viewing Station`'s Tails Persistent Volume
* `Viewing Station`'s OpenPGP secret key
* `Viewing Station`'s SSL certificate authority secret key

Each journalist will also need to come up with a password for login to the `Document Server`.
