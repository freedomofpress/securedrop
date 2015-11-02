Ubuntu Install Guide
====================

The *Application Server* and the *Monitor Server* specifically require
the 64-bit version of `Ubuntu Server 14.04.2 LTS (Trusty
Tahr) <http://old-releases.ubuntu.com/releases/14.04.2/>`__. The image
you want to get is named ``ubuntu-14.04.2-server-amd64.iso``. In order
to verify the installation media, you should also download the files
named ``SHA256SUMS`` and ``SHA256SUMS.gpg``.

Verify the Ubuntu installation media
------------------------------------

First you should make sure that the Ubuntu image you downloaded hasn't
been modified by a malicious attacker by checking its integrity with
cryptographic signatures and hashes — which might sound complex but it's
relatively easy to do. Before you can verify the Ubuntu installation
media, you will need to download the associated public key.

::

    gpg --keyserver pool.sks-keyservers.net --recv-key C5986B4F1257FFA86632CBA746181433FBB75451
    gpg --fingerprint C5986B4F1257FFA86632CBA746181433FBB75451

The Ubuntu CD Image Automatic Signing Key should have a fingerprint of
"C598 6B4F 1257 FFA8 6632 CBA7 4618 1433 FBB7 5451". If the fingerprint
does not match what you see here, please get in touch at
securedrop@freedom.press.

Verify the ``SHA256SUMS`` file and move on to the next step if you see
"Good Signature" in the output.

::

    gpg --verify SHA256SUMS.gpg SHA256SUMS

The next and final step is to verify the Ubuntu image. If you are using
Linux, use the following command.

::

    sha256sum -c <(grep ubuntu-14.04.2-server-amd64.iso SHA256SUMS)

If you are using OS X, use the command below.

::

    shasum -a 256 -c <(grep ubuntu-14.04.2-server-amd64.iso SHA256SUMS)

If the final verification step is successful, you should see the
following output in your terminal.

::

    ubuntu-14.04.2-server-amd64.iso: OK

Create the Ubuntu installation media
------------------------------------

To create the Ubuntu installation media, you can either burn the ISO
image to a CD-R or create a bootable USB stick (see instructions for
doing this on `OS
X <http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-mac-osx>`__,
`Ubuntu <http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-ubuntu>`__
and
`Windows <http://www.ubuntu.com/download/desktop/create-a-usb-stick-on-windows>`__).
As a reliable method we recommend using the ``dd`` command to copy the
hybrid ISO directly to a USB drive rather than a utility like UNetbootin
which can result in errors. Once you have a CD or USB with an ISO image
of Ubuntu on it, you may begin the Ubuntu installation on both
SecureDrop servers.

Install Ubuntu
--------------

The steps below are the same for both the *Application Server* and the
*Monitor Server*.

Start by inserting the Ubuntu installation media into the server. Boot
or reboot the server with the installation media inserted, and enter the
boot menu. To enter the boot menu, you need to press a key as soon as
you turn the server on. This key varies depending on server model, but
common choices are Esc, F2, F10, and F12. Often, the server will briefly
display a message on boot that shows which key should be pressed to
enter the boot menu. Once you've entered the boot menu, select the
installation media (USB or CD) and press Enter to boot it.

After booting the Ubuntu image, select **Install Ubuntu Server**.

|Ubuntu Server|

Follow the steps to select your language, country and keyboard settings.
Once that's done, let the installation process continue.

Configure the network manually
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Ubuntu installer will try to autoconfigure networking for the server
you are setting up; however, SecureDrop 0.3 requires manual network
configuration. You can hit **Cancel** at any point during network
autoconfiguration to be given the choice to *Configure the network
manually*.

If network autoconfiguration completes before you can do this, the next
window will ask for your hostname. To get back to the choice of
configuring the network manually, **Cancel** the step that asks you to
set a hostname and choose the manu option that says **Configure the
network manually** instead.

For a production install with a pfSense network firewall in place, the
*Application Server* and the *Monitor Server* are on separate networks.
You may choose your own network settings at this point, but make sure
the settings you choose are unique on the firewall's network and
remember to propagate your choices through the rest of the installation
process.

Below is the configuration you should enter, assuming you used the
network settings from the network firewall guide. If you did not, adjust
these settings accordingly.

-  **Application Server**:

   -  Server IP address: 10.20.1.2
   -  Netmask (default is fine): 255.255.255.0
   -  Gateway: 10.20.1.1
   -  For DNS, use Google's name servers: 8.8.8.8
   -  Hostname: app
   -  Domain name should be left blank

-  **Monitor Server**:

   -  Server IP address: 10.20.2.2
   -  Netmask (default is fine): 255.255.255.0
   -  Gateway: 10.20.2.1
   -  For DNS, use Google's name servers: 8.8.8.8
   -  Hostname: mon
   -  Domain name should be left blank

Continue the installation
~~~~~~~~~~~~~~~~~~~~~~~~~

You can choose whatever username and password you would like. To make
things easier later you should use the same username and password on
both servers. Make sure to save this password in your admin KeePassX
database afterwards.

Click 'no' when asked to encrypt the home directory. Then configure your
time zone.

Partition the disks
~~~~~~~~~~~~~~~~~~~

Before setting up the server's disk partitions and filesystems in the
next step, you will need to decide if you would like to enable `*Full
Disk Encryption
(FDE)* <https://www.eff.org/deeplinks/2012/11/privacy-ubuntu-1210-full-disk-encryption>`__.
If the servers are ever powered down, FDE will ensure all of the
information on them stays private in case they are seized or stolen.

While FDE can be useful in some cases, we currently do not recommend
that you enable it because there are not many scenarios where it will be
a net security benefit for SecureDrop operators. Doing so will introduce
the need for more passwords and add even more responsibility on the
administrator of the system (see `this GitHub
issue <https://github.com/freedomofpress/securedrop/issues/511#issuecomment-50823554>`__
for more information).

If you wish to proceed without FDE as recommended, choose the
installation option that says *Guided - use entire disk and set up LVM*.

However, if you decide to go ahead and enable FDE, please note that
doing so means SecureDrop will become unreachable after an automatic
reboot. An administrator will need to be on hand to enter the password
in order to decrypt the disks and complete the startup process, which
will occur anytime there is an automatic software update, and also
several times during SecureDrop's installation. We recommend that the
servers be integrated with a monitoring solution that so that you
receive an alert when the system becomes unavailable.

To enable FDE, select *Guided - use entire disk and set up encrypted
LVM* during the disk partitioning step and write the changes to disk.
Follow the recommendations as to choosing a strong password. As the
administrator, you will be responsible for keeping this passphrase safe.
Write it down somewhere and memorize it if you can. **If inadvertently
lost it could result in total loss of the SecureDrop system.**

After selecting either of those options you may be asked a few questions
about overwriting anything currently on the server you are using. Select
yes. You do not need an HTTP proxy, so when asked, you can just click
continue.

Finish the installation
~~~~~~~~~~~~~~~~~~~~~~~

Wait for the base system to finish installing. When you get to the
*Configure tasksel* screen, choose **No automatic updates**. The
subsequent SecureDrop installation will include a task that handles
regular software updates.

When you get to the software selection screen, only choose **OpenSSH
server** by hitting the space bar (Note: hitting enter before the space
bar will force you to start the installation process over).

Once **OpenSSH Server** is selected, hit *Continue*.

You will then have to wait for the packages to finish installing.

When the packages are finished installing, Ubuntu will automatically
install the bootloader (GRUB). If it asks to install the bootloader to
the Master Boot Record, choose **Yes**. When everything is done, reboot.

You can now return to where you left off in the main SecureDrop install
guide :doc:`by clicking here <servers>`.

.. |Ubuntu Server| image:: images/install/ubuntu_server.png
