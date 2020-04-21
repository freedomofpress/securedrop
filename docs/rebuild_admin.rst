Rebuilding an *Admin Workstation* USB
-------------------------------------

.. note:: These instructions refer to a SecureDrop instance using v2 onion 
          services. If your instance uses v3 onion services and you need to
          rebuild your *Admin Workstation*, please contact FPF through the
          `SecureDrop Support Portal`_.                            
                                                                                
.. _SecureDrop Support Portal: https://securedrop-support.readthedocs.io/en/latest/


In cases where an *Admin Workstation* USB stick has been lost or destroyed, and no
backup exists, it is possible to rebuild one. In order to do so, you'll need
 
 - physical access to the SecureDrop servers
 - 2 USB sticks:

   - Tails Master USB
   - 1 replacement *Admin Workstation* USB (USB3 and 16GB or better recommended)

The process requires experience with the Linux command line and Tails, and 
can take up to 3 hours. If a backup of the SecureDrop application server is available,
reinstalling the instance may be simpler. An outline of the steps involved in
rebuilding an *Admin Workstation* is as follows:

 #. Prepare the USB sticks.
 #. (Optional) Boot the *Application* and *Monitor Server* in single user mode and  reset
    the shell admin account password.
 #. Set up SSH access for the new *Admin Workstation*.
 #. Retrieve SecureDrop configuration settings from the  *Application* and *Monitor Server*.
 #. Back up and configure the SecureDrop application.
 #. Run the ``./securedrop-admin tailsconfig`` and ``./securedrop-admin install``
    commands from the new *Admin Workstation*.
 #. Complete post-rebuild tasks.


.. important:: The rebuild process involves temporarily removing ``iptables`` 
               rules on the *Application* and *Monitor Servers*, weakening their
               security. Because of this, it's important to complete the rebuild
               process promptly, to avoid leaving the servers in an insecure state.


Step 1: Prepare the USB sticks
==============================

First, :ref:`create a new Admin Workstation USB <setup_install_tails>` 
and set up a persistent volume with a strong passphrase.

Once persistence has been set up, start up the *Admin Workstation* with 
persistence enabled, :ref:`install the SecureDrop application code, and set up
the KeePassXC database <set_up_admin_tails>`.

The *Admin Workstation* uses SSH with key authentication to connect to the servers,
so you'll need to create a new SSH keypair for your SecureDrop instance. To do so,
open a terminal by navigating to **Applications>Favorites>Terminal**,  and run 
the following command:

.. code:: sh

 ssh-keygen -t rsa -b 4096

When prompted to ``Enter file in which to save the key``, Press **Enter** to use
the default location. When prompted for a passphrase, it's safe to leave it blank.


Step 2: (Optional) Boot the servers in single-user mode
=======================================================
If you do not have the original password for the shell admin account on the
*Application* and *Monitor Servers*, you'll need to reset the password on each
server by booting in single user mode. In order to do so, you'll need physical
access to the server, a keyboard, and a monitor. 

First, connect a monitor and keyboard to the *Monitor Server*. Then reboot the server.
When the GRUB menu appears, make sure the **Ubuntu** entry is highlighted, and 
press **e** to edit boot options.
In the boot options for Ubuntu, find the line that starts with ``linux`` and ends
with ``ro``. Add ``single`` after ``ro``, separated by a space, and press
**F10** to boot in single user mode.

Reset the SecureDrop admin user's password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Once the root prompt appears, you'll need to reset the password for the
SecureDrop admin user. By default this user is named `sdadmin` and has UID 1000.
However it may have been named differently during the installation of your 
instance. You can use the command ``getent passwd 1000`` to check the username
corresponding to UID 1000. Once you have the correct username, reset its password
using the `passwd` command, for example:

.. code:: sh 

 passwd sdadmin

.. important::
 Make sure to select a strong password, and record it in the *Admin Workstation's*
 KeePassXC database.

Finally, reboot the *Monitor Server* and verify that you can log in at the console
using the new password.

Repeat the process for the *Application Server*. Use the same username and 
password as for the *Monitor Server* - this is required in order for the 
``./securedrop-admin install`` command to work correctly.

Step 3: Set up *Admin Workstation* access
=========================================
Next, you'll configure the servers to allow temporary SSH access from the new *Admin
Workstation*.

First, start the new *Admin Workstation* with persistence enabled and an administration
password set.

Next, connect the new *Admin Workstation* to the *Hardware Firewall* via the
appropriate Ethernet port, and set up its static IP address. For more information
on how to do so, see :ref:`this section in the firewall setup documentation
<assign_static_ip_to_workstation>`. If you do not know the correct static IP
address for the *Admin Workstation*, and you are using a recommended pfSense-based
*Hardware Firewall*, you can retrieve the address by loggging into its admin
interface and checking the settings under **Firewall ▸ Aliases**.

.. note:: If you do not have login credentials for your pfSense firewall, check 
 its user manual for instructions on resetting the administration password.

Next, determine whether your instance was set up to allow adminstrative access
via SSH over Tor, or via SSH over LAN. If you don't know which option was originally
chosen, you can check as follows:

 #. Log in to the *Application Server* via the console using the adminstration username
    and password.
 #. Check to see if an SSH hidden proxy service exists, using the command 
    ``sudo cat /var/lib/tor/services/ssh/hostname``. If this file exists and
    includes an Onion URL and authorization token, your instance is set up 
    to use SSH over Tor and you should configure temporary SSH access
    using :ref:`these instructions <rebuild_ssh_over_tor>`.
    If not, your instance is set up to use SSH over LAN, and you should follow
    :ref:`these instructions instead <rebuild_ssh_over_lan>`.

.. _rebuild_ssh_over_tor:

Configuring access for an SSH-over-Tor instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Direct SSH access is disabled when the SSH-over-Tor option is selected during
installation. To temporarily re-enable it, you'll need to update ``iptables`` rules
and change the sshd daemon's configuration.

First, log on to the *Application Server* via the console, and run the following
commands, substituting the *Admin Workstation's* static IP for ``<admin_static_ip>``:

.. code:: sh

  sudo iptables -I INPUT -p tcp --dport 22 -s <admin_static_ip> \
    -m state --state NEW,ESTABLISHED -j ACCEPT
  sudo iptables -I OUTPUT -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT 

Next, edit the file ``/etc/ssh/sshd_config``, changing the line:

.. code-block:: none

  ListenAddress 127.0.0.1:22                                    

to:
 
.. code-block:: none

  ListenAddress 0.0.0.0:22                                   

and deleting the line: 

.. code-block:: none

  PasswordAuthentication no                                         

Then, restart ``sshd`` using the command ``sudo service sshd restart``.

Finally, check the file ``/etc/network/interfaces``, and note down the network
settings for the default Ethernet interface. You'll need them in the next step.

Repeat the process above for the *Monitor Server*, making sure to note down its
network settings as well.

.. _rebuild_ssh_over_lan:

Once the *Monitor Server* has been configured, proceed to :ref:`enable access from
the new Admin Workstation <enabling_access_from_admin>`.

Configuring access for an SSH-over-LAN instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, log on to the *Application Server* via the console and edit the file 
``/etc/ssh/sshd_config``, deleting the line:

.. code-block:: none

  PasswordAuthentication no                                         

Then, restart ``sshd`` using the command ``sudo service sshd restart``.

Finally, check the file ``/etc/network/interfaces``, and note down the network
settings for the default Ethernet interface. You'll need them in the next step.

Repeat the process above for the *Monitor Server*, making sure to note down its
network settings as well.

.. _enabling_access_from_admin:

Enabling access from the new *Admin Workstation*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

From the *Admin Workstation*, open a terminal and copy the *Admin Workstation's* 
SSH public key to the servers, substituting the values for the server administration
username and server IP addresses in the commands below and entering the admin account's 
password when prompted:

.. code:: sh

  ssh-copy-id <admin-username>@<application-server-ip>
  ssh-copy-id <admin-username>@<monitor-server-ip>
  
Next, create a file ``~/.ssh/config`` with contents as below, again substituting
the appropriate values for your servers:

.. code-block:: none
 
  Host app
    User <admin-username>
    Hostname <application-server-ip>
    ProxyCommand none

  Host mon
    User <admin-username>
    Hostname <monitor-server-ip>
    ProxyCommand none


Finally, test direct SSH access from the terminal, using the commands ``ssh app`` and 
``ssh mon``. It should be possible to connect without entering a password.

Step 4: Retrieve SecureDrop configuration info from the servers
===============================================================

In addition to the account and networking information retrieved from the servers
so far, you'll need to retrieve the following files and info:

 - Tor Onion Service URLs and tokens
 - GPG *Submission Public Key* and OSSEC public key
 - OSSEC alert configuration details
 - (Optional) HTTPS configuration details

Retrieve Onion Service info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to connect to the Tor Onion Services used by your instance, you will
need to copy their details to the *Admin Workstation*. To do so, run the following
commands from a Terminal window:

.. code:: sh

 cd ~/Persistent/securedrop/install_files/ansible-base
 echo "HidServAuth $(ssh app sudo cat /var/lib/tor/services/journalist/hostname)" \
    > app-journalist-aths
 echo "$(ssh app sudo cat /var/lib/tor/services/source/hostname)" > app-source-ths

If your instance was set up to use SSH over TOR, you'll also need to copy over the details 
of the SSH proxy Onion Services, by running the following commands:

.. code:: sh

 echo "HidServAuth $(ssh app sudo cat /var/lib/tor/services/ssh/hostname)" > app-ssh-aths
 echo "HidServAuth $(ssh mon sudo cat /var/lib/tor/services/ssh/hostname)" > mon-ssh-aths

Retrieve GPG Public Keys 
~~~~~~~~~~~~~~~~~~~~~~~~
There are 2 GPG public keys required by the instance configuration, that you will need to 
copy to the new *Admin Workstation*.

To copy the *Submission Public Key*, download it from the *Source Interface* and import
it locally using the following commands:

.. code:: sh

 cd ~/Persistent/securedrop/install_files/ansible-base
 curl http://$(cat app-source-ths)/journalist-key > SecureDrop.asc
 gpg --import SecureDrop.asc

Validate that the imported key's fingerprint matches the one on your 
SecureDrop install. You can do this by first running the command:

.. code:: sh

  gpg --with-fingerprint --import-options import-show --dry-run --import SecureDrop.asc

Then, compare the returned fingerprint value with that advertised by your *Source Interface*,
using the command:

.. code:: sh

 curl http://$(cat app-source-ths)/metadata

To copy the OSSEC alert public key, first list available keys on the monitor server:

.. code:: sh
 
 ssh mon sudo gpg --homedir=/var/ossec/.gnupg  -k

Look for the key corresponding to the destination email address for OSSEC alerts. 
Then, import it locally using the following commands (substituting the 
appropriate email address for ``alerts@example.com``):

.. code:: sh

 ssh mon sudo gpg --homedir=/var/ossec/.gnupg --export --armor alerts@example.com > ossec.pub
 gpg --import ossec.pub
 
You will be prompted for the fingerprints for both keys during the next step. To view their fingerprints, use the command:

.. code:: sh
 
 gpg -k --fingerprint

Retrieve OSSEC alert configuration details
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In addition to the OSSEC alert GPG key you retrieved above, you'll also need 
the following configuration information:

 - SMTP server
 - SMTP port
 - SASL username
 - SASL domain
 - SASL password

To retrieve these values, use the following command in the terminal:

.. code:: sh

 ssh mon sudo cat /etc/postfix/sasl_passwd

This will return a line like:

.. code:: sh
 
 [smtp.gmail.com]:587 testossec@gmail.com:AwfulPassword

In this example, ``smtp.gmail.com`` is the SMTP server, ``587`` is the SMTP port,
``testossec`` is the SASL username, ``gmail.com`` is the SASL domain, and 
``AwfulPassword`` is the SASL password.

(Optional) Retrieve HTTPS certificate files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If your *Source Interface* was configured to use HTTPS, you will need to copy
three related files from the *Application Server* to the *Admin Workstation*.

To retrieve these files, use the commands:

.. code:: sh

   cd ~/Persistent/securedrop/install_files/ansible-base
   ssh app sudo tar -c -C /var/lib ssl/  | tar xvf - 

These commands will create a directory named 
``~/Persistent/securedrop/install_files/ansible-base/ssl``
on the *Admin Workstation*, containing your instance's SSL certificate, 
certificate key, and chain file. When prompted for the names of these files
during the next step, you should specify them relative to the 
``install_files/ansible-base`` directory, i.e. as ``ssl/mydomain.crt``.

Step 5: Configure and back up the application
=============================================

Next, configure the application using the files and info retrieved in the 
previous steps. To do so, connect to the Tor network on the
*Admin Workstation*, open a Terminal and run the following commands:

.. code:: sh

 cd ~/Persistent/securedrop
 ./securedrop-admin setup
 ./securedrop-admin sdconfig

.. note:: The ``./securedrop-admin setup`` command may take several minutes to complete, and may
 fail due to network issues. If it fails, it's safe to run again.

When prompted, fill in the values retrieved in the previous steps.

Once complete, configure the *Admin Workstation* using the command:

.. code:: sh

  ./securedrop-admin tailsconfig

This will set up desktop shortcuts for the *Source* and *Journalist Interfaces*,
and configure adminstrative access to the servers.

Once the ``./securedrop-admin tailsconfig`` command is complete: 
 - verify that the ``Hostname`` references in ``~/.ssh/config`` have been updated 
   to refer to Onion URLs instead of direct IP addresses,
 - verify that you can connect to 
   the servers using ``ssh app`` and ``ssh mon``, accepting the host verification
   prompt if necessary,
 - and verify that the desktop shortcuts for the *Source* and *Journalist Interfaces*
   work correctly, opening their respective homepages in the Tor Browser.

Next, back up the servers by running the following command in the terminal:

.. code:: sh 
 
 ./securedrop-admin backup


Step 6: Run the ``./securedrop-admin install`` command
======================================================

After the ``./securedrop-admin backup`` command completes successfully, you should
undo the changes made to enable temporary local SSH access, by running the following 
command:

.. code:: sh

 ./securedrop-admin install

Once the command completes successfully, your new *Admin Workstation* is ready
for use. To revert the changes made to enable temporary local SSH access, you
should reboot the servers, by issuing the following commands in a terminal:

.. code:: sh
 
 ssh app sudo reboot
 ssh mon sudo reboot

Step 7: Post-rebuild tasks
==========================

We recommend completing the following tasks after the rebuild:

 - Set up a new administration account on the *Journalist Interface*, by following
   :doc:`these instructions <create_admin_account>`
 - Verify that submissions can be decrypted, by going through the decryption 
   workflow with a new submission.
 - Back up your *Admin Workstation* using the process 
   :ref:`documented here <backup_workstations>`.
 - Delete invalid admin accounts in the *Journalist Interface*.
 - Restrict SSH access to the *Application* and *Monitor Servers* to valid 
   *Admin Workstions*. If your new *Admin Workstation* USB stick
   is the only one that should have SSH access to the servers, you can remove 
   access for any previous *Admin Workstations* from the terminal,  using the 
   commands:

   .. code:: sh

     cd ~/Persistent/securedrop
     ./securedrop-admin reset_admin_access

   You can also selectively remove invalid keys by logging on to the *Application*
   and *Monitor Servers* and editing the file ``~/.ssh/authorized_keys``, making 
   sure not to remove the public key belonging to your new *Admin Workstation*.
 - Optionally, set up :ref:`daily journalist alerts <daily_journalist_alerts>`, 
   by running ``./securedrop-admin sdconfig`` and providing a valid
   GPG key and fingerprint, along with the corresponding destination email address, then
   running ``./securedrop-admin install`` again to update the server configuration.
     
