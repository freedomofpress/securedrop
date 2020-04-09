Deploying SecureDrop staging instance on Qubes
==============================================

This assumes you have an up-to-date Qubes installation on a compatible laptop
with at least 16GB RAM and 60GB free disk space.

Overview
--------

Follow the the Qubes platform instructions in :doc:`setup_development`
to create an ``sd-dev`` Standalone VM. Once done, we'll create three new
Standalone (HVM) Qubes VMs for use with staging:

- ``sd-staging-base``, a base VM for cloning reusable staging VMs
- ``sd-staging-app-base``, a base VM for the *SecureDrop Application Server*
- ``sd-staging-mon-base``, a base VM for the *SecureDrop Monitor Server*

While the development VM, ``sd-dev``, is based on Debian 9, the other VMs
will be based on Ubuntu Xenial.

.. note:: The staging server VM names were recently changed from ``sd-app`` and
         ``sd-mon`` to account for a name change in the SecureDrop Workstation
         project.

Download Ubuntu Xenial server ISO
---------------------------------

On ``sd-dev``, download the Ubuntu Xenial server ISO, along with corresponding
checksum and signature files. See the :ref:`hardware installation docs <download_ubuntu>`
for detailed instructions. If you opt for the command line instructions, omit
the ``torify`` prepended to the ``curl`` command.

Create the base VM
------------------

We're going to build a single, minimally configured Ubuntu VM.
Once it's bootable, we'll clone it for the application and monitoring VMs.

In ``dom0``, do the following:

.. code:: sh

   qvm-create sd-staging-base --class StandaloneVM --property virt_mode=hvm --label green
   qvm-volume extend sd-staging-base:root 20g
   qvm-prefs sd-staging-base memory 2000
   qvm-prefs sd-staging-base maxmem 2000
   qvm-prefs sd-staging-base kernel ''

The commands above will create a new StandaloneVM, expand the storage space
and memory available to it, as well as disable the integrated kernel support.
The SecureDrop install process will install a custom kernel.

Boot into installation media
----------------------------

In ``dom0``:

.. code:: sh

   qvm-start sd-staging-base --cdrom=sd-dev:/home/user/ubuntu-16.04.6-server-amd64.iso

You may need to edit the filepath above if you downloaded the ISO to a
different location within the ``sd-dev`` VM. Choose **Install Ubuntu**.
For the most part, the install process matches the
:ref:`hardware install flow <install_ubuntu>`, with a few exceptions:

  -  Server IP address: use value returned by ``qvm-prefs sd-staging-base ip``, with ``/24`` netmask suffix
  -  Gateway: use value returned by ``qvm-prefs sd-staging-base visible_gateway``
  -  For DNS, use Qubes's DNS servers: ``10.139.1.1`` and ``10.139.1.2``.
  -  Hostname: ``sd-staging-base``
  -  Domain name should be left blank

Make sure to configure LVM and use **Virtual disk 1 (xvda 20.0GB Xen Virtual Block device)**
when asked for a target partition during installation. It should be the default option.

You'll be prompted to add a "regular" user for the VM: this is the user you'll be
using later to SSH into the VM. We're using a standardized name/password pair:
``sdadmin/securedrop``.

Once installation is done, let the machine shut down and then restart it with

.. code:: sh

   qvm-start sd-staging-base

in ``dom0``. You should get a login prompt.

Initial VM configuration
------------------------

Before cloning this machine, we'll update software to reduce provisioning time
on the staging VMs. In the new ``sd-staging-base`` VM's console, do:

.. code:: sh

   sudo apt update
   sudo apt dist-upgrade -y

Before we continue, let's allow your user to ``sudo`` without their password.
Edit ``/etc/sudoers`` using ``visudo`` to make the sudo group line look like

.. code:: sh

   %sudo    ALL=(ALL) NOPASSWD: ALL


Finally, update the machine's Grub configuration to use a consistent Ethernet device
name across kernel versions. Edit the file ``/etc/default/grub``, changing the line:

.. code:: sh

   GRUB_CMDLINE_LINUX=""

to

.. code:: sh

   GRUB_CMDLINE_LINUX="net.ifnames=0 biosdevname=0"


When initial configuration is done, run ``qvm-shutdown sd-staging-base`` to shut it down.

Clone VMs
---------

We're going configure the VMs to use specific IP addresses, which will make
various routing issues easier later. We'll also tag the VMs for management
by the ``sd-dev`` VM. Doing so will require Qubes RPC policy changes,
documented below. Run the following in ``dom0``:

.. code:: sh

   qvm-clone sd-staging-base sd-staging-app-base
   qvm-clone sd-staging-base sd-staging-mon-base
   qvm-prefs sd-staging-app-base ip 10.137.0.50
   qvm-prefs sd-staging-mon-base ip 10.137.0.51
   qvm-tags sd-staging-app-base add created-by-sd-dev
   qvm-tags sd-staging-mon-base add created-by-sd-dev

Now start both new VMs:

.. code:: sh

   qvm-start sd-staging-app-base
   qvm-start sd-staging-mon-base

On the consoles which eventually appear, you should be able to log in with
``sdadmin/securedrop``.

Configure cloned VMs
~~~~~~~~~~~~~~~~~~~~

We'll need to fix each machine's idea of its own IP. In the console for each
machine, edit ``/etc/network/interfaces`` to update the ``address`` line with
the machine's IP.

Edit ``/etc/hosts`` on each host to include the hostname and IP for itself.
Use ``sd-staging-app`` and ``sd-staging-mon``, omitting the ``-base`` suffix, since the cloned VMs
will not have the suffix.

Next, on each host edit ``/etc/hostname`` to reflect the machine's name.
Again, omit the ``-base`` suffix.

Halt each machine, then restart each from ``dom0``. The prompt in each console
should reflect the correct name of the VM. Confirm you have network access by
running ``ping freedom.press``. It should show no errors.

Inter-VM networking
~~~~~~~~~~~~~~~~~~~

We want to be able to SSH connections from ``sd-dev`` to these new standalone VMs.
In order to do so, we have to adjust the firewall on ``sys-firewall``.

.. tip::

   See the official Qubes guide on configuring `inter-VM networking`_ for details.

.. _`inter-VM networking`: https://www.qubes-os.org/doc/firewall/#enabling-networking-between-two-qubes

Let's get the IP address of ``sd-dev``. On ``dom0``:

.. code:: sh

   qvm-prefs sd-dev ip

Get a shell on ``sys-firewall``. Create or edit
``/rw/config/qubes-firewall-user-script``, to include the following:

.. code:: sh

   sd_dev="<sd-dev-addr>"
   sd_app="10.137.0.50"
   sd_mon="10.137.0.51"

   iptables -I FORWARD 2 -s "$sd_dev" -d "$sd_app" -j ACCEPT
   iptables -I FORWARD 2 -s "$sd_dev" -d "$sd_mon" -j ACCEPT
   iptables -I FORWARD 2 -s "$sd_app" -d "$sd_mon" -j ACCEPT
   iptables -I FORWARD 2 -s "$sd_mon" -d "$sd_app" -j ACCEPT

Run those commands on ``sys-firewall`` with

.. code:: sh

   sudo sh /rw/config/qubes-firewall-user-script

Now from ``sd-dev``, you should be able to do

.. code:: sh

   ssh sdadmin@10.137.0.50

and log in with the password ``securedrop``.

SSH using keys
~~~~~~~~~~~~~~

.. tip::
   You likely already have an SSH keypair configured for access to GitHub.
   If not, create one with ``ssh-keygen -b 4096 -t rsa``. The configuration
   logic will use the key at ``~/.ssh/id_rsa`` to connect to the VMs.

Later we'll be using Ansible to provision the application VMs, so we should
make sure we can SSH between those machines without needing to type
a password. On ``sd-dev``:

.. code:: sh

   ssh-copy-id sdadmin@10.137.0.50
   ssh-copy-id sdadmin@10.137.0.51

Confirm that you're able to ssh as user ``sdadmin`` from ``sd-dev`` to
``sd-staging-mon-base`` and ``sd-staging-app-base`` without being prompted for a password.

SecureDrop Installation
-----------------------

We're going to configure ``sd-dev`` to build the SecureDrop ``.deb`` files,
then we're going to build them, and provision ``sd-staging-app`` and ``sd-staging-mon``.
Follow the instructions in the :doc:`developer documentation <setup_development>`
to set up the development environment.

Once finished, build the Debian packages for installation on the staging VMs.

.. code::

   make build-debs

The ``.deb`` files will be available in ``build/``.

Managing Qubes RPC for Admin API capability
-------------------------------------------

We're going to be running Qubes management commands on ``sd-dev``,
which requires some additional software. Install it with

.. code::  sh

    sudo apt install qubes-core-admin-client

You'll need to grant the ``sd-dev`` VM the ability to create other VMs,
by editing the Qubes RPC policies in ``dom0``. Here is an example of a
permissive policy, sufficient to grant ``sd-dev`` management capabilities
over VMs it creates:

.. todo::

   Reduce these grants to the bare minimum necessary. We can likely
   pare them down to a single grant, preferably with tags-based control.

.. code:: sh

   /etc/qubes-rpc/policy/include/admin-local-rwx:
     sd-dev $tag:created-by-sd-dev allow,target=$adminvm

   /etc/qubes-rpc/policy/include/admin-global-rwx:
     sd-dev $adminvm allow,target=$adminvm
     sd-dev $tag:created-by-sd-dev allow,target=$adminvm

.. tip::

   See the Qubes documentation for details on leveraging the `Admin API`_.

.. _`Admin API`: https://www.qubes-os.org/doc/admin-api/

Creating staging instance
-------------------------

After creating the StandaloneVMs as described above:

* ``sd-dev``
* ``sd-staging-base``
* ``sd-staging-app-base``
* ``sd-staging-mon-base``

And after building the SecureDrop .debs, we can finally provision the staging
environment. In from the root of the SecureDrop project in ``sd-dev``, run:

.. code:: sh

   make staging

The ``make staging`` command invokes the ``qubes-staging`` Molecule scenario. 
You can also run constituent Molecule actions directly, rather than using
the Makefile target: 

.. code:: sh

   molecule create -s qubes-staging
   molecule converge -s qubes-staging
   molecule test -s qubes-staging

.. note:: 

  If the Molecule converge scenario fails with an error like ``"stderr": 
  "app: Failed to clone appmenus, qvm-appmenus missing\`` you may be running 
  into a bug in Qubes that prevents non-dom0 VMs from cloning new VMs. A 
  workaround is described `here <https://github.com/freedomofpress/securedrop/issues/3936>`_.

That's it. You should now have a running, configured SecureDrop staging instance
running on your Qubes machine. For day-to-day operation, you should run
``sd-dev`` in order to make code changes, and use the Molecule commands above
to provision staging VMs on-demand. To remove the staging instance, use the Molecule command:

.. code:: sh

   molecule destroy -s qubes-staging

