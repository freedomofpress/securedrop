Set up the Servers
==================

Now that the firewall is set up, you can plug the *Application Server*
and the *Monitor Server* into the firewall. If you are using a setup
where there is a switch on the LAN port, plug the *Application Server*
into the switch and plug the *Monitor Server* into the OPT1 port.

Install Ubuntu
--------------

Install Ubuntu Server 14.04 (Trusty) on both servers. This setup is
fairly easy, but please keep the following in mind:

- Since the firewall is configured to give the servers a static IP
  address, you will have to manually configure the network on each
  server with the values that were used during the Network Firewall
  setup.
- The hostname for the servers are, conventionally, ``app`` and
  ``mon``. Adhering to this isn't necessary, but it will make the rest
  of your install easier.
- The username and password for these two servers **must be the
  same**.

For detailed instructions on installing and configuring Ubuntu for use
with SecureDrop, see our :doc:`ubuntu_install`.

When you are done, make sure you save the following information:

-  The IP address of the App Server
-  The IP address of the Monitor Server
-  The non-root user's name and password for the servers.

Test Connectivity
-----------------

Now that both the network firewall and the servers are connected and
configured, you should make sure you can connect from the Admin
Workstation to both of the servers before continuing with the
installation.

In a terminal, verify that you can SSH into both servers,
authenticating with your password:

.. code:: sh

    $ ssh <username>@<App IP address> hostname
    app
    $ ssh <username>@<Monitor IP address> hostname
    mon

.. tip:: If you cannot connect, check the network firewall logs for
         clues.

Set up SSH keys
---------------

Ubuntu's default SSH configuration authenticates users with their
passwords; however, public key authentication is more secure, and once
it's set up it is also easier to use. In this section, we will create
a new SSH key for authenticating to both servers. Since the Admin Live
USB was set up with `SSH Client Persistence`_, this key will be saved
on the Admin Live USB and can be used in the future to authenticate to
the servers in order to perform administrative tasks.

.. _SSH Client Persistence: https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html#index3h2

First, generate the new SSH keypair:

::

    $ ssh-keygen -t rsa -b 4096

You'll be asked to "enter file in which to save the key." Type
**Enter** to use the default location.

If you choose to passphrase-protect this key, you must use a strong,
diceword-generated, passphrase that you can manually type (as Tails'
pinentry will not allow you to copy and paste a passphrase). It is also
acceptable to leave the passphrase blank in this case.

.. todo:: Not sure if we should encourage people to put a passphrase
          on this key. It's already on the encrypted persistence of a
          Tails USB, so by the same logic that we use to justify not
          passphrase-protecting the GPG key on the SVS, this key
          should not be passphrase protected either. It also reduces
          credential juggling and is one less thing to
          forget/lose/actually be a bad passphrase because we're
          asking people to keep track of so many of them.

	  I also tend to agree with Joanna Rutkowska that encrypted
	  private keys are security theater
	  (http://blog.invisiblethings.org/keys/).

Once the key has finished generating, you need to copy the public key
to both servers. Use ``ssh-copy-id`` to copy the public key to each
server, authenticating with your password:

.. code:: sh

    $ ssh-copy-id <username>@<App IP address>
    $ ssh-copy-id <username>@<Mon IP address>

Verify that you are able to authenticate to both servers by running
the below commands. You should not be prompted for a passphrase
(unless you chose to passphrase-protect the key you just created).

.. code:: sh

    $ ssh <username>@<App IP address> hostname
    app
    $ ssh <username>@<Monitor IP address> hostname
    mon

