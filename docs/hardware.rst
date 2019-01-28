.. _hardware_guide:

Hardware
========

This document outlines the required hardware components necessary to
successfully install and operate a SecureDrop instance, and recommends
some specific components that we have found to work well. If you have
any questions, please email securedrop@freedom.press.

Hardware Overview
-----------------

For an installation of SecureDrop, you must acquire:

.. include:: includes/pre-install-hardware.txt

In the sections that follow, we provide additional details on each item.

.. _Hardware Recommendations:

Required Hardware
-----------------

Servers
^^^^^^^

These are the core components of a SecureDrop instance.

* *Application Server*: 1 physical server to run the SecureDrop web services.

* *Monitor Server*: 1 physical server which monitors activity on the
  *Application Server* and sends email notifications to an admin.

* *Network Firewall*: 1 physical computer that is used as a dedicated firewall
  for the SecureDrop servers.

An acceptable alternative that requires more technical expertise is
to :doc:`configure an existing hardware firewall <network_firewall>`.

We are often asked if it is acceptable to run SecureDrop on
cloud servers (e.g. Amazon EC2, DigitalOcean, etc.) or on dedicated
servers in third-party datacenters instead of on dedicated hardware
hosted in the organization. This request is generally motivated by a
desire for cost savings and/or convenience. However: we consider it
**critical** to have dedicated physical machines hosted within the
organization for both technical and legal reasons:

* While the documents are stored encrypted at rest (via PGP) on the
  SecureDrop *Application Server*, the documents hit server memory
  unencrypted (unless the source used the GPG key provided to
  encrypt the documents first before submitting), and are then
  encrypted in server memory before being written to disk. If the
  machines are compromised then the security of source material
  uploaded from that point on cannot be assured. The machines are
  hardened to prevent compromise for this reason. However, if an
  attacker has physical access to the servers either because the
  dedicated servers are located in a datacenter or because the
  servers are not dedicated and may have another virtual machine
  co-located on the same server, then the attacker may be able to
  compromise the machines. In addition, cloud servers are trivially
  accessible and manipulable by the provider that operates them. In
  the context of SecureDrop, this means that the provider could
  access extremely sensitive information, such as the plaintext of
  submissions or the encryption keys used to identify and access
  the Tor Hidden Services.

* In addition, attackers with legal authority such as law
  enforcement agencies may (depending on the jurisdiction) be able
  to compel physical access, potentially with a gag order attached,
  meaning that the third party hosting your servers or VMs may be
  legally unable to tell you that law enforcement has been given
  access to your SecureDrop servers.

One of the core goals of SecureDrop is to avoid the potential
compromise of sources through the compromise of third-party
communications providers. Therefore, we consider the use of
virtualization for production instances of SecureDrop to be an
unacceptable compromise and do not support it. Instead, dedicated
servers should be hosted in a physically secure location in the
organization itself. While it is technically possible to modify
SecureDrop's automated installation process to work on virtualized
servers (for example, we do so to support our CI pipeline), doing so
in order to run it on cloud servers is at your own risk and without
our support or consent.

Workstations
^^^^^^^^^^^^
.. note:: SecureDrop depends on the Tails operating system for its bootable USB
  drives.  Since the release of Tails 3.0, 32-bit computers are no longer
  supported.

  To see if you have a 64-bit machine, run ``uname -m`` from a terminal.  If you
  see ``x86_64``, then Tails should work on your current machine.  If, on the
  other hand, you see ``i686``, your current machine will not work with Tails
  3.0 or greater.  For more details, see `the Tails website
  <https://tails.boum.org/news/version_3.0/index.en.html#index3h3>`_.

These components are necessary to do the initial installation of
SecureDrop and to process submissions using the air-gapped workflow.

*Secure Viewing Station* (SVS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1 physical computer used as an air-gap to decrypt and view submissions retrieved
from the *Application Server*.

The chosen hardware should be solely used for this purpose and should have any
wireless networking hardware removed before use.

Admin/Journalist Workstation(s)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*At least 1* physical computer that is used as a workstation for SecureDrop
admins and/or journalists.

Each Admin and Journalist will have their own bootable Tails USB with an
encrypted persistent partition that they will use to access SecureDrop. You will
need at least one *workstation* to boot the Tails USBs, and may need more
depending on: the number of admins/journalists you wish to grant access to
SecureDrop, whether they can share the same workstation due to availability
requirements, geographic distribution, etc.

USB Drive(s)
~~~~~~~~~~~~

*At least 2* USB drives to use as a bootable Tails USB for the *SVS* and the
*Admin Workstation*/*Journalist Workstation*.

If only one person is maintaining the system, you may use the same Tails
instance as both the *Admin Workstation* and the *Journalist Workstation*; otherwise, we
recommend buying 1 drive for each admin and each journalist.

We also recommend buying two additional USBs to use as bootable backups of the
*SVS* and *Admin Workstation*.

**Two-factor authenticator**: Two-factor authentication is used when connecting
to different parts of the SecureDrop system. Each admin and each journalist
needs a two-factor authenticator. We currently support two options for
two-factor authentication:

* Your existing smartphone with an app that computes TOTP codes
  (e.g. FreeOTP `for Android <https://play.google.com/store/apps/details?id=org.fedorahosted.freeotp>`__ and `for iOS <https://itunes.apple.com/us/app/freeotp-authenticator/id872559395>`__).

* A dedicated hardware dongle that computes HOTP codes (e.g. a
  `YubiKey <https://www.yubico.com/products/yubikey-hardware/yubikey/>`__).

.. include:: includes/otp-app.txt

**Transfer Device(s)**: You need a mechanism to transfer encrypted submissions
from the *Journalist Workstation* to the *SVS* to decrypt and view them. The
most common transfer devices are DVD/CD-R discs and USB drives.

From a security perspective, it is preferable to use write-once media such as
DVD/CD-R discs because it eliminates the risk of exfiltration by malware that
persists on the Transfer Device (e.g. `BadUSB <https://srlabs.de/badusb/>`__).

On the other hand, using write-once media to transfer data is typically
inconvenient and time-consuming. You should consider your threat model and
choose your transfer device accordingly.

**Monitor, Keyboard, Mouse**: You will need these to do the initial installation
of Ubuntu on the *Application* and *Monitor Servers*.

Depending on your setup, you may also need these to work on the *SVS*.

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
	  and recycled ThinkPad laptops work well for the
	  *Admin Workstation*/*Journalist Workstation*.

	  If you choose to use recycled hardware, you should of course
	  consider whether or not it is trustworthy; making that
	  determination is outside the scope of this document.

Optional Hardware
-----------------

This hardware is not *required* to run a SecureDrop instance, but most
of it is still recommended.

Offline Printer
^^^^^^^^^^^^^^^

It is often useful to print submissions from the *Secure Viewing Station* for
review and annotation.

.. warning:: To maintain the integrity of the air-gap, this printer should be
             dedicated to use with the *Secure Viewing Station*, connected via
             a wired connection, and should not have any wireless communication
             capabilities.

Offline Storage
^^^^^^^^^^^^^^^

The *SVS* is booted from a Tails USB drive, which has an encrypted persistent
volume but typically has a fairly limited storage capacity since it's just a USB
drive. For installations that expect to receive a large volume of submissions,
we recommend buying an external hard drive that can be encrypted and used to
store submissions that have been transferred from the *Application Server* to
the *SVS*.

Backup Storage
^^^^^^^^^^^^^^

It's useful to run periodic backups of the servers in case of failure. We
recommend buying an external hard drive that can be encrypted and used to store
server backups.

.. warning:: Since this drive will be connected to the *Admin Workstation* to
             perform backups, it should *not* be the same drive used for
             *Offline Storage*.

Network Switch
^^^^^^^^^^^^^^

If your firewall has fewer than **four** NICs, you will need an additional
Ethernet switch to perform installation and maintenance tasks with the *Admin
Workstation*. This switch is generally useful because it allows you to connect
the *Admin Workstation* to your firewall's LAN port without taking down either
of the SecureDrop servers.

Labeling Equipment
^^^^^^^^^^^^^^^^^^

As you have probably noticed by now, a SecureDrop installation has a plethora of
components. Some of these components can be hard to tell apart; for example, if
you buy 3 of the same brand of USB sticks to use for the Admin Workstation,
Journalist Workstation, and Secure Viewing Station, they will be
indistinguishable from each other unless you label them. We recommend buying
some labeling equipment up front so you can label each component as you
provision it during the installation process.

There is a multitude of options for labeling equipment. We've had good results
with small portable labelmakers, such as the `Brother P-Touch PT-210`_ or the
`Epson LabelWorks LW-300`_. We like them because they produce crisp,
easy-to-read labels, and it's easy to customize the size of the label's text,
which is great for clearly labeling both large components (like computers) and
small components (like USB sticks).

.. _`Brother P-Touch PT-210`: https://www.amazon.com/Brother-P-Touch-PT-D210-Label-Maker/dp/B01BTMEKRQ/ref=zg_bs_226180_1
.. _`Epson LabelWorks LW-300`: https://www.amazon.com/Epson-LabelWorks-LW-300-Label-Maker/dp/B005J7Y6HW/ref=pd_sbs_229_7

If you do not have a label maker available but have an inkjet printer available to you, it may
also be possible to print and cut out labels using adhesive-backed paper and some scissors. These are some labels designed by our team which may be used for labeling:

-  :download:`Admin Workstation Label <./images/labels/admin_workstation.png>`
-  :download:`Journalist Workstation Label <images/labels/journalist_workstation.png>`
-  :download:`Secure Viewing Station Label <images/labels/secure_viewing_station_offline_warning.png>`
-  :download:`Firewall Label <images/labels/firewall.png>`
-  :download:`Application Server Label <images/labels/app_server.png>`
-  :download:`Monitor Server Label <images/labels/mon_server.png>`
-  :download:`Admin TAILS USB Drive Label <images/labels/usb_admin.png>`
-  :download:`Journalist TAILS USB Drive Label <images/labels/usb_journalist.png>`
-  :download:`Secure Viewing Station TAILS USB Drive Label <images/labels/usb_svs.png>`
-  :download:`File Transfer USB Drive Label <images/labels/usb_file_transfer.png>`

.. _Specific Hardware Recommendations:

Specific Hardware Recommendations
---------------------------------

Application and Monitor Servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We currently recommend the Intel NUC for SecureDrop servers.

.. note:: If using non-recommended hardware, ensure you remove as much
    extraneous hardware as physically possible from your servers. This
    could include: speakers, cameras, microphones, fingerprint readers,
    wireless, and Bluetooth cards.

Intel NUC
~~~~~~~~~

The Intel NUC (Next Unit of Computing) is an inexpensive, quiet, low-power
device that can be used for the SecureDrop servers. There are a
`variety of models <https://www-ssl.intel.com/content/www/us/en/nuc/products-overview.html>`__
to choose from. We recommend the
`NUC5i5MYHE <https://www.intel.com/content/www/us/en/products/boards-kits/nuc/kits/nuc5i5myhe.html>`__
because it has a mid-range CPU (the 5th generation Intel i5), a Mini
DisplayPort port for a monitor, and two USB 3.0 ports for faster OS
installation and data transfer.

The NUC5i5MYHE supports wireless through *optionally-purchased* expansion cards.
This means the wireless components aren't soldered on which would make them
nearly impossible to remove without inflicting damage to the NUC. This optional
support is preferable, since you want neither WiFi nor Bluetooth.

The NUCs come as kits, and some assembly is required. You will need to purchase
the RAM and hard drive separately for each NUC and insert both into the NUC
before it can be used. We recommend:

-  2x 240 GB SSDs (2.5")
-  1x memory kit of 2x4GB sticks
   -  You can put one 4GB memory stick in each of the servers.

.. note:: The D54250WYK we previously recommended has now entered `End of Life`
    and `End of Interactive Support` statuses. If you're currently using this
    model for your SecureDrop setup, and need hardware support, you'll need to
    consult the `support community <https://communities.intel.com/community/tech/nuc>`__ forum.

.. note:: If you encounter issues booting Ubuntu on the NUCs, try
	  updating the BIOS according to `these instructions
	  <http://arstechnica.com/gadgets/2014/02/new-intel-nuc-bios-update-fixes-steamos-other-linux-booting-problems/>`__.

.. caution:: Some older NUC BIOS versions will cause the server to `brick itself <https://communities.intel.com/message/359708>`__ if the device
    attempts to suspend. This has `since been fixed <https://communities.intel.com/message/432692#432692>`__
    in a BIOS update. See these `release notes <https://downloadmirror.intel.com/26263/eng/RY_0359_ReleaseNotes.pdf>`__ (PDF) for more details.

Later NUC revisions (the NUC7 and NUC8 series) typically include onboard WiFi
and Bluetooth, and may use an Ethernet chipset not supported by the default Ubuntu 
14.04.5 kernel. We are investigating workarounds for both issues. If you are 
having trouble sourcing the NUC5i5MYHE, please `contact us <https://securedrop.org/help/>`__
for more information on how to safely configure and use more recent NUCs.  

Mac Minis
~~~~~~~~~

.. caution:: We have previously recommended the 2014 Apple Mac Minis (part
  number MGEM2) for installing SecureDrop. The 2018 Apple Mac Mini (part number
  MRTR2 or MRTT2) is not a viable candidate for installing SecureDrop, due to
  hardware support issues. The instructions below apply if you want to
  (re-)install SecureDrop on the 2014 version.


The 2014 Apple Mac Minis have removable wireless cards that you should remove.
This requires a screwdriver for non-standard
`TR6 Torx security screws <https://www.amazon.com/Mini-Torx-Security-Screwdriver-Tool/dp/B01BG8P2Q6>`__.

However, on the first install of Ubuntu Server
the Mac Minis will not boot: this is a known and
`documented <https://nsrc.org/workshops/2015/nsrc-icann-dns-ttt-dubai/raw-attachment/wiki/Agenda/install-ubuntu-mac-mini.htm#your-mac-does-not-boot>`__
issue. The workaround requires a one-time modification after you
install Ubuntu but before you move on to
`install SecureDrop <https://docs.securedrop.org/en/stable/install.html>`__.
After Ubuntu is installed, for each Mac Mini you should:

#. Connect your Ubuntu installation media (USB drive or CD)
#. Boot your Mac Mini while holding down the **Option** key.
#. Select **EFI Boot** and select **Rescue a broken system** at the Ubuntu
   install screen.
#. Accept the default options for the install steps until you get to **Device to
   use as root file system**.
#. At the **Device to use as root file system** prompt, select
   ``/dev/mon-vg/root`` or ``/dev/app-vg/root`` for the monitor and application
   servers respectively.
#. Select to mount the separate ``/boot`` partition.
#. Select **Execute a shell in** ``/dev/mon-vg/root`` (or ``/dev/app-vg/root``)
   and select **Continue**.
#. You should now be at a rescue Linux shell. Type ``efibootmgr``, and you
   should see the following:

    .. code::

        BootCurrent: 0000
        Timeout: 5 seconds
        BootOrder: 0080
        Boot0000* ubuntu
        Boot0080* Mac OS X
        BootFFFF*

#. Type ``efibootmgr -o 00``.
#. Again type ``efibootmgr``. This time you should see the following:

    .. code::

        BootCurrent: 0000
        Timeout: 5 seconds
        BootOrder: 0000
        Boot0000* ubuntu
        Boot0080* Mac OS X
        BootFFFF*

#. Type ``exit``.
#. Select **Reboot the system** and remove the installation media.
   Your server should now boot to Ubuntu by default.

Journalist Workstation and Admin Workstation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Both the *Journalist Workstation* and the *Admin Workstation* must be compatible
with the Tails operating system. Compare any hardware you want to procure or
allocate for this purpose against the `list of known issues <https://tails.boum.org/support/known_issues/index.en.html>`__
maintained by the Tails project, but please be advised that the list is far
from exhaustive.

We advise against using Macs, as there are many Tails compatibility issues both
with older and with newer models. Instead, we recommend the
`ThinkPad T series <https://www3.lenovo.com/us/en/laptops/thinkpad/thinkpad-t-series/c/thinkpadt>`__,
and have had good experiences specifically with the T420 and T440. The
`ThinkWiki <https://www.thinkwiki.org/wiki/ThinkWiki>`__ is an excellent,
independently maintained resource for verifying general Linux compatibility of
almost any ThinkPad model.

For any Tails workstation, we recommend at least 8GB of RAM.

Secure Viewing Station (SVS)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The *Secure Viewing Station* is a machine that is kept offline and only
ever used together with the Tails operating system. This machine will be
used to generate the GPG keys used by SecureDrop to encrypt submissions,
as well as decrypt and view submissions. Since this machine will never
touch the Internet or run an operating system other than Tails, it does
not need a hard drive or network device; in fact, we recommend removing
these components if they are already present.

As with the workstations, one good option is to buy a Linux-compatible laptop
from the Lenovo ThinkPad T series. We have tested the T420 and successfully
removed the wireless components with ease. It's possible to re-purpose old
laptops from other manufacturers, as long as the wireless components are
removable.

Just as with the servers, you can also use an Intel NUC for the *SVS*. As noted
before, NUCs do not ship with a hard drive, and can be configured without any
wireless components, so you'll save time by not having to remove these, since
they won't be present. However, NUCs *do* contain an IR receiver, which we
recommend taping over with opaque masking tape.

If you choose to use an Intel NUC that differs from our recommended
model, make sure you use one that offers wireless as an **option**. If the model
is advertised as having "integrated wireless", such as the `NUC5i5RYK`, this
could mean it's built into the motherboard, making it physically irremovable, and
attempting to do so would risk damaging the unit; instead, look for attributes like
`M.2 22×30 slot and wireless antenna pre-assembled (for wireless card support)`,
as advertised by the `NUC5i5MYHE` that we recommend.

Tails USBs
^^^^^^^^^^

.. note:: Tails no longer supports 32-bit computers.
	Please see the note in the `Workstations`_ section for more details.

We *strongly recommend* getting USB 3.0-compatible drives to run Tails
from. The transfer speeds are significantly faster than USB 2.0, which
means a live operating system booting from one will be much faster and
more responsive.

You will need *at least* an 8GB drive to run Tails with an encrypted
persistent partition. We recommend getting something in the 16-64GB
range so you can handle large amounts of submissions without hassle.
Anything more than that is probably overkill.

Transfer Device
^^^^^^^^^^^^^^^

If you are using USBs for the transfer device, the same general
recommendations for the Tails USBs also apply. One thing to consider is
that you are going to have *a lot* of USB drives to keep track of, so
you should consider how you will label or identify them and buy drives
accordingly. Drives that are physically larger are often easier to label
(e.g. with tape, printed sticker or a label from a labelmaker).

If you are using DVD/CD-R's for the transfer device, you will need *two*
DVD/CD writers: one for burning DVDs from the *Journalist
Workstation*, and one for reading the burned DVDs on the *SVS*. We
recommend using two separate drives instead of sharing the same drive to
avoid the potential risk of malware exfiltrating data by compromising
the drive's firmware. We've found the DVD/CD writers from Samsung and LG
to work reasonably well, you can find some examples
`here <http://www.newegg.com/External-CD-DVD-Blu-Ray-Drives/SubCategory/ID-420>`__.

Finally, you will need a stack of blank DVD/CD-R's, which you can buy
anywhere.

Network Firewall
^^^^^^^^^^^^^^^^

We recommend the `pfSense SG-3100
<https://store.netgate.com/SG-3100.aspx>`__.

Network Switch
^^^^^^^^^^^^^^

This is optional, for people who are using a firewall with less than 4
ports (the recommended firewall has 4 ports). Any old switch with more
than 3 ports will do, such as the `5-port Netgear ProSafe Ethernet
Switch <http://www.amazon.com/NETGEAR-ProSafe-Gigabit-Ethernet-Desktop/dp/B0000BVYT3/>`__.
The SG-3100 sells with an internal switch on the LAN interface.

.. _printers_tested_by_fpf:

Printers
^^^^^^^^

Careful consideration should be given to the printer used with the *SVS*.
Most printers today have wireless functionality (WiFi or Bluetooth
connectivity) which should be **avoided** because it could be used to
compromise the air-gap.

Unfortunately, it is difficult to find printers that work with Tails,
and it is increasingly difficult to find non-wireless printers at all.
To assist you, we have compiled the following partial list of
air-gap-safe printers that have been tested and are known to work with
Tails:

+-------------------------+--------------+----------------+--------------------+
| Printer Model           | Testing Date | Tails Versions | Printer Type       |
+=========================+==============+================+====================+
| HP DeskJet F4200        | 06/2017      | 3.0            | Color Inkjet       |
+-------------------------+--------------+----------------+--------------------+
| HP DeskJet 1112         | 06/2017      | 3.0            | Color Inkjet       |
+-------------------------+--------------+----------------+--------------------+
| HP DeskJet 1110         | 08/2017      | 3.1            | Color Inkjet       |
+-------------------------+--------------+----------------+--------------------+
| HP LaserJet 400 M401n   | 06/2015      | 1.4            | Monochrome Laser   |
+-------------------------+--------------+----------------+--------------------+
| HP DeskJet 6940         | 04/2015      | 1.3.2          | Monochrome Injket  |
+-------------------------+--------------+----------------+--------------------+

.. note:: We've documented both the HP DeskJet F4200 and HP LaserJet 400 M401n
          with screenshots of the installation process, in our section on
          :ref:`printer_setup_in_tails`. While the F4200 installed
          automatically, the 400 M401n required that we set "Make and model" to
          "HP LaserJet 400 CUPS+Gutenprint v5.2.9" when manually configuring the
          drivers.

If you know of another model of printer that fits our requirements and
works with Tails, please submit a pull request to add it to this list.

Monitor, Keyboard, Mouse
^^^^^^^^^^^^^^^^^^^^^^^^

We don't have anything specific to recommend when it comes to displays.
You should make sure you know what monitor cable you need for the
servers, since you will need to connect them to a monitor to do the
initial Ubuntu installation.

You should use a wired (USB) keyboard and mouse, not wireless.
