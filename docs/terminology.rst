Terminology
===========

A number of terms used in this guide, and in the `SecureDrop workflow
diagram <https://freedom.press/securedrop-files/SecureDrop_complex.png>`__,
are specific to SecureDrop. The list below attempts to enumerate and
define these terms.

.. todo:: Pictures would be good for many of the objects defined here

App Server
----------

The *Application Server* (or *App Server* for short) runs the SecureDrop
application. This server hosts both the website that sources access
(*Source Interface*) and the website that journalists access (*Journalist
Interface*). You may only connect to this server using Tor.

Monitor Server
--------------

The *Monitor Server* keeps track of the *App Server* and sends out an
email alert if something seems wrong. You may only connect to this
server using Tor.

Source Interface
----------------

The *Source Interface* is the website that sources will access when
submitting documents and communicating with journalists. This site is
hosted on the *App Server* and can only be accessed over Tor.

Journalist Interface
------------------

The *Journalist Interface* is the website that journalists will access
when downloading new documents and communicating with sources. This site
is hosted on the *App Server* and can only be accessed over Tor. In previous
releases, this was called the *Document Interface*, but we have renamed it
to avoid ambiguity.

Journalist Workstation
----------------------

The *Journalist Workstation* is a machine that is online and used
together with the Tails operating system on the *online* USB stick. This
machine will be used to connect to the *Journalist Interface*, download
documents, and move them to the *Secure Viewing Station* using the
*Transfer Device*.

Admin Workstation
-----------------

The *Admin Workstation* is a machine that the system administrator can
use to connect to the *App Server* and the *Monitor Server* using Tor
and SSH. The administrator will also need to have an Android or iOS
device with the Google Authenticator app installed.

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
and so a variety of devices can be used to provide two factor
authentication for devices. We recommend using one of:

-  An Android or iOS device with `Google
   Authenticator <https://support.google.com/accounts/answer/1066447?hl=en>`__
   installed
-  A `YubiKey <https://www.yubico.com/products/yubikey-hardware/>`__

Transfer Device
---------------

The *Transfer Device* is the physical media used to transfer encrypted
documents from the *Journalist Workstation* to the *Secure Viewing
Station*. Examples: a dedicated USB stick, CD-R, DVD-R, or SD card.

If you use a USB stick for the transfer device, we recommend using a
small one (4GB or less). You will want to securely wipe the entire
device at times, and this process takes longer for larger devices.

Depending on your threat model, you may wish to only use one-time use
media (such as CD-R or DVD-R) for transferring files to and from the
SVS. While doing so is cumbersome, it reduces the risk of malware (that
could be run simply by opening a malicious submission) exfiltrating
sensitive data, such as the private key used to decrypt submissions or
the content of decrypted submissions.

When we use the phrase "sneakernet" we mean physically moving documents
on the Transfer Device from one computer to another.
