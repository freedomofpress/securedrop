![SecureDrop](/docs/images/logo.png)

SecureDrop is an open-source whistleblower submission system managed by Freedom of the Press Foundation that media organizations use to securely accept documents from anonymous sources. It was originally coded by the late Aaron Swartz.

# Technical Summary

SecureDrop is a tool for sources to communicate securely with journalists. The SecureDrop application environment consists of four dedicated computers:

* `Viewing Station`: An airgapped laptop running Tails from a USB stick that journalists use to decrypt and view submitted documents. (If this laptop does not have a DVD drive, buy an external DVD drive you can use with it.)
* `Source Server`: Ubuntu server running a Tor hidden service that sources use to send messages and documents to journalists.
* `Document Server`: Ubuntu server running a Tor hidden service that journalists use to download encrypted documents and respond to sources.
* `Monitor`: Ubuntu server that monitors the `Source` and `Document` servers and sends email alerts.

In addition to these computers, journalists use normal workstation computers:

* `Journalist Workstations`: The every-day laptops that journalists use. They will use this computer to connect to the `Document Server` to respond to sources and download encrypted documents to copy to the `Viewing Station`. They will also copy encrypted documents back from the `Viewing Station` station to this computer to do final work before publication.

These computers should all physically be in your organization's office. 

## Before You Begin

Before beginning installation, you should have three servers running Ubuntu Server 12.04.3 LTS, each with the grsec kernel patches installed. If you don't yet have those computers configured, see additional documentation for [Preparing Ubuntu servers for installation](/docs/ubuntu_config.md).

You will need a DVD with the latest version of the [Tails](https://tails.boum.org/download/index.en.html) operating system burned to it. You will only have to use this DVD once: After the first run from a Live DVD you can create a Live USB to boot from instead. If you already have a Tails Live USB, you may skip this requirement.

You will also need a total of three USB sticks:
* USB stick with Tails for the `Viewing Station`
* USB stick for transfering files from the `Journalist Workstations` to the `Viewing Station`
* USB stick for transfering files from the `Viewing Station` to the `Journalist Workstations`

The `Monitor Server` also sends emails. You will need an SMTP server, such as your company's mail server.

Finally, you will also need to come up with and memorize a series of passphrases. The best way to generate secure passphrases is to follow the [Diceware method](http://world.std.com/~reinhold/diceware.html). Generating secure passphrase takes time, so we recommend you generate these at the beginning of the installation process. You will need passphrases for:

* `Viewing Station`'s Tails Persistent Volume
* `Viewing Station`'s OpenPGP secret key

Each journalist will also need to come up with a password for login to the `Document Server`.

## How to Install SecureDrop

After installing and configuring Ubuntu Server on `Source Server`, `Document Server`, and `Monitor Server`, and download, verifying, and burning Tails to a Live DVD, follow the [SecureDrop Installation Guide](/docs/install.md).

## How to Use SecureDrop

See [How to Use SecureDrop](/docs/user_manual.md).

## Demo

You can see live demos of the source and journalist websites at the following links. **These are for testing purposes only; please don't submit any documents here!**

In an actual SecureDrop setup, these websites are Tor hidden services running on the `Source Server` and `Document Server`, respectively.

* [Source website](http://SecureDropDemo.org)
* [Journalist website](http://SecureDropDemo.org/journalist/) (needs the ending slash to work)

## License

SecureDrop is open source and released under the [GNU General Public License v2](/LICENSE). 

The [wordlist](/modules/deaddrop/files/deaddrop/wordlist) we use to generate source passphrases comes from [Diceware](http://world.std.com/~reinhold/diceware.html), and is licensed under Creative Commons Attribution 3.0 Unported thanks to A G Reinhold. 
