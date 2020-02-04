Set Up the Servers
==================


Install Ubuntu
--------------

.. caution:: Please ensure you are using Ubuntu Xenial ISO images 16.04.6 or greater.
    Ubuntu Xenial ISO images 16.04.5 and lower ship with a version of the `apt` package
    vulnerable to CVE-2019-3462. If you are using 16.04.5 or lower, the initial base OS
    must be installed without Internet connectivity.

.. note:: Installing Ubuntu is simple and may even be something you are very familiar
  with, but we **strongly** encourage you to read and follow this documentation
  exactly as there are some "gotchas" that may cause your SecureDrop set up to break.

The SecureDrop *Application Server* and *Monitor Server* run **Ubuntu Server
16.04.6 LTS (Xenial Xerus)**. To install Ubuntu on the servers, you must first
download and verify the Ubuntu installation media. You should use the *Admin
Workstation* to download and verify the Ubuntu installation media.

.. _download_ubuntu:

Download the Ubuntu Installation Media
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The installation media and the files required to verify it are available on the
`Ubuntu Releases page`_. You will need to download the following files:

* `ubuntu-16.04.6-server-amd64.iso`_
* `SHA256SUMS`_
* `SHA256SUMS.gpg`_

If you're reading this documentation in the Tor Browser on the *Admin
Workstation*, you can just click the links above and follow the prompts to save
them to your Admin Workstation. We recommend saving them to the
``/home/amnesia/Persistent/Tor Browser`` directory on the *Admin Workstation*,
because it can be useful to have a copy of the installation media readily
available.

Alternatively, you can use the command line:

.. code:: sh

   cd ~/Persistent
   torify curl -OOO http://releases.ubuntu.com/16.04.6/{ubuntu-16.04.6-server-amd64.iso,SHA256SUMS{,.gpg}}

.. note:: Downloading Ubuntu on the *Admin Workstation* can take a while
   because Tails does everything over Tor, and Tor is typically slow relative
   to the speed of your upstream Internet connection.

.. _Ubuntu Releases page: http://releases.ubuntu.com/
.. _ubuntu-16.04.6-server-amd64.iso: http://releases.ubuntu.com/16.04.6/ubuntu-16.04.6-server-amd64.iso
.. _SHA256SUMS: http://releases.ubuntu.com/16.04.6/SHA256SUMS
.. _SHA256SUMS.gpg: http://releases.ubuntu.com/16.04.6/SHA256SUMS.gpg

Verify the Ubuntu Installation Media
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You should verify the Ubuntu image you downloaded hasn't been modified by
a malicious attacker or otherwise corrupted. We can do so by checking its
integrity with cryptographic signatures and hashes.

First, we will download both *Ubuntu Image Signing Keys* and verify their
fingerprints. ::

    gpg --recv-key --keyserver hkps://keyserver.ubuntu.com \
    "C598 6B4F 1257 FFA8 6632 CBA7 4618 1433 FBB7 5451" \
    "8439 38DF 228D 22F7 B374 2BC0 D94A A3F0 EFE2 1092"

.. note:: It is important you type this out correctly. If you are not
          copy-pasting this command, we recommend you double-check you have
          entered it correctly before pressing enter.

Again, when passing the full public key fingerprint to the ``--recv-key`` command, GPG
will implicitly verify that the fingerprint of the key received matches the
argument passed.

.. caution:: If GPG warns you that the fingerprint of the key received
             does not match the one requested **do not** proceed with
             the installation. If this happens, please email us at
             securedrop@freedom.press.

Next, verify the ``SHA256SUMS`` file. ::

    gpg --keyid-format long --verify SHA256SUMS.gpg SHA256SUMS

Move on to the next step if you see "Good Signature" twice in the output, as
below. Note that any other message (such as "Can't check signature: no public
key") means that you are not ready to proceed. ::

    gpg: Signature made Wed Nov 11 20:08:10 2015 GMT
                    using DSA key ID 46181433FBB75451
    gpg: Good signature from "Ubuntu CD Image Automatic Signing Key
    <cdimage@ubuntu.com>"
    gpg: WARNING: This key is not certified with a trusted signature!
    gpg:          There is no indication that the signature belongs to the
    owner.
    Primary key fingerprint: C598 6B4F 1257 FFA8 6632  CBA7 4618 1433 FBB7 5451
    gpg: Signature made Wed Nov 11 20:08:10 2015 GMT
                    using RSA key ID D94AA3F0EFE21092
    gpg: Good signature from "Ubuntu CD Image Automatic Signing Key (2012)
    <cdimage@ubuntu.com>"
    gpg: WARNING: This key is not certified with a trusted signature!
    gpg:          There is no indication that the signature belongs to the
    owner.
    Primary key fingerprint: 8439 38DF 228D 22F7 B374  2BC0 D94A A3F0 EFE2 1092

The next and final step is to verify the Ubuntu image. ::

    sha256sum -c <(grep ubuntu-16.04.6-server-amd64.iso SHA256SUMS)


If the final verification step is successful, you should see the
following output in your terminal. ::

    ubuntu-16.04.6-server-amd64.iso: OK

.. caution:: If you do not see the line above it is not safe to proceed with the
             installation. If this happens, please contact us at
             securedrop@freedom.press.

Create the Ubuntu Installation Media
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create the Ubuntu installation media, you can either burn the ISO image to a
CD-R or create a bootable USB stick.  As a reliable method we recommend using
the ``dd`` command to copy the hybrid ISO directly to a USB drive rather than a
utility like UNetbootin which can result in errors. Once you have a CD or USB
with an ISO image of Ubuntu on it, you may begin the Ubuntu installation on both
SecureDrop servers.

To use `dd` you first need to find where the USB device you wish to install
Ubuntu on has been mapped. Simply running the command ``lsblk`` in the terminal
will give you a list of your block storage device mappings (this includes hard
drives and USB). If the USB you are writing the Ubuntu installer to is of a
different size or brand than the USB you are running Tails from, it should be
easy to identify which USB has which sdX identifier. If you are unsure, try
running ``lsblk`` before and after plugging in the USB you are using for the
Ubuntu installer.

If your USB is mapped to /dev/sdX and you are currently in the directory that
contains the Ubuntu ISO, you would use dd like so: ::

   sudo dd conv=fdatasync if=ubuntu-16.04.6-server-amd64.iso of=/dev/sdX

.. _install_ubuntu:

Perform the Installation
~~~~~~~~~~~~~~~~~~~~~~~~

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

Configure the Network Manually
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Ubuntu installer will try to autoconfigure networking for the server
you are setting up; however, SecureDrop requires manual network
configuration. You can hit **Cancel** at any point during network
autoconfiguration to be given the choice to *Configure the network
manually*.

If network autoconfiguration completes before you can do this, the next
window will ask for your hostname. To get back to the choice of
configuring the network manually, **Cancel** the step that asks you to
set a hostname and choose the menu option that says **Configure the
network manually** instead.

For a production install with a pfSense network firewall in place, the
*Application Server* and the *Monitor Server* are on separate networks.
You may choose your own network settings at this point, but make sure
the settings you choose are unique on the firewall's network and
remember to propagate your choices through the rest of the installation
process.

Below are the configurations you should enter, assuming you used the
network settings from the network firewall guide for a 3 NIC or 4 NIC firewall.
If you did not, adjust these settings accordingly.

-  *Application Server*:

  -  Server IP address: 10.20.2.2
  -  Netmask (default is fine): 255.255.255.0
  -  Gateway: 10.20.2.1
  -  For DNS, use Google's name servers: 8.8.8.8 and 8.8.4.4
  -  Hostname: app
  -  Domain name should be left blank

-  *Monitor Server*:

  -  Server IP address: 10.20.3.2
  -  Netmask (default is fine): 255.255.255.0
  -  Gateway: 10.20.3.1
  -  For DNS, use Google's name servers: 8.8.8.8 and 8.8.4.4
  -  Hostname: mon
  -  Domain name should be left blank

Continue the Installation
~~~~~~~~~~~~~~~~~~~~~~~~~

You can choose whatever username and passphrase you would like. To make
things easier later you should use the same username and same passphrase
on both servers (but not the same passphrase as username). Make sure to
save this passphrase in your admin KeePassXC database afterwards.

Click 'no' when asked to encrypt the home directory. Then configure your
time zone.

Partition the Disks
~~~~~~~~~~~~~~~~~~~

Before setting up the server's disk partitions and filesystems in the
next step, you will need to decide if you would like to enable `Full
Disk Encryption
(FDE) <https://www.eff.org/deeplinks/2012/11/privacy-ubuntu-1210-full-disk-encryption>`__.
If the servers are ever powered down, FDE will ensure all of the
information on them stays private in case they are seized or stolen.

.. warning:: The Ansible playbooks for SecureDrop will enable nightly reboots
             after the ``cron-apt`` task runs for automatic updates. Using FDE
             would therefore require manual intervention every morning.
             Consequently **we strongly discourage the use of FDE.**

While FDE can be useful in some cases, we currently do not recommend
that you enable it because there are not many scenarios where it will be
a net security benefit for SecureDrop operators. Doing so will introduce
the need for more passphrases and add even more responsibility on the
admin of the system (see `this GitHub
issue <https://github.com/freedomofpress/securedrop/issues/511#issuecomment-50823554>`__
for more information).

If you wish to proceed without FDE as recommended, choose the
installation option that says *Guided - use entire disk and set up LVM*.

However, if you decide to go ahead and enable FDE, please note that
doing so means SecureDrop will become unreachable after an automatic
reboot. An admin will need to be on hand to enter the passphrase
in order to decrypt the disks and complete the startup process, which
will occur anytime there is an automatic software update, and also
several times during SecureDrop's installation. We recommend that the
servers be integrated with a monitoring solution so that you receive
an alert when the system becomes unavailable.

To enable FDE, select *Guided - use entire disk and set up encrypted
LVM* during the disk partitioning step and write the changes to disk.
Follow the recommendations as to choosing a strong passphrase. As the
admin, you will be responsible for keeping this passphrase safe.
Write it down somewhere and memorize it if you can. **If inadvertently
lost it could result in total loss of the SecureDrop system.**

After selecting either of those options you may be asked a few questions
about overwriting anything currently on the server you are using. Select
yes. You do not need an HTTP proxy, so when asked, you can just click
continue.

Finish the Installation
~~~~~~~~~~~~~~~~~~~~~~~

Wait for the base system to finish installing. When you get to the
*Configure tasksel* screen, choose **No automatic updates**. The
subsequent SecureDrop installation will include a task that handles
regular software updates.

.. note:: The Ansible playbooks for SecureDrop will configure automatic
          updates via ``cron-apt``. As part of the automatic update process,
          the servers will reboot nightly. See the
          :ref:`OSSEC guide <AnalyzingAlerts>` for example notifications
          generated by the reboots.

When you get to the software selection screen, deselect the preselected
**Standard system utilities** and select **OpenSSH server** by highlighting each
option and pressing the space bar.

.. caution:: Hitting enter before the space bar will force you to start the
             installation process over.

Once **OpenSSH Server** is selected, hit *Continue*.

You will then have to wait for the packages to finish installing.

When the packages are finished installing, Ubuntu will automatically
install the bootloader (GRUB). If it asks to install the bootloader to
the Master Boot Record, choose **Yes**. When everything is done, reboot.

.. |Ubuntu Server| image:: images/install/ubuntu_server.png

Save the Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you are done, make sure you save the following information:

-  The IP address of the *Application Server*
-  The IP address of the *Monitor Server*
-  The non-root user's name and passphrase for the servers.

.. _test_connectivity:

Test Connectivity
-----------------


Now that the firewall is set up, you can plug the *Application Server*
and the *Monitor Server* into the firewall. If you are using a setup
where there is a switch on the LAN port, plug the *Application Server*
into the switch and plug the *Monitor Server* into the OPT1 port.

You should make sure you can connect from the Admin
Workstation to both of the servers before continuing with the
installation.

In a terminal, verify that you can SSH into both servers,
authenticating with your passphrase:

.. code:: sh

    $ ssh <username>@<App IP address> hostname
    app
    $ ssh <username>@<Monitor IP address> hostname
    mon

.. tip:: If you cannot connect, check the network firewall logs for
         clues.

Set Up SSH Keys
---------------

Ubuntu's default SSH configuration authenticates users with their
passphrases; however, public key authentication is more secure, and once
it's set up it is also easier to use. In this section, we will create
a new SSH key for authenticating to both servers. Since the Admin Live
USB was set up with `SSH Client Persistence`_, this key will be saved
on the Admin Live USB and can be used in the future to authenticate to
the servers in order to perform administrative tasks.

.. _SSH Client Persistence: https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html#index3h2

First, generate the new SSH keypair:

::

    ssh-keygen -t rsa -b 4096

You'll be asked to "Enter file in which to save the key" Type
**Enter** to use the default location.

Given that this key is on the encrypted persistence of a Tails USB,
you do not need to add an additional passphrase to protect the key.
If you do elect to use a passphrase, note that you will need to manually
type it (Tails' pinentry will not allow you to copy and paste a passphrase).

Once the key has finished generating, you need to copy the public key
to both servers. Use ``ssh-copy-id`` to copy the public key to each
server, authenticating with your passphrase:

.. code:: sh

    ssh-copy-id <username>@<App IP address>
    ssh-copy-id <username>@<Mon IP address>

Verify that you are able to authenticate to both servers by running
the below commands. You should not be prompted for a passphrase
(unless you chose to passphrase-protect the key you just created).

.. code:: sh

    $ ssh <username>@<App IP address> hostname
    app
    $ ssh <username>@<Monitor IP address> hostname
    mon

If you have successfully connected to the server via SSH, the terminal
output will be name of the server to which you have connected ('app'
or 'mon') as shown above.
