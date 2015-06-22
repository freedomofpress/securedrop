# Hardware for SecureDrop

This document outlines requirements and recommended hardware for use with SecureDrop. If you have any questions, please contact securedrop@freedom.press.

## SecureDrop Infrastructure

The SecureDrop infrastructure consists of different components, all of which are listed below. We recommend you read through the whole document and figure out what makes the most sense for your organization.

### App Server and Monitor Server

The *Application Server* (or *App Server* for short) runs the SecureDrop application. This server hosts both the website that sources access (*Source Interface*) and the website that journalists access (*Document Interface*). The *Monitor Server* keeps track of the *App Server* and sends out email alerts if something seems wrong. SecureDrop requires that you have:

 * 1 x physical server for the *Application Server*, which will run the SecureDrop application.
 * 1 x physical server for the *Monitor Server*, which sends emails about issues with the *App Server*.

The SecureDrop application requires a 64-bit operating system. You can repurpose old hardware if it is capable of running 64-bit Ubuntu. Otherwise, we recommend you get two [Intel NUCs](http://www.amazon.com/dp/B00F3F38O2/) with power cords. Make sure you also get the cables required to connect the NUCs to a monitor. Additionally, you will need to get the following [two 240 GB hard drives](http://www.amazon.com/dp/B00BQ8RKT4/) and a [4 GB (2GBx2) memory kit](http://www.amazon.com/Crucial-PC3-12800-204-Pin-Notebook-CT2CP25664BF160B/dp/B005MWQ6WC/).

#### Potential BIOS issue

The previous release of SecureDrop (0.2.1) was based on Ubuntu 12.04.1 (precise). We encountered issues installing this version of SecureDrop on some types of Intel NUCs. The problem manifested after installing Ubuntu on the NUC. The installation would complete, but rebooting after installation would not succeed.

We have not encountered this or any similar problems in testing the current release (0.3) with the Intel NUCs. Since 0.3 is based on Ubuntu 14.04.1 (trusty), we believe the issue has been resolved by Ubuntu.

If you do encounter issues booting Ubuntu on the NUCs, try [updating the BIOS according to these instructions](http://arstechnica.com/gadgets/2014/02/new-intel-nuc-bios-update-fixes-steamos-other-linux-booting-problems/).

### Secure Viewing Station (SVS)

The *Secure Viewing Station* is a machine that is kept offline and only ever used together with the Tails operating system. This machine will be used to generate GPG keys for all journalists with access to SecureDrop, as well as decrypt and view submitted documents. Since this machine will never touch the Internet or run an operating system other than Tails, it does not need a hard drive or network device. We recommend the following:

 * 1 x laptop without a hard drive, network interface card or wireless units.
 * 1 x encrypted, external hard drive to store documents on while working on a story.
 * 1 x offline printer.

We recommend that you either buy or repurpose an old laptop. Another option is to buy an [Intel NUC](http://www.amazon.com/dp/B00F3F38O2/) with a power cord and [4 GB of memory](http://www.amazon.com/Crucial-PC3-12800-204-Pin-Notebook-CT2CP25664BF160B/dp/B005MWQ6WC/), but note that you will also need to get a monitor and a wired keyboard and mouse.

#### Printers

Careful consideration should be given to the printer used with the SVS. Most printers today have wireless functionality (WiFi or Bluetooth connectivity) which should be **avoided** because it could be used to compromise the airgap.

Unfortunately, it is difficult to find printers that work with Tails, and it is increasingly difficult to find non-wireless printers at all. To assist you, we have compiled the following partial list of airgap-safe printers that have been tested and are known to work with Tails:

| Model                     | Testing Date | Tails Versions | Price (new)      | Price (used)     | Notes      |
|---------------------------|--------------|----------------|------------------|------------------|------------|
| HP LaserJet 400 M401n     | 06/2015      | 1.4            | $178.60 (Amazon) | $115.00 (Amazon) | Monochrome laser printer. Heavy (10 lbs.) When adding the printer in Tails, you need to set "Make and model" to "HP LaserJet 400 CUPS+Gutenprint v5.2.9". |
| HP Deskjet 6940           | 04/2015      | 1.3.2          | $639.99 (Amazon) | $196.99 (Amazon) | Monochrome Inkjet printer |

If you know of another model of printer that fits our requirements and works with Tails, please submit a pull request to add it to this list.

### Tails and Transfer Devices

The *Transfer Device* is the physical media used to transfer encrypted documents from the *Journalist Workstation* to the *Secure Viewing Station*. Additional devices are needed to run Tails. We recommend the following:

 * 1 x physical media for the system administrator to run Tails on.
 * 1 x physical media for the system administrator to transfer files with.
 * 1 x physical media for the journalist to run Tails on.
 * 1 x physical media for the journalist to transfer files with.
 * 1 x physical media with Tails for the *Secure Viewing Station*.
 * 1 x physical media with Tails for the *Secure Viewing Station* (backup).

We recommend getting [16 GB Leef Supra](http://www.amazon.com/dp/B00FWQTBZ2/) USB sticks to run Tails on, and [4 GB Patriot](http://www.amazon.com/Swivel-Flash-Drive-Memory-Stick/dp/B00M1GYD90/) USB sticks to use when transferring files. Each journalist should have two USB sticks. For the Secure Viewing Station and backup, we recommend getting [Corsair 64 GB](http://www.amazon.com/dp/B00EM71W1S/) USB sticks.

Another alternative setup exists in which journalists do not transfer files on a USB stick, but instead use a CD-R or DVD-R. The encrypted documents are copied to the CD-R or DVD-R, then decrypted and read on the Secure Viewing Station. The disks are destroyed after first use. We recommend getting a [Samsung model burner](http://www.newegg.com/External-CD-DVD-Blu-Ray-Drives/SubCategory/ID-420) for this purpose.

### Two-factor authentication device

Two-factor authentication is used when connecting to different parts of the SecureDrop system, including the *Document Interface*. We recommend the following for each administrator or journalist with access to the system:

 * 1 x two-factor authentication device

We recommend using either a smartphone capable of running [Google Authenticator](https://support.google.com/accounts/answer/1066447?hl=en) or a [YubiKey](https://www.yubico.com/products/yubikey-hardware/yubikey/).

### Network firewall

An important part of SecureDrop's security model involves segmenting the infrastructure from the Internet and/or the corporate environment. For this reason, we recommend that you get:

 * 1 x firewall with pfSense and minimum three NICs.

We recommend getting a Netgate firewall with pfSense pre-installed, and you can choose from a firewall with [2 GB of system memory](http://store.netgate.com/NetgateAPU2.aspx) or one with [4 GB of system memory](http://store.netgate.com/APU4.aspx).

### Network Switch

If you firewall has fewer than **four** NICs, you will need an additional Ethernet switch to perform installation and maintenance tasks with the Admin Workstation. This switch is generally useful because it allows you to connect to your firewall's LAN port without taking down either of the SecureDrop servers, which is useful if you want to perform maintenance tasks from the Admin Workstation on the SecureDrop installation or the firewall configuration. This is possible without the switch if your firewall has enough ports, but you will need to perform some additional initial firewall setup to get this to work.

We recommend getting a [5-port Netgear ProSafe Ethernet Switch](http://www.amazon.com/NETGEAR-ProSafe-Gigabit-Ethernet-Desktop/dp/B0000BVYT3/) or similar.

## Appendix

### Notes on the NUCs

There are a variety of available NUCs, and each different model supports different hardware specs and peripheral connectors. For hardware testing, we have been using:

#### D34010WYK

[Amazon link w/ picture](http://www.amazon.com/Intel-Computing-BOXD34010WYK1-Black-White/dp/B00H3YT886/)

We have been using one for the Secure Viewing Station (SVS), which is air-gapped and never connected to the Internet, and one for the Admin Workstation, which is Internet-connected and is used to run the Ansible playbooks. You could also use an existing workstation, or a recycled machine, for this purpose, assuming you feel confident that this machine has not been physically compromised in any way.

This machine has USB 3.0, which is nice for booting live USBs quickly and for transferring large files. It has two available display connectors: Mini-HDMI and DisplayPort.

#### DC3217IYE

[Amazon link w/ picture](http://www.amazon.com/Intel-Computing-Gigabit-i3-3217U-DC3217IYE/dp/B0093LINVK)

We have been using two of these for the Application and Monitor servers (app and mon). They only have USB 2.0, which is not so bad because the Linux installation using live USB is a one-time process and you rarely transfer files directly from the servers. They also only have one available display connector: HDMI.
