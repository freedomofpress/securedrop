Terminology
===========

A number of terms used in this guide, and in the `SecureDrop workflow
diagram <https://docs.securedrop.org/en/latest/overview.html#infrastructure>`__,
are specific to SecureDrop. The list below attempts to enumerate and
define these terms.

.. todo:: Pictures would be good for many of the objects defined here

Source
------

The *Source* is the person who submits documents to SecureDrop, and may use
SecureDrop to communicate with a *Journalist*. A *Source* will always
access SecureDrop through the *Source Interface*, and must do so using Tor.

Instructions for using SecureDrop as a *Source* are available in our
`Source Guide <https://docs.securedrop.org/en/latest/source.html>`__.

Journalist
----------

The *Journalist* uses SecureDrop to communicate with and download documents
submitted by the *Source*. Journalists do this by using the *Journalist
Workstation* to connect to the *Journalist Interface* over Tor.

The *Journalist* also uses a *Transfer Device* to move documents to the *Secure
Viewing Station*. If a *Journalist* chooses to release any of these documents,
they can be prepared for publication on the *Secure Viewing Station* before
being transferred to an Internet-connected computer.

Instructions for using SecureDrop as a *Journalist* are available in our
`Journalist Guide <https://docs.securedrop.org/en/latest/journalist.html>`__.

Application Server
------------------

The *Application Server* runs the SecureDrop application. This server hosts both
the website that sources access (the *Source Interface*) and the website that
journalists access (the *Journalist Interface*). Sources, journalists, and
admins may only connect to this server using Tor.

Monitor Server
--------------

The *Monitor Server* keeps track of the *Application Server* and sends out an
email alert if something seems wrong. Only system admins connect
to this server, and they may only do so using Tor.

Source Interface
----------------

The *Source Interface* is the website that sources will access to
submit documents and communicate with journalists. This site is
hosted on the *Application Server* and can only be accessed over Tor.

Instructions for using the *Source Interface* are available in our `Source Guide
<https://docs.securedrop.org/en/latest/source.html>`__.

Journalist Interface
--------------------

The *Journalist Interface* is the website that journalists access to download
new documents and communicate with sources. This site is hosted on the
*Application Server* and can only be accessed over Tor. In previous releases,
this was called the *Document Interface*, but we have renamed it to avoid
ambiguity.

Instructions for using the *Journalist Interface* are available in our
`Journalist Guide <https://docs.securedrop.org/en/latest/journalist.html>`__.

Journalist Workstation
----------------------

The *Journalist Workstation* is a machine that is online and used
together with the Tails operating system on the *online* USB stick. This
machine will be used to connect to the *Journalist Interface*, download
documents, and move them to the *Secure Viewing Station* using the
*Transfer Device*.

Instructions for using the *Journalist Workstation* are available in our
`Journalist Guide <https://docs.securedrop.org/en/latest/journalist.html>`__.

Admin Workstation
-----------------

The *Admin Workstation* is a machine that the system admin can
use to connect to the *Application Server* and the *Monitor Server* using Tor
and SSH. The admin will also need to have an Android or iOS
device with the FreeOTP app installed.

Secure Viewing Station
----------------------

The *Secure Viewing Station* (or *SVS* for short) is a machine that is
kept offline and only ever used together with the Tails operating system
on the *offline* USB stick. This machine will be used to generate GPG
keys for all journalists with access to SecureDrop, as well as to
decrypt and view submitted documents.

Since this machine will never touch the Internet or run an operating
system other than Tails on a USB, it does not need a hard drive or
network device. We recommend physically removing the drive and any
networking cards (wireless, Bluetooth, etc.) from this machine.

This is also referred to as the "airgapped computer," meaning there is a
gap between it and a computer connected to the Internet.

Two-Factor Authenticator
------------------------

There are several places in the SecureDrop architecture where two-factor
authentication is used to protect access to sensitive information or
systems. These instances use the standard TOTP and/or HOTP algorithms,
and so a variety of devices can be used to provide two-factor
authentication for devices. We recommend using one of:

-  FreeOTP `for Android <https://play.google.com/store/apps/details?id=org.fedorahosted.freeotp>`__ or `for iOS <https://itunes.apple.com/us/app/freeotp-authenticator/id872559395>`__ installed
-  A `YubiKey <https://www.yubico.com/products/yubikey-hardware/>`__

.. include:: includes/otp-app.txt

Transfer Device
---------------

The *Transfer Device* is the physical media used to transfer encrypted
documents from the *Journalist Workstation* to the *Secure Viewing
Station*. Examples: a dedicated USB stick, CD-R, DVD-R, or SD card.

If you use a USB stick for the *Transfer Device*, we recommend using a
small one (4GB or less). It will be necessary to securely wipe the entire
device at times, and this process takes longer for larger devices.

Depending on your threat model, you may wish to only use one-time use
media (such as CD-R or DVD-R) for transferring files to and from the
*SVS*. While doing so is cumbersome, it reduces the risk of malware (that
could be run simply by opening a malicious submission) exfiltrating
sensitive data, such as the private key used to decrypt submissions or
the content of decrypted submissions.

When we use the phrase "sneakernet" we mean physically moving documents
with the *Transfer Device* from one computer to another.
