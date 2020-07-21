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

.. include:: includes/pre-install-hardware-required.txt

Additionally, you may want to consider the following purchases:

.. include:: includes/pre-install-hardware-optional.txt

In the sections that follow, we provide additional details on most of these
items.

.. tip::

    While a printer is not required, we highly recommend it. Printing documents
    is generally far safer than copying them in digital form. See our
    :ref:`guide to working with documents <working_with_documents>` for more information.

Advice for users on a tight budget
----------------------------------
If you cannot afford to purchase new hardware for your
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

Please note that very old laptops or desktops may not work for the workstations.
Since the release of Tails 3.0, 32-bit computers are no longer supported.

If you choose to use recycled hardware, you should of course
consider whether or not it is trustworthy; making that
determination is outside the scope of this document.

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
  the onion services.

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
^^^^^^^^^^^^

*At least 2* USB drives to use as a bootable Tails USB for the *SVS* and the
*Admin Workstation*/*Journalist Workstation*.

If only one person is maintaining the system, you may use the same Tails
instance as both the *Admin Workstation* and the *Journalist Workstation*; otherwise, we
recommend buying 1 drive for each admin and each journalist.

We also recommend buying an additional USB drive for making regular backups of
your Tails workstations.

One thing to consider is that you are going to have *a lot* of USB drives to
keep track of, so you should consider how you will label or identify them and
buy drives accordingly. Drives that are physically larger are often easier to
label (e.g. with tape, printed sticker or a label from a labelmaker).

Two-factor Device
^^^^^^^^^^^^^^^^^
Two-factor authentication is used when connecting to different parts of the
SecureDrop system. Each admin and each journalist needs a two-factor
device. We currently support two options for two-factor authentication:

* Your existing smartphone with an app that computes TOTP codes
  (e.g. FreeOTP `for Android <https://play.google.com/store/apps/details?id=org.fedorahosted.freeotp>`__ and `for iOS <https://itunes.apple.com/us/app/freeotp-authenticator/id872559395>`__).

* A dedicated hardware dongle that computes HOTP codes (e.g. a
  `YubiKey <https://www.yubico.com/products/yubikey-hardware/yubikey/>`__).

.. include:: includes/otp-app.txt

Transfer Device(s) and Export Device(s)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Journalists need physical media (known as the *Transfer Device*) to transfer
encrypted submissions from the *Journalist Workstation* to the
*Secure Viewing Station*, to decrypt and view them there. If they deem a
submission to be newsworthy, they may need physical media (known as the
*Export Device*) to copy it to their everyday workstation.

Our standard recommendation is to use USB drives, in combination with
volume-level encryption and careful data hygiene. Our documentation, including
the :doc:`journalist guide <journalist>`, is based on this approach. We also
urge the use of a secure printer or similar analog conversions to export
documents from the *Secure Viewing Station*, whenever possible.

You may want to consider enforcing write protection on USB drives when only read
access is needed, or you may want to implement a workflow based on CD-Rs or
DVD-Rs instead. We encourage you to evaluate these options in the context of
your own threat model.

Please find some notes regarding each of these methods below, and see our
recommendations in the :doc:`setup guide <set_up_transfer_and_export_device>`
for additional background.

USB drives
~~~~~~~~~~
We recommend using one or multiple designated USB drives as the *Transfer
Device(s)*, and one or multiple designated USB drives as the *Export
Device(s)*. Whether one or multiple drives are appropriate depends on the number
of journalists accessing the system, and on whether the team is distributed
or not.

Our documentation explains how the *Transfer Device* can be encrypted using
LUKS, and how the *Export Device* can be encrypted using VeraCrypt (which works
across platforms). We have not evaluated hardware-based encryption options; if
you do select a hardware solution, make sure that both devices work in Tails,
and that the *Export Device* also works on the operating system(s) used by
journalists accessing the *Secure Viewing Station*.

USB drives with write protection (optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When it is consistently applied and correctly implemented in hardware, write
protection can prevent the spread of malware from the computers used to read
files stored on a *Transfer Device* or an *Export Device*.

It is especially advisable to enable write protection before attaching an
*Export Device* to an everyday workstation that lacks the security protections
of the Tails operating system. For defense in depth, you may also want to
enable write protection before attaching a *Transfer Device* to the
*Secure Viewing Station*.

The two main options to achieve write protection of USB drives are:

- drives with a built-in physical write protection switch
- a separate USB write blocker device as used in forensic applications.

DVD-Rs or CD-Rs
~~~~~~~~~~~~~~~
Single-use, write-once media can be used to realize a transfer and export
workflow that is always one-directional: files are transferred to the *Secure
Viewing Station* and the media used to do so are destroyed; files are exported
from the *Secure Viewing Station* and the media used to do so are destroyed.

If you want to realize such a workflow, we recommend purchasing separate drives
for each computer that will write to or read from the media, to minimize the
risks from malware compromising any one drive's firmware.

You will also need a stack of blank DVD/CD-Rs, which you can buy anywhere, and a
method to securely destroy media after use. Depending on your threat model, this
can be very expensive; a cheap shredder can be purchased for less than $50,
while shredders designed for use in Sensitive Compartmented Information
Facilities (SCIFs) sell for as much as $3,000.

Monitor, Keyboard, Mouse
^^^^^^^^^^^^^^^^^^^^^^^^
You will need these to do the initial installation of Ubuntu on the
*Application* and *Monitor Servers*.

Depending on your setup, you may also need these to work on the *SVS*.

Optional Hardware
-----------------

This hardware is not *required* to run a SecureDrop instance, but most
of it is still recommended.

Offline Printer
^^^^^^^^^^^^^^^

We highly recommend purchasing a printer for your *Secure Viewing Station* and
using it as the preferred method to make copies of documents received via
SecureDrop.

By printing a submission, even a non-technical user can effectively mitigate
many of the complex risks associated with malware or hidden metadata embedded in
files received via SecureDrop. Your organization may also already have robust
procedures in place for destroying sensitive printed documents.

.. important:: To maintain the integrity of the air-gap, this printer should be
               dedicated to use with the *Secure Viewing Station*, connected via
               a wired connection, and should not have any wireless communication
               capabilities.

While printing is notable for what it strips away, it is also important to
remember what it preserves: QR codes or links that journalists may scan or type
in; `printer tracking information <https://www.eff.org/issues/printers>`__
included in a scanned document; other visually encoded information. See the
:ref:`malware_risks` section in the Journalist Guide for further guidance on
this subject.

Offline Storage
^^^^^^^^^^^^^^^

The *SVS* is booted from a Tails USB drive, which has an encrypted persistent
volume but typically has a fairly limited storage capacity since it's just a USB
drive. For installations that expect to receive a large volume of submissions,
we recommend buying an external hard drive that can be used to store submissions
that have been transferred from the *Application Server* to the *SVS*.

.. include:: includes/encrypting-drives.txt

Backup Storage
^^^^^^^^^^^^^^

It's useful to run periodic backups of the servers in case of failure. We
recommend buying an external hard drive to store server backups.

Because this drive will be connected to the *Admin Workstation* to perform
backups, it should *not* be the same drive used for *Offline Storage*.

.. include:: includes/encrypting-drives.txt

Network Switch
^^^^^^^^^^^^^^
If you follow our firewall recommendations, you do not need to purchase a
switch.

If you use a firewall with fewer than four ports, you will need an additional
Ethernet switch to perform installation and maintenance tasks with the
*Admin Workstation* without disconnecting one of your servers.

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

.. _nuc7_recommendation:

Intel 7th-gen NUC
~~~~~~~~~~~~~~~~~

The Intel NUC (Next Unit of Computing) is an inexpensive, quiet, low-power
device that can be used for the SecureDrop servers. There are a
`variety of models <https://www.intel.com/content/www/us/en/products/boards-kits/nuc.html>`__
to choose from.

The NUCs typically come as kits, and some assembly is required. You will need to
purchase the RAM and hard drive separately for each NUC and insert both into the
NUC before it can be used. We recommend:

-  2x 240GB SSDs (2.5")
-  1x memory kit of compatible 2x4GB sticks
   -  You can put one 4GB memory stick in each of the servers.

We have tested and can recommend the `NUC7i5BNH <https://www.intel.com/content/www/us/en/products/boards-kits/nuc/kits/nuc7i5bnh.html>`__ - these tend to be readily available in
retail stores.

The NUC7i5BNH has soldered-on wireless components, which cannot easily be
removed. For security reasons, we recommend that you take the following steps
to disable wireless functionality:

- before installation of the RAM and storage, disconnect the wireless antennae
  leads.

|NUC7 leads|

- before the initial OS installation, boot into the BIOS by pressing **F2** at
  startup, navigate to **Advanced > Devices > Onboard Devices**, and disable
  unwanted hardware - everything except **LAN**.

|Visual Bios|


.. |NUC7 leads| image:: images/hardware/nuc7-leads.jpg
.. |Visual BIOS| image:: images/hardware/visualbios.png

Other 7th-generation NUCs have also been reported to work, although we have not
tested them. For example, the `NUC7i5DNHE <https://www.intel.com/content/www/us/en/products/boards-kits/nuc/kits/nuc7i5dnhe.html>`__ uses the same Ethernet chipset as the NUC7i5BNH,
and also has a removable wireless card, simplifying the server setup process.
However, it may be harder to find a retail source for this model.

Previous Server Recommendations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Intel 5th-gen NUC
~~~~~~~~~~~~~~~~~

We previously recommended the
`NUC5i5MYHE <https://www.intel.com/content/www/us/en/products/boards-kits/nuc/kits/nuc5i5myhe.html>`__, however, it has now reached end-of-life. We will continue to support and
test SecureDrop on this hardware, but if you are building a new SecureDrop
instance we recommend using 7th-generation NUCs instead.

The NUC5i5MYHE supports wireless through *optionally-purchased* expansion cards.
This means the wireless components aren't soldered on which would make them
nearly impossible to remove without inflicting damage to the NUC. This optional
support is preferable, since you want neither WiFi nor Bluetooth.


.. note:: If you encounter issues booting Ubuntu on the NUCs, try
	  updating the BIOS according to `these instructions
	  <https://arstechnica.com/gadgets/2014/02/new-intel-nuc-bios-update-fixes-steamos-other-linux-booting-problems/>`__.

2014 Mac Minis
~~~~~~~~~~~~~~

We previously recommended the 2014 Apple Mac Minis (part number MGEM2)
for installing SecureDrop. These will soon be `officially obsolete <https://support.apple.com/en-us/HT201624>`__. Unfortunately
the 2018 revision of the Mac Mini is not a viable candidate for use with
SecureDrop, as security features of the device prevent Linux from being
installed on its internal storage. We will continue to support existing
instances using 2014 Mac Minis, but if you are building a new instance we
recommend using the 7th-gen Intel NUCs.

2014 Mac Minis have removable wireless cards that you
should remove. This requires a screwdriver for non-standard
`TR6 Torx security screws <https://www.amazon.com/Mini-Torx-Security-Screwdriver-Tool/dp/B01BG8P2Q6>`__.

However, on the first install of Ubuntu Server
the Mac Minis will not boot: this is a known issue.
The workaround requires a one-time modification after you
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

We *strongly recommend* getting USB 3.0-compatible drives to run Tails
from. The transfer speeds are significantly faster than USB 2.0, which
means a live operating system booting from one will be much faster and
more responsive.

You will need *at least* an 8GB drive to run Tails with an encrypted
persistent partition. We recommend getting something in the 16-64GB
range so you can handle large amounts of submissions without hassle.
Anything more than that is probably overkill.

Transfer Device(s) and Export Device(s)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
For USB drives with physical write protection, we have tested the `Kanguru SS3 <https://www.kanguru.com/storage-accessories/kanguru-ss3.shtml>`__
on Tails, and it works well with and without encryption.

If you want to use a setup based on CD-Rs or DVD-Rs, we've found the CDR/DVD
writers from Samsung and LG to work reasonably well; you can find some examples
`here <https://www.newegg.com/External-CD-DVD-Blu-Ray-Drives/SubCategory/ID-420>`__.

Please see our recommendations in the :doc:`setup guide <set_up_transfer_and_export_device>`
for additional background.

Network Firewall
^^^^^^^^^^^^^^^^

We recommend the `pfSense SG-3100
<https://store.netgate.com/SG-3100.aspx>`__. It has 3 NICs and an internal
switch, increasing the number of available ports to 6.

Network Switch
^^^^^^^^^^^^^^

This is optional, for people who are using a firewall with less than 4
ports.  Any old switch with more than 3 ports will do, such as the
`5-port Netgear ProSafe Ethernet Switch
<http://www.amazon.com/NETGEAR-ProSafe-Gigabit-Ethernet-Desktop/dp/B0000BVYT3/>`__.

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
