Glossary
========

A number of terms used in this guide, and in the `SecureDrop workflow
diagram <https://docs.securedrop.org/en/latest/overview.html#infrastructure>`__,
are specific to SecureDrop. The list below attempts to enumerate and
define these terms.

Source
------

The *Source* is the person who submits documents to SecureDrop and may use
SecureDrop to communicate with a *Journalist*. A *Source* will always
access SecureDrop through the *Source Interface* and must do so using Tor.

Instructions for using SecureDrop as a *Source* are available in our
`Source Guide <https://docs.securedrop.org/en/latest/source.html>`__.

Journalist
----------

The *Journalist* uses SecureDrop to communicate with and download documents
submitted by the *Source*. Journalists do this by using the *Journalist
Workstation* to connect to the *Journalist Interface* through Tor.

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

Landing Page
------------

The *Landing Page* is the public-facing webpage for a SecureDrop instance. This
page is hosted as a standard (i.e. non-Tor) webpage on the news organization's
site. It provides first instructions for potential sources.

Source Interface
----------------

The *Source Interface* is the website that sources will access to
submit documents and communicate with journalists. This site is
hosted on the *Application Server* and can only be accessed through Tor.

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

.. _svs:

Secure Viewing Station
----------------------

The *Secure Viewing Station* (or *SVS* for short) is the computer you use to
decrypt and view documents and messages submitted to your SecureDrop. This
computer is permanently kept offline. It is "air-gapped", meaning that there
is a gap between it and any computer connected to the Internet.

You will boot the *SVS* from a designated USB stick running the Tails operating
system. Once you have created it, you should never attach this USB stick to any
Internet-connected device.

During the installation, the *SVS* is used to generate the *Submission Key*
for encrypting and decrypting documents and messages submitted to SecureDrop.
In addition, we recommend importing the public keys of individual journalists to
the *SVS*, so you can securely encrypt files to their keys before exporting them.

Since this machine will never touch the Internet or run an operating
system other than Tails on a USB, it does not need a hard drive or
network device. We recommend physically removing the drive and any
networking cards (wireless, Bluetooth, etc.) from this machine.

.. _submission-key:

Submission Key
--------------

The *Submission Key* is the GPG keypair used to encrypt and decrypt documents
and messages sent to your SecureDrop. Because the public key and private key
must be treated very differently, we sometimes refer to them explicitly as the
*Submission Public Key* and the *Submission Private Key*.

The *Submission Public Key* is uploaded to your SecureDrop servers as part of
the installation process. Once your SecureDrop is online, anyone will be able
to download it.

The *Submission Private Key* should never be accessible to a computer with
Internet connectivity. Instead, it should remain on the *Secure Viewing Station*
and on offline backup storage.

Two-Factor Authentication
-------------------------

There are several places in the SecureDrop architecture where two-factor
authentication is used to protect access to sensitive information or
systems. These instances use the standard TOTP and/or HOTP algorithms,
and so a variety of devices can be used to generate 6-digit two-factor
authentication codes. We recommend using one of:

-  FreeOTP `for Android <https://play.google.com/store/apps/details?id=org.fedorahosted.freeotp>`__ or `for iOS <https://itunes.apple.com/us/app/freeotp-authenticator/id872559395>`__ installed
-  A `YubiKey <https://www.yubico.com/products/yubikey-hardware/>`__

.. include:: includes/otp-app.txt

Transfer Device
---------------
The *Transfer Device* is the physical media (e.g., designated USB drive) used
to transfer encrypted documents from the *Journalist Workstation* to the
*Secure Viewing Station*, where they can be decrypted.

Please see the detailed security recommendations for the choice, configuration
and use of your *Transfer Device* in the :doc:`journalist guide <journalist>`
and in the :doc:`setup guide <set_up_transfer_and_export_device>`.

Export Device
-------------
The *Export Device* is the physical media (e.g., designated USB drive) used to
transfer decrypted documents from the *Secure Viewing Station* to a journalist's
everyday workstation, or to another computer for additional processing.

Please see the detailed security recommendations for the choice, configuration
and use of your *Export Device* in the :doc:`journalist guide <journalist>`
and in the :doc:`setup guide <set_up_transfer_and_export_device>` .
