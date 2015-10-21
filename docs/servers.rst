Set up the Servers
==================

Now that the firewall is set up, you can plug the *Application Server*
and the *Monitor Server* into the firewall. If you are using a setup
where there is a switch on the LAN port, plug the *Application Server*
into the switch and plug the *Monitor Server* into the OPT1 port.

Install Ubuntu Server 14.04 (Trusty) on both servers. This setup is
fairly easy, but please note the following:

-  Since the firewall is configured to give the servers a static IP
   address, you will have to manually configure the network with those
   values.
-  The hostname for the servers are, conventionally, ``app`` and
   ``mon``. Adhering to this isn't necessary, but it will make the rest
   of your install easier.
-  The username and password for these two servers **must be the same**.

For detailed instructions on installing and configuring Ubuntu for use
with SecureDrop, see our :doc:`ubuntu_config`.

When you are done, make sure you save the following information:

-  The IP address of the App Server
-  The IP address of the Monitor Server
-  The non-root user's name and password for the servers.

Before continuing, you'll also want to make sure you can connect to the
App and Monitor servers. You should still have the Admin Workstation
connected to the firewall from the firewall setup step. In the terminal,
verify that you can SSH into both servers, authenticating with your
password:

.. code:: sh

    ssh <username>@<App IP address>
    ssh <username>@<Monitor IP address>

Once you have verified that you can connect, continue with the
installation. If you cannot connect, check the firewall logs.

