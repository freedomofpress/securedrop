![SecureDrop](/docs/images/logo.png)

[![Build Status](https://travis-ci.org/freedomofpress/securedrop.png)](http://travis-ci.org/freedomofpress/securedrop)

SecureDrop is an open-source whistleblower submission system that media organizations can use to securely accept documents from and communicate with anonymous sources. It was originally created by the late Aaron Swartz and is currently managed by [Freedom of the Press Foundation](https://pressfreedomfoundation.org).

## Technical Summary

SecureDrop is a tool for sources to communicate securely with journalists. The SecureDrop application environment consists of three dedicated computers:

* `Secure Viewing Station`: An air-gapped laptop running the [Tails operating system](https://tails.boum.org/) from a USB stick that journalists use to decrypt and view submitted documents. (If this laptop does not have a DVD drive, buy an external DVD drive you can use with it.)
* `Application Server`: Ubuntu server running two segmented Tor hidden services. The source connects to the first, public-facing Tor hidden service to send messages and documents to the journalist. The journalist connects to the second authenticated Tor hidden service to download encrypted documents and respond to sources.
* `Monitor server`: Ubuntu server that monitors the `Application Server` and sends email alerts.

In addition to these dedicated computers, the journalist will also use his or her normal workstation computer:

* `Journalist Workstation`: The every-day laptop that the journalist uses for his or her work. The journalist will use this computer to connect to the `Application Server` to download encrypted documents that he or she will transfer to the `Secure Viewing Station`. The `Journalist Workstation` is also used to respond to sources.

Depending on the news organizations's threat model, it is recommended that journalists always use the [Tails operating system](https://tails.boum.org/) on their `Journalist Workstation` when connecting to the `Application Server`. Alternatively, this can also be its own dedicated computer.

These computers should all physically be in your organization's office.

## Before You Begin

Before beginning installation, you should have two servers running Ubuntu Server 12.04.4 LTS (Precise Pangolin), each with the grsec kernel patches installed. If you don't yet have those computers configured, see additional documentation for [Preparing Ubuntu servers for installation](/docs/ubuntu_config.md).

You will need a DVD with the latest version of the [Tails operating system](https://tails.boum.org/download/index.en.html) burned to it. Go [here for instructions](https://tails.boum.org/download/index.en.html) on how to download and burn Tails to a DVD.  You will only have to use this DVD once: After the first run from a Live DVD, you can create a Live USB to boot from instead. If you already have a Tails Live USB, you may skip this requirement. If you can't or don't want to burn a DVD, see the [Tails documentation](https://tails.boum.org/download/index.en.html) for alternative instructions.

You will also need a total of four USB sticks, preferably color-coded for easy distinction:
* USB stick with Tails for the `Secure Viewing Station`
* USB stick with Tails for the `Journalist Workstation`
* USB stick for transfering files from the `Journalist Workstation` to the `Secure Viewing Station`
* USB stick for transfering files from the `Secure Viewing Station` to the `Journalist Workstation`

The `Monitor Server` also sends emails. You will need an SMTP server, such as your company's mail server.

Finally, you will also need to come up with and memorize a series of passphrases. The best way to generate secure passphrases is to follow the [Diceware method](http://world.std.com/~reinhold/diceware.html). Generating secure passphrase takes time, so we recommend you generate these at the beginning of the installation process. You will need passphrases for:

* `Secure Viewing Station`'s Tails [Persistent Volume](https://tails.boum.org/doc/first_steps/persistence/index.en.html) that allows you to store files
* `Secure Viewing Station`'s GPG secret key
* `Journalist Workstation`'s Tails [Persistent Volume](https://tails.boum.org/doc/first_steps/persistence/index.en.html) that allows you to store files

If the journalist does not have a personal GPG secret keypair, he or she will have to create one as well.

## How to Contribute

See the [Development Guide](/docs/develop.md).

## How to Install SecureDrop

See the [Installation Guide](/docs/install.md).

## How to Use SecureDrop

See [how to use SecureDrop as a source](/docs/source_user_manual.md) and [how to use SecureDrop as a journalist](/docs/journalist_user_manual.md).

## License

SecureDrop is open source and released under the [GNU Affero General Public License v3](/LICENSE).

The [wordlist](/securedrop/wordlist) we use to generate source passphrases comes from [Diceware](http://world.std.com/~reinhold/diceware.html), and is licensed under Creative Commons Attribution 3.0 Unported thanks to A G Reinhold.
