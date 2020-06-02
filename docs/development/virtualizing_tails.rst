.. _virtualizing_tails:

Virtual Environments: Admin Workstation
=======================================

SecureDrop uses Tails for the *Admin Workstation* environment. In order to
perform a fully virtualized production install, you will need to first set up
Tails in a virtual machine.

.. note:: For the instructions that follow, you need to download the most
          recent Tails ISO from the `Tails`_ website.

.. _`Tails`: https://tails.boum.org

macOS
-----

For the macOS instructions, you will use VirtualBox to create a Tails VM that
you can use to install SecureDrop on ``app-prod`` and ``mon-prod``.

Create a VirtualBox VM
~~~~~~~~~~~~~~~~~~~~~~

1. Open VirtualBox
2. Click **New** to create a new VM with the following options:

   * **Name**: "Admin Workstation"
   * **Type**: "Linux"
   * **Version**: "Debian (64-bit)"

.. note:: You may call the VM a different name, but you must replace
    "Admin Workstation" later on in these instructions with the name you select.

3. Click **Continue**.
4. At the prompt, configure at least 2048 MB of RAM. Click **Continue**.
5. Leave the default **Create a virtual hard disk now** selected and click
   **Create**. All the default options (**Hard disk file type: VDI (VirtualBox
   Disk Image)** and **Dynamically allocated**) are fine. Click **Create**.

Booting Tails
~~~~~~~~~~~~~

Now that the VM is set up, you are ready to boot to Tails. Select the new VM
in the VirtualBox sidebar, and click **Settings**.

1. Click **Storage**.
2. Click **Empty** under **Controller: IDE**.
3. Click the CD icon next to **Optical Drive:** and click **Choose Virtual
   Optical Disk File**.
4. Navigate to the Tails ISO to boot from.
5. Click **General** then **Advanced**.
6. Under **Shared Clipboard** select **Bidirectional** instead of **Disabled**.
   This option will enable you to transfer text from your host to the Tails VM,
   which we will use later on in these steps.

   .. note:: Alternatively you can open these docs in Tor Browser in Tails.
             This will obviate the need to copy and paste between the guest
             and host OS.

Install Tails
~~~~~~~~~~~~~

Next you will install Tails onto the Virtual Hard Disk Image. Start the VM, boot
to Tails, and enter an administration password and start Tails.

.. note:: For all the instructions that follow, you will need to configure an
          administration password each time you boot Tails.

1. Copy the following patch and save it as ``installer.patch`` in a folder in
   your Tails VM:

.. code:: Diff

  --- /usr/lib/python2.7/dist-packages/tails_installer/creator.py      2018-01-22 14:59:40.000000000 +0100
  +++ /usr/lib/python2.7/dist-packages/tails_installer/creator.py.mod  2018-03-05 05:15:00.000000000 -0800
  @@ -595,16 +595,6 @@ class LinuxTailsInstallerCreator(TailsInstallerCreator):
                   self.log.debug('Skipping non-removable device: %s'
                                  % data['device'])

  -            # Only pay attention to USB and SDIO devices, unless --force'd
  -            iface = drive.props.connection_bus
  -            if iface != 'usb' and iface != 'sdio' \
  -               and self.opts.force != data['device']:
  -                self.log.warning(
  -                    "Skipping device '%(device)s' connected to '%(interface)s' interface"
  -                    % {'device': data['udi'], 'interface': iface}
  -                )
  -                continue
  -
               # Skip optical drives
               if data['is_optical'] and self.opts.force != data['device']:
                   self.log.debug('Skipping optical device: %s' % data['device'])
  --- /usr/lib/python2.7/dist-packages/tails_installer/gui.py      2018-01-22 14:59:40.000000000 +0100
  +++ /usr/lib/python2.7/dist-packages/tails_installer/gui.py.mod  2018-03-05 05:15:00.000000000 -0800
  @@ -568,16 +568,6 @@ class TailsInstallerWindow(Gtk.ApplicationWindow):
                       self.devices_with_persistence.append(info['parent'])
                       continue
                   pretty_name = self.get_device_pretty_name(info)
  -                # Skip devices with non-removable bit enabled
  -                if not info['removable']:
  -                    message =_('The USB stick "%(pretty_name)s"'
  -                               ' is configured as non-removable by its'
  -                               ' manufacturer and Tails will fail to start on it.'
  -                               ' Please try installing on a different model.') % {
  -                               'pretty_name':  pretty_name
  -                               }
  -                    self.status(message)
  -                    continue
                   # Skip too small devices, but inform the user
                   if not info['is_device_big_enough_for_installation']:
                       message =_('The device "%(pretty_name)s"'

2. Now run the following two commands in a Terminal in your Tails VM:

.. code:: sh

  sudo patch -p0 -d/ < installer.patch
  sudo /usr/bin/python -tt /usr/bin/tails-installer -u -n --clone -P -m -x

3. The **Tails Installer** will appear. Click **Install Tails**.
4. Once complete, navigate to **Applications**, **Utilities** and open **Disks**.
5. Click on the disk named "Tails" and click the Play icon to mount the disk.
6. Next open ``/media/amnesia/Tails/syslinux/live*.cfg`` and delete all instances
   of ``live-media=removable``.
7. Shut down the VM.

Boot to Tails Hard Drive Install
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now we will remove the CD and boot to the Tails we just installed on our
virtual hard drive. From macOS you should:

1. Click the VM in the sidebar of VirtualBox and click **Settings**.
2. Click **Storage** and select the Tails .iso under **Controller: IDE**.
3. Click the CD icon, then **Remove Disk from Virtual Drive**.
4. Click **Ok**.
5. Start the VM.

Configure Persistence
~~~~~~~~~~~~~~~~~~~~~

Now in your booted Tails VM you should:

1. Configure an admin password when prompted.
2. Copy the following patch to the Tails VM and save it as ``persistence.patch``:

.. code:: Diff

   --- /usr/share/perl5/Tails/Persistence/Setup.pm	2017-06-30 09:56:25.000000000 +0000
   +++ /usr/share/perl5/Tails/Persistence/Setup.pm.mod	2017-07-20 07:17:48.472000000 +0000
   @@ -404,19 +404,6 @@

        my @checks = (
            {
   -            method  => 'drive_is_connected_via_a_supported_interface',
   -            message => $self->encoding->decode(gettext(
   -                "Tails is running from non-USB / non-SDIO device %s.")),
   -            needs_drive_arg => 1,
   -        },
   -        {
   -            method  => 'drive_is_optical',
   -            message => $self->encoding->decode(gettext(
   -                "Device %s is optical.")),
   -            must_be_false    => 1,
   -            needs_drive_arg => 1,
   -        },
   -        {
                method  => 'started_from_device_installed_with_tails_installer',
                message => $self->encoding->decode(gettext(
                    "Device %s was not created using Tails Installer.")),

3. To apply the patch, from the Terminal run:

.. code:: sh

  sudo patch -p0 -d/ < persistence.patch

4. Navigate to **Applications** then **Tails** and click **Configure
   persistent volume**. Configure a persistent volume enabling all persistence
   options.

Shared Folders
~~~~~~~~~~~~~~

1. In macOS, click on the Tails VM in VirtualBox and then go to
   **Settings**.
2. Click on **Shared Folders** and click the button on the right hand side to
   add the folder. Navigate to the location of the SecureDrop repository on
   your local machine. Check **Auto-mount**. Do not check
   **Read-only**.

3. Now reboot your Tails VM, decrypt the Persistent volume, and run the following
   commands in a **Terminal** in Tails:

.. code:: sh

  mkdir ~/Persistent/securedrop
  echo 'if [ ! -d ~/Persistent/securedrop/install_files ]; then sudo mount -t vboxsf -o uid=$UID,gid=$(id -g) securedrop ~/Persistent/securedrop; fi' >> /live/persistence/TailsData_unlocked/dotfiles/.bashrc

The first time you open a Terminal in that session you will be prompted for your
sudo password and the shared folder will be mounted. Each time you open a
Terminal thereafter in the Tails session, your sudo password will not be needed.

Allow the Guest to Create Symlinks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finally, you'll need to allow the guest to create symlinks, which are
`disabled by default in VirtualBox`_.

.. _`disabled by default in VirtualBox`: https://www.virtualbox.org/ticket/10085#comment:12

Shut down the Tails VM, and in your host run:

.. code:: sh

  VBoxManage setextradata "Admin Workstation" VBoxInternal2/SharedFoldersEnableSymlinksCreate/securedrop 1

.. note:: If you named your Tails VM something other than "Admin Workstation",
    you can run ``VBoxManage list vms`` to get the name of the Virtual Machine.

Finally, restart VirtualBox.

Configure Networking
~~~~~~~~~~~~~~~~~~~~

In order to communicate with the server VMs, you'll need to attach this
virtualized *Admin Workstation* to the ``securedrop`` network.

.. warning:: If you named the SecureDrop repository something other than
    ``securedrop``, you should connect your VM to the network of the same name.

With the *Admin Workstation* VM turned off, you should:

1. Click on the VM in VirtualBox.
2. Click **Settings**.
3. Click **Network** and then **Adapter 2**.
4. Enable this network adapter and attach it to the **Internal Network** called
   ``securedrop``.
5. Click OK and start the VM.

Now you should be able to boot to Tails, decrypt the Persistent volume,
navigate to ``~/Persistent/securedrop`` and proceed with the :ref:`production
install <prod_install_from_tails>`.

Disable Shared Clipboard (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Click on the VM in VirtualBox.
2. Click **Settings**.
3. Click **General** and then **Advanced**.
4. Now that you are finished with copy pasting the patches above you can change
   the **Shared Clipboard** from **Bidirectional** back to **Disabled**.

Linux
-----

For the Linux instructions, you will use KVM/libvirt to create a Tails VM that
you can use to install SecureDrop on ``app-prod`` and ``mon-prod``.

Create a libvirt VM
~~~~~~~~~~~~~~~~~~~

Follow the Tails virt-manager instructions for
`Running Tails from a virtual USB storage <https://tails.boum.org/doc/advanced_topics/virtualization/virt-manager/index.en.html#index5h1>`__.
After installing Tails on the removable USB device, shut down the VM
and edit the boot options. You'll need to manually enable booting from the USB
device by checking the box labeled **USB Disk 1**.

.. image:: ../images/devenv/tails-libvirt-boot-options.png

Then proceed with booting to the USB drive, and configure a persistence volume.

Shared Folders
~~~~~~~~~~~~~~

In order to mount the SecureDrop git repository as a folder inside the Tails
persistence volume, you must add a filesystem via virt-manager.

1. Choose **View ▸ Details** to edit the configuration of the virtual machine.
2. Click on the **Add Hardware** button on the bottom of the left pane.
3. Select **Filesystem** in the left pane.
4. In the right pane, change the **Mode** to **Mapped**.
5. In the right pane, change **Source path** to the path to the SecureDrop git repository on the host machine.
6. In the right pane, change **Target path** to **securedrop**.
7. Click **Finish**.

.. image:: ../images/devenv/tails-libvirt-filesystem-config.png

On the next VM boot, you will be able to mount the SecureDrop git repository
from the host machine via:

.. code:: sh

  mkdir -p ~/Persistent/securedrop
  sudo mount -t 9p securedrop ~/Persistent/securedrop

You will need to run the ``mount`` command every time you boot the VM.
By default only read operations are supported. In order to support modifying files
in the git repository, you will need to configure file ACLs.
On the host machine, from within the SecureDrop git repository, run:

.. code:: sh

  make libvirt-share

All files will be created with mode ``0600`` and ownership ``libvirt-qemu:libvirt-qemu``.
You will need to modify the files manually on the host machine in order to commit them.
