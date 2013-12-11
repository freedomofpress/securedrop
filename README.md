![SecureDrop](/docs/images/logo.png)

SecureDrop is an open-source whistleblower submission system that media organizations can use to securely accept documents from and communicate with anonymous sources. It was originally created by the late Aaron Swartz and is currently managed by [Freedom of the Press Foundation](https://pressfreedomfoundation.org).

# Technical Summary

SecureDrop is a tool for sources to communicate securely with journalists. The SecureDrop application environment consists of three dedicated computers:

* `Secure Viewing Station`: An airgapped laptop running the [Tails operating system](https://tails.boum.org/) from a USB stick that journalists use to decrypt and view submitted documents. (If this laptop does not have a DVD drive, buy an external DVD drive you can use with it.)
* `Application Server`: Ubuntu server running two segmented Tor hidden services. The source connects to the first, public-facing Tor hidden service to send messages and documents to the journalist. The journalist connects to the second authenticated Tor hidden service to download encrypted documents and respond to sources.
* `Monitor server`: Ubuntu server that monitors the `Application Server` and sends email alerts.

In addition to these dedicated computers, the journalist will also use his or her normal workstation computer:

* `Journalist Workstation`: The every-day laptop that the journalist uses for his or her work. The journalist will use this computer to connect to the `Application Server` to download encrypted documents that he or she will transfer to the `Secure Viewing Station`. The `Journalist Workstation` is also used to respond to sources.

These computers should all physically be in your organization's office. 

## Before You Begin

Before beginning installation, you should have two servers running Ubuntu Server 12.04.3 LTS, each with the grsec kernel patches installed. If you don't yet have those computers configured, see additional documentation for [Preparing Ubuntu servers for installation](/docs/ubuntu_config.md).

You will need a DVD with the latest version of the [Tails operating system](https://tails.boum.org/download/index.en.html) burned to it. Go [here for instructions](https://tails.boum.org/download/index.en.html) on how to download and burn Tails to a DVD. You will only have to use this DVD once: After the first run from a Live DVD you can create a Live USB to boot from instead. If you already have a Tails Live USB, you may skip this requirement.

You will also need a total of three USB sticks:
* USB stick with Tails for the `Secure Viewing Station`
* USB stick for transfering files from the `Journalist Workstation` to the `Secure Viewing Station`
* USB stick for transfering files from the `Secure Viewing Station` to the `Journalist Workstation`

The `Monitor Server` also sends emails. You will need an SMTP server, such as your company's mail server.

Finally, you will also need to come up with and memorize a series of passphrases. The best way to generate secure passphrases is to follow the [Diceware method](http://world.std.com/~reinhold/diceware.html). Generating secure passphrase takes time, so we recommend you generate these at the beginning of the installation process. You will need passphrases for:

* `Secure Viewing Station`'s Tails [Persistent Volume](https://tails.boum.org/doc/first_steps/persistence/index.en.html) that allows you to store files
* `Secure Viewing Station`'s GPG secret key

Each journalist will also need to come up with a password for login to the `Application Server`.

## How to Install SecureDrop

After installing and configuring Ubuntu Server on `Application Server` and `Monitor Server`, and downloading, verifying, and burning Tails to a Live DVD, follow the [SecureDrop Installation Guide](/docs/install.md).

## How to Use SecureDrop

See [How to Use SecureDrop](/docs/user_manual.md).

## Demo

You can see live demos of the source and journalist websites at the following links. **These are for testing purposes only; please don't submit any documents here!**

In an actual SecureDrop setup, these websites are separate Tor hidden services running on the `Application Server`.

* [Source website](http://SecureDropDemo.org)
* [Journalist website](http://SecureDropDemo.org/journalist/) (needs the ending slash to work)

## License

SecureDrop is open source and released under the [GNU General Public License v2](/LICENSE). 

The [wordlist](/securedrop/wordlist) we use to generate source passphrases comes from [Diceware](http://world.std.com/~reinhold/diceware.html), and is licensed under Creative Commons Attribution 3.0 Unported thanks to A G Reinhold.
