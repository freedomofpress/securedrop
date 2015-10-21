Hardware
========

This document outlines the required hardware components necessary to
successfully install and operate a SecureDrop instance, and recommends
some specific components that we have found to work well. If you have
any questions, please email securedrop@freedom.press.

Required Hardware
-----------------

Servers
~~~~~~~

These are the core components of a SecureDrop instance.

-  **Application Server**: 1 physical server to run the SecureDrop web
   services.
-  **Monitor Server**: 1 physical server which monitors activity on the
   *Application Server* and sends email notifications to an
   administrator.
-  **Network Firewall**: 1 physical computer that is used as a dedicated
   firewall for the SecureDrop servers.

.. warning:: We are often asked if it is acceptable to run SecureDrop
	     on cloud servers (e.g. Amazon EC2, DigitalOcean, etc.)
	     instead of on dedicated hardware. This request is
	     generally motivated by a desire for cost savings and
	     convenience; however, cloud servers are trivially
	     accessible and manipulable by the provider that operates
	     them. In the context of SecureDrop, this means that the
	     provider could access extremely sensitive information,
	     such as the plaintext of submissions or the encryption
	     keys used to identify and access the Tor Hidden Services.

	     One of the core goals of SecureDrop is to avoid the
	     potential compromise of sources through the compromise of
	     third party communications providers. Therefore, we
	     consider the use of virtualization for production
	     instances of SecureDrop to be an unacceptable compromise
	     and do not support it. While it is technically possible
	     to modify SecureDrop's automated installation process to
	     work on virtualized servers (for example, we do so to
	     support our CI pipeline), doing so in order to run it on
	     cloud servers is at your own risk and without our support
	     or consent.

Workstations
~~~~~~~~~~~~

These components are necessary to do the initial installation of
SecureDrop and to process submissions using the airgapped workflow.

-  **Secure Viewing Station (SVS)**: 1 physical computer used as an
   airgap to decrypt and view submissions retrieved from the
   **Application Server**.

   -  The chosen hardware should be solely used for this purpose and
      should have any wireless networking hardware removed before use.

-  **Admin/Journalist Workstation(s)**: *At least 1* physical computer
   that is used as a workstation for SecureDrop admins and/or
   journalists.

   -  Each Admin and Journalist will have their own bootable Tails USB
      with an encrypted persistent partition that they will use to
      access SecureDrop. You will need at least one *workstation* to
      boot the Tails USBs, and may need more depending on: the number of
      admins/journalists you wish to grant access to SecureDrop, whether
      they can share the same workstation due to availability
      requirements, geographic distribution, etc.

-  **USB drive(s)**: *At least 2* USB drives to use as a bootable Tails
   USB for the **SVS** and the **Admin Tails**/**Journalist Tails**.

   -  If only one person is maintaining the system, you may use the same
      Tails instance as both the Admin Tails and the Journalist Tails;
      otherwise, we recommend buying 1 drive for each admin and each
      journalist.
   -  We also recommend buying two additional USBs to use as bootable
      backups of the **SVS** and **Admin Tails**.

-  **Two-factor authenticator**: Two-factor authentication is used when
   connecting to different parts of the SecureDrop system. Each admin
   and each journalist needs a two-factor authenticator. We currently
   support two options for two-factor authentication:

   -  Your existing smartphone with an app that computes TOTP codes
      (e.g. `Google
      Authenticator <https://support.google.com/accounts/answer/1066447?hl=en>`__)
   -  A dedicated hardware dongle that computes HOTP codes (e.g. a
      `YubiKey <https://www.yubico.com/products/yubikey-hardware/yubikey/>`__).

-  **Transfer Device(s)**: You need a mechanism to transfer encrypted
   submissions from the **Journalist Workstation** to the **SVS** to
   decrypt and view them. The most common transfer devices are DVD/CD-R
   discs and USB drives.

   -  From a security perspective, it is preferable to use write-once
      media such as DVD/CD-R discs because it eliminates the risk of
      exfiltration by malware that persists on the Transfer Device (e.g.
      `BadUSB <https://srlabs.de/badusb/>`__).
   -  On the other hand, using write-once media to transfer data is
      typically inconvenient and time-consuming. You should consider
      your threat model and choose your transfer device accordingly.

-  **Monitor, Keyboard, Mouse**: You will need these to do the initial
   installation of Ubuntu on the Application and Monitor servers.

   -  Depending on your setup, you may also need these to work on the
      **SVS**.

.. note:: If you cannot afford to purchase new hardware for your
	  SecureDrop instance, we encourage you to consider
	  re-purposing existing hardware to use with SecureDrop. If
	  you are comfortable working with hardware, this is a great
	  way to set up a SecureDrop instance for cheap.

	  Since SecureDrop's throughput is significantly limited by
	  the use of Tor for all connections, there is no need to use
	  top of the line hardware for any of the servers or the
	  firewall. In our experience, relatively recent recycled Dell
	  desktops or servers are adequate for the SecureDrop servers,
	  and recycled Thinkpad laptops work well for the
	  Admin/Journalist workstations.

	  If you choose to use recycled hardware, you should of course
	  consider whether or not it is trustworthy; making that
	  determination is outside the scope of this document.

Optional Hardware
-----------------

This hardware is not *required* to run a SecureDrop instance, but most
of it is still recommended.

-  **Offline Printer**: It is often useful to print submissions from the
   **SVS** for review and annotation.

   -  To maintain the integrity of the airgap, this printer should be
      dedicated to use with the SVS, connected via a wired connection,
      and should not have any wireless communication capabilities.

-  **Offline Storage**: The **SVS** is booted from a Tails USB drive,
   which has an encrypted persistent volume but typically has a fairly
   limited storage capacity since it's just a USB drive. For
   installations that expect to receive a large volume of submissions,
   we recommend buying an external hard drive that can be encrypted and
   used to store submissions that have been been transferred from the
   **Application Server** to the **SVS**.
-  **Backup storage**: It's useful to run periodic backups of the
   servers in case of failure. We recommend buying an external hard
   drive that can be encrypted and used to store server backups.

   -  Since this drive will be connected to the **Admin Workstation** to
      perform backups, it should *not* be the same drive used for
      **Offline Storage**.

-  **Network Switch**: If your firewall has fewer than **four** NIC's,
   you will need an additional Ethernet switch to perform installation
   and maintenance tasks with the Admin Workstation. This switch is
   generally useful because it allows you to connect the **Admin
   Workstation** to your firewall's LAN port without taking down either
   of the SecureDrop servers.

Specific Hardware Recommendations
---------------------------------

Application/Monitor Servers
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Intel NUC (Next Unit of Computing) is a capable, cheap, quiet, and
low-powered device that can be used for the SecureDrop servers. There
are a `variety of
models <https://www-ssl.intel.com/content/www/us/en/nuc/products-overview.html>`__
to choose from. We recommend the
`D54250WYK <https://www-ssl.intel.com/content/www/us/en/nuc/nuc-kit-d54250wyk.html>`__
because it has a mid-range CPU (Intel i5), the common Mini DisplayPort
connector for the monitor, and USB 3.0 ports for faster OS installation
and data transfer.

Conveniently (for the paranoid), it supports wireless networking (Wifi
and Bluetooth) through *optional* expansion cards not included by
default - which means you don't have to spend time ripping out the
wireless hardware before beginning the installation.

.. note:: If you purchase the NUC from `Amazon
	  <http://www.amazon.com/Intel-D54250WYK-DisplayPort-Graphics-i5-4250U/dp/B00F3F38O2/>`__,
	  make sure you click "With Powercord" to have one included in
	  the package.

The NUCs come as kits, and some assembly is required. You will
need to purchase the RAM and hard drive separately for each NUC and
insert the cards into the NUC before it can be used. We recommend:

-  2 `240 GB SSDs <http://www.amazon.com/dp/B00BQ8RKT4/>`__
-  A `4 GB (4GBx2) memory
   kit <http://www.amazon.com/Crucial-PC3-12800-204-Pin-Notebook-CT2CP25664BF160B/dp/B005MWQ6WC/>`__

   -  You can put one 4GB memory stick in each of the servers.

.. note:: The D54250WYK has recently been `EOL'ed by Intel
	  <http://ark.intel.com/products/series/70407/Intel-NUC-Boards-and-Kits>`__.
	  Availability and prices may be subject to change. We are
	  working on analyzing alternative recommendations, but there
	  are no immediately obvious alternatives that share the
	  benefits of the D54250WYK (primarily, the lack of integrated
	  wireless networking hardware).

.. note:: An earlier release of SecureDrop (0.2.1) was based on Ubuntu
	  12.04.1 (precise). We encountered issues installing this
	  version of Ubuntu on some types of Intel NUCs. The problem
	  manifested after installing Ubuntu on the NUC. The
	  installation would complete, but rebooting after
	  installation would not succeed.

	  We have not encountered this or any similar problems in
	  testing the current release series (0.3.x) with the Intel
	  NUCs. Since 0.3 is based on Ubuntu 14.04.1 (trusty), we
	  believe the issue has been resolved in the newer release of
	  Ubuntu.

	  If you do encounter issues booting Ubuntu on the NUCs, try
	  updating the BIOS according to `these instructions
	  <http://arstechnica.com/gadgets/2014/02/new-intel-nuc-bios-update-fixes-steamos-other-linux-booting-problems/>`__.

Secure Viewing Station (SVS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The *Secure Viewing Station* is a machine that is kept offline and only
ever used together with the Tails operating system. This machine will be
used to generate the GPG keys used by SecureDrop to encrypt submissions,
as well as decrypt and view submissions. Since this machine will never
touch the Internet or run an operating system other than Tails, it does
not need a hard drive or network device; in fact, we recommend removing
these components if they are already present.

One option is to buy a Linux-compatible laptop such as a `Lenovo
Thinkpad <http://shop.lenovo.com/us/en/laptops/thinkpad/t-series/t540p/>`__.
You can also repurpose an old laptop if you have one available.

Another option is to buy an `Intel NUC
D54250WYK <http://www.amazon.com/Intel-D54250WYK-DisplayPort-Graphics-i5-4250U/dp/B00F3F38O2/>`__
(same model as the servers) with a power cord and `4 GB of
memory <http://www.amazon.com/Crucial-PC3-12800-204-Pin-Notebook-CT2CP25664BF160B/dp/B005MWQ6WC/>`__,
but note that you will also need to get a monitor and a wired keyboard
and mouse. It does not come with a hard drive or wireless networking
hardware by default, so you will not need to remove these components
before using it. However, we do recommend taping over the IR receiver
with some opaque masking tape.

Note that if you do want to use a NUC for the SVS, you *should not* use
any of the new generation of NUCs, which have names starting with "NUC5"
(e.g.
`NUC5i5RYK <https://www-ssl.intel.com/content/www/us/en/nuc/nuc-kit-nuc5i5ryk.html>`__..
These NUCs have wireless networking built into the motherboard, and it
is impossible to physically remove.

A note about Hi-DPI displays
''''''''''''''''''''''''''''

The current version of Tails (1.5.1) is based on Debian 7 ("Wheezy"),
which does not have good support for Hi-DPI displays. Examples of
laptops that use this type of display are MacBook/MacBook Pros with the
Retina display, or the Dell Precision M3800. We *do not recommend* using
such laptops with any of the components that run Tails (the SVS, Admin
Workstation, and Journalist Workstation). While it is possible to use
them, the screen resolution will not be scaled correctly. Typically,
this means everything will be really tiny, bordering on unreadable.

Until the upcoming version of Tails (2.x, based on Debian 8) comes out,
use standard resolution displays with Tails.

Tails USBs
~~~~~~~~~~

We *strongly recommend* getting USB 3.0-compatible drives to run Tails
from. The transfer speeds are significantly faster than USB 2.0, which
means a live operating system booting from one will be much faster and
more responsive.

You will need *at least* an 8GB drive to run Tails with an encrypted
persistent partition. We recommend getting something in the 16-64GB
range so you can handle large amounts of submissions without hassle.
Anything more than that is probably overkill.

Other than that, the choice of USB drive depends on capacity, form
factor, cost, and a host of other factors. One option that we like is
the `Leef
Supra <http://www.amazon.com/Leef-Supra-PrimeGrade-Memory-Silver/dp/B00FWQMKA0>`__.

Transfer Device
~~~~~~~~~~~~~~~

If you are using USBs for the transfer device, the same general
recommendations for the Tails USBs also apply. One thing to consider is
that you are going to have *a lot* of USB drives to keep track of, so
you should consider how you will label or identify them and buy drives
accordingly. Drives that are physically larger are often easier to label
(e.g. with tape or a label from a labelmaker).

If you are using DVD/CD-R's for the transfer device, you will need *two*
DVD/CD writers: one for burning DVDs from the **Journalist
Workstation**, and one for reading the burned DVDs on the **SVS**. We
recommend using two separate drives instead of sharing the same drive to
avoid the potential risk of malware exfiltrating data by compromising
the drive's firmware. We've found the DVD/CD writers from Samsung and LG
to work reasonably well, you can find some examples
`here <http://www.newegg.com/External-CD-DVD-Blu-Ray-Drives/SubCategory/ID-420>`__.

Finally, you will need a stack of blank DVD/CD-R's, which you can buy
anywhere.

Network Firewall
~~~~~~~~~~~~~~~~

We recommend the `pfSense
SG-2440 <http://store.pfsense.org/SG-2440/>`__.

Network Switch
~~~~~~~~~~~~~~

This is optional, for people who are using a firewall with less than 4
ports (the recommended firewall has 4 ports). Any old switch with more
than 3 ports will do, such as the `5-port Netgear ProSafe Ethernet
Switch <http://www.amazon.com/NETGEAR-ProSafe-Gigabit-Ethernet-Desktop/dp/B0000BVYT3/>`__.

Printers
~~~~~~~~

Careful consideration should be given to the printer used with the SVS.
Most printers today have wireless functionality (WiFi or Bluetooth
connectivity) which should be **avoided** because it could be used to
compromise the airgap.

Unfortunately, it is difficult to find printers that work with Tails,
and it is increasingly difficult to find non-wireless printers at all.
To assist you, we have compiled the following partial list of
airgap-safe printers that have been tested and are known to work with
Tails:

+-------------------------+----------------+------------------+--------------------+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Model                   | Testing Date   | Tails Versions   | Price (new)        | Price (used)       | Notes                                                                                                                                                       |
+=========================+================+==================+====================+====================+=============================================================================================================================================================+
| HP LaserJet 400 M401n   | 06/2015        | 1.4              | $178.60 (Amazon)   | $115.00 (Amazon)   | Monochrome laser printer. Heavy (10 lbs.) When adding the printer in Tails, you need to set "Make and model" to "HP LaserJet 400 CUPS+Gutenprint v5.2.9".   |
+-------------------------+----------------+------------------+--------------------+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+
| HP Deskjet 6940         | 04/2015        | 1.3.2            | $639.99 (Amazon)   | $196.99 (Amazon)   | Monochrome Inkjet printer                                                                                                                                   |
+-------------------------+----------------+------------------+--------------------+--------------------+-------------------------------------------------------------------------------------------------------------------------------------------------------------+

If you know of another model of printer that fits our requirements and
works with Tails, please submit a pull request to add it to this list.

Monitor, Keyboard, Mouse
~~~~~~~~~~~~~~~~~~~~~~~~

We don't have anything specific to recommend when it comes to displays.
You should make sure you know what monitor cable you need for the
servers, since you will need to connect them to a monitor to do the
initial Ubuntu installation.

You should use a wired (USB) keyboard and mouse, not wireless.
