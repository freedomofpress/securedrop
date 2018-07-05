Deploying SecureDrop staging instance on Qubes
==============================================

This assumes you have an up-to-date Qubes installation on a compatible laptop
with at least 16GB RAM and 60GB free disk space.

Overview
--------

We're going to create two new standalone (HVM) Qubes VMs:

- a base VM for the *SecureDrop Application Server*
- a base VM for the *SecureDrop Monitor Server*

Along the way we'll be creating an Ubuntu Trusty VM, which we'll be using
as a starting point for the application and monitoring base VMs.

We'll also be creating ``sd-dev``, a standalone Qube based on Debian 9,
where we'll building and deploying the SecureDrop code,
and where server and client development can happen.

Create ``sd-dev``
---------------

Let's get started. Create yourself a new *standalone* Qube called ``sd-dev`` based
on the Debian 9 template that comes standard in Qubes 4.
You can use the "Q" menu for this, or in ``dom0``:

.. code:: sh

   qvm-clone --class StandaloneVM debian-9 sd-dev

Now start the VM with:

.. code:: sh

   qvm-start sd-dev

and set up its "Q" app menu:

.. code:: sh

   qvm-sync-appmenus sd-dev

Download Ubuntu Trusty server ISO
---------------------------------

On ``sd-dev``, download the Ubuntu Trusty server ISO, along with corresponding
checksum and signature files.

.. code:: sh

   wget http://releases.ubuntu.com/14.04/ubuntu-14.04.5-server-amd64.iso
   wget https://mirrors.ocf.berkeley.edu/ubuntu-releases/14.04.5/SHA256SUMS
   wget https://mirrors.ocf.berkeley.edu/ubuntu-releases/14.04.5/SHA256SUMS.gpg

After downloading, confirm the ISO's validity by checking its SHA256 sum.
Note that you may need to download the GPG keys to validate the signature.

.. code:: sh

   gpg --verify SHA256SUMS.gpg SHA256SUMS
   sha256sum --check --ignore-missing SHA256SUMS

Create the Trusty base VM
-------------------------

We're going to build a single, minimally configured Ubuntu VM.
Once it's bootable, we'll clone it for the application and monitoring VMs.

In ``dom0``, do the following:

.. code:: sh

   qvm-create sd-trusty-base --class StandaloneVM --property virt_mode=hvm --label green
   qvm-volume extend sd-trusty-base:root 20g
   qvm-prefs sd-trusty-base kernel ''
   qvm-prefs sd-trusty-base memory 2000
   qvm-prefs sd-trusty-base maxmem 2000
   qvm-prefs sd-trusty-base

The last command above will display the VM configuration. Note the IP and
gateway IP addresses Qubes gave the new VM: you'll need them for later configuration.

Boot into installation media
----------------------------

In ``dom0``:

.. code:: sh

   qvm-start sd-trusty-base --cdrom=<download-vm>:/path/to/ubuntu-14.04.5-server-amd64.iso

where ``download-vm`` is the name of the VM to which you downloaded the ISO.

Start configuration.

At some point you'll need to manually set up the network interface, after DHCP
fails. If you didn't mark it down down earlier, you can check the machine's IP
and gateway via the Qubes GUI. When prompted, use enter that IP address,
with a ``/24`` netmask (for example: ``10.137.0.16/24``. Use Qubes' internal resolvers
as DNS servers: ``10.139.1.1`` and ``10.139.1.2``. Use the gateway address indicated
in the Qubes Settings UI.

Give the new VM the hostname ``sd-trusty-base``.

You'll be prompted to add a "regular" user for the VM: this is the user you'll be
using later to SSH into the VM. We're using a standardized name/password pair:
``securedrop/securedrop``.

When presented with the partitioning menu, choose "Guided - use entire disk".
There's no need to encrypt the filesystem.
When prompted, select "Virtual disk 1 (xvda)" to partition.

During software installation, make sure you install the SSH server.
You don't need to install anything else.

The installer will prompt about where to install GRUB: choose the default (MBR).

Once installation is done, let the machine shut down and then restart it with

.. code:: sh

   qvm-start sd-trusty-base

in ``dom0``. You should get a login prompt. Yay!

Initial VM configuration
------------------------

Before cloning this machine, we'll add some software we might want on all the staging VMs.

In the new ``sd-trusty-base`` VM's console, do:

.. code:: sh

   sudo apt update
   sudo apt dist-upgrade
   sudo apt install vim

Feel free to add anything else you need to make your console life happy.

Before we continue, let's allow your user to ``sudo`` without their password.
Edit ``/etc/sudoers`` using ``visudo`` to make the sudo group line look like

.. code:: sh

   %sudo    ALL=(ALL) NOPASSWD: ALL

When initial configuration is done, ``halt`` the ``sd-trusty-base`` VM.

Clone VMs
---------

In ``dom0``:

.. code:: sh

   qvm-clone sd-trusty-base sd-app-base
   qvm-clone sd-trusty-base sd-mon-base

We're going configure the VMs to use specific IP addresses, which will make
various routing issues easier later. Run the following in ``dom0``
to set those IPs:

.. code:: sh

   qvm-prefs sd-app-base ip 10.137.0.50
   qvm-prefs sd-mon-base ip 10.137.0.51

Now start both new VMs:

.. code:: sh

   qvm-start sd-app-base
   qvm-start sd-mon-base

On the consoles which eventually appear, you should be able to log in with
``securedrop/securedrop``.

Configure cloned VMs
~~~~~~~~~~~~~~~~~~~~

We'll need to fix each machine's idea of its own IP. In the console for each
machine, edit ``/etc/network/interfaces`` to update the ``address`` line with
the machine's IP.

``/etc/hosts`` on each host needs to be modified to include the hostname and IP
for itself. On each host, add the IP and the hostname of the VM.
Use ``sd-app`` and ``sd-mon``, omitting the ``-base`` suffix, since the cloned VMs
will not have the suffix.

Finally, on each host edit ``/etc/hostname`` to reflect the machine's name.
Again, omit the ``-base`` suffix.

Halt each machine, then restart each from ``dom0``. The prompt in each console
should reflect the correct name of the VM. You should be able to ping IPs on the internet.

Inter-VM networking
~~~~~~~~~~~~~~~~~~~

(Following https://www.qubes-os.org/doc/firewall/#enabling-networking-between-two-qubes)

We want to be able to ssh from ``sd-dev`` to these new standalone VMs. In order
to do so, we have to adjust the firewall on ``sys-firewall``.

Let's get the IP address of ``sd-dev``. On ``dom0``:

.. code:: sh

   qvm-ls -n | grep sd-dev | awk '{ print $4 }'

or just look in the Qubes Settings for sd-dev, or in the output of
``/sbin/ifconfig`` on ``sd-dev`` itself.

Get a shell on ``sys-firewall``. Create or edit
``/rw/config/qubes-firewall-user-script``, to include the following:

.. code:: sh

   iptables -I FORWARD 2 -s <sd-dev-addr> -d 10.137.0.50 -j ACCEPT
   iptables -I FORWARD 2 -s <sd-dev-addr> -d 10.137.0.51 -j ACCEPT

Run those commands with

.. code:: sh

   sudo sh /rw/config/qubes-firewall-user-script

Now from ``sd-dev``, you should be able to do

.. code:: sh

   ssh securedrop@10.137.0.50

and log in with the password ``securedrop``.

sd-dev hosts
~~~~~~~~~~~~

Edit ``/etc/hosts`` on `sd-dev` to include:

.. code:: sh

   10.137.0.50 sd-app
   10.137.0.51 sd-mon

SSH using keys
~~~~~~~~~~~~~~

Later we'll be using Ansible to provision the application VMs, so we should
make sure we can ssh between those machines without needing to type
a password. On ``sd-dev``:

.. code:: sh

   ssh-keygen
   ssh-copy-id securedrop@sd-app
   ssh-copy-id securedrop@sd-mon

Confirm that you're able to ssh as user ``securedrop`` from ``sd-dev`` to
``sd-mon`` and ``sd-app`` without being prompted for a password.

SecureDrop Installation
-----------------------

We're going to configure ``sd-dev`` to build the securedrop ``.deb`` files,
then we're going to build them, and provision ``sd-app`` and ``sd-mon``.

Follow the instructions at https://docs.securedrop.org/en/latest/development/setup_development.html
to set up the development environment.

Notes:

* Don't forget to complete the Docker post-installation instructions.
  You should only need to complete the part about running docker as a non-root
  user (and you'll probably need to shutdown and restart the VM to ensure it works):
  https://docs.docker.com/install/linux/linux-postinstall/#manage-docker-as-a-non-root-user
* You'll be accessing GitHub from ``sd-dev`` to clone the SecureDrop repo,
  so you'll want that VM to have an SSH key that GitHub knows about.
  Either create a new one and register it with Github, or copy an existing key to ``sd-dev``.
* You can skip the "Using the Docker Environment" section altogether.
* Installing kernel headers will fail. That's OK.
* Installing Vagrant will fail. That's OK.

Build
~~~~~

Now we can build the .debs for the server!

.. code:: sh

   make build-debs

This will take some time.

Managing Qubes RPC for Admin API capability
-------------------------------------------

(These docs are WIP!) You'll need to grant the "work/sd-dev" VM the ability
to create other VMs. Here is an example of an extremely permissive policy,
that essentially makes "work/sd-dev" as powerful as dom0
(we must reduce these grants before submitting for review):

.. code:: sh

   /etc/qubes-rpc/policy/admin.vm.property.List:
     sd-dev $adminvm allow,target=$adminvm

   /etc/qubes-rpc/policy/admin.vm.List:
    sd-dev $adminvm allow,target=$adminvm
    sd-dev $anyvm allow,target=$adminvm

   /etc/qubes-rpc/policy/admin.property.List:
     sd-dev $adminvm allow,target=$adminvm

   /etc/qubes-rpc/policy/admin.vm.Create.StandaloneVM:
     sd-dev $adminvm allow,target=$adminvm
     sd-dev $anyvm allow,target=$adminvm

   /etc/qubes-rpc/policy/include/admin-local-rwx:
     sd-dev $adminvm allow,target=$adminvm
     sd-dev $anyvm allow,target=$adminvm

   /etc/qubes-rpc/policy/include/admin-global-ro:
     sd-dev $adminvm allow,target=$adminvm
     sd-dev $anyvm allow,target=$adminvm

   /etc/qubes-rpc/policy/include/admin-global-rwx:
     sd-dev $adminvm allow,target=$adminvm
     sd-dev $anyvm allow,target=$adminvm

Creating staging instance
-------------------------

After creating the StandaloneVMs as described above:

* sd-trusty-base
* sd-app-base
* sd-mon-base

And after building the SecureDrop .debs, we can finally provision the staging
environment. In from the root of the SecureDrop project in ``sd-dev``, run:

.. code:: sh

   molecule test -s qubes-staging

Note that since the reboots don't automatically bring the machines back up,
due to the fact that the machines are Standalone VMs, the ``test`` action will
fail by default, unless you judiciously run ``qvm-start <vm>`` for each VM
after they've shut down. You can use the smaller constituent Molecule actions,
rather than the bundled ``test`` action:

.. code:: sh

   molecule create -s qubes-staging
   molecule prepare -s qubes-staging
   molecule converge -s qubes-staging

That's it
---------

You should now have a running, configured SecureDrop staging instance running
on your Qubes machine.

For day-to-day operation, you should only need to run the ``sd-app`` and ``sd-mon`` VMs.
To do development work on the the SecureDrop server, make your changes on ``sd-dev``,
and build and deploy as covered in the SecureDrop documentation.

Notes
-----

- You may need to bump up the memory for `sd-build` or `sd-app` past 2GB. I was running in to some issues which seemed to be solved by giving the VMs more memory.
- `securedrop-admin` is made for the Tails environment and had to be modified a bit to run on `sd-build`. Also it interacts poorly with the existing virtual environment created there. We should decide if we need it at all, and if so how we can modify it to work better in for this task. Or perhaps we don't need it at all, if we instead can automatically configure the build, like we do in the existing Vagrant-based staging provisioning workflow.
