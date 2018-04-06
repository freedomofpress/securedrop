SSH Over Local Network
======================

Under a production installation post-install, the default way to gain SSH
administrative access is over the Tor network. This provides a number of benefits:

* Allows remote administration outside of the local network
* Provides anonymity to an administrator while logging into the SecureDrop
  back-end.
* Can mitigate against an attacker on your local network attempting to exploit
  vulnerabilities against the SSH daemon.

Most administrators will need SSH access during the course of running a
SecureDrop instance and a few times a year for maintanence. So the
potential short-falls of having SSH over Tor aren't usually a big deal.
The cons of having SSH over Tor can include:

* Really slow and delayed remote terminal performance
* Allowing SSH access from outside of your local network can be seen as a
  potential larger security hole for some organizations. Particularly those
  with tight network security controls.

That being said, the default setting of only allowing SSH over Tor is a good fit
for most organizations. If you happen to require SSH restricted to the local
network instead please continue to read.


.. _ssh_over_local:

Configuring SSH for local access
--------------------------------

.. warning:: It is important that your firewall is configured adequately if you
          decide you need SSH over the local network. The install process locks
          down access as much as possible with net restrictions, SSH-keys, and
          google authenticator. However, you could still leave the interface
          exposed to unintended users if you did not properly follow our network
          firewall guide.

.. warning:: This setting will lock you out of SSH access to your instance if your
          *Admin Workstation* passes through a NAT in order to get to the
          SecureDrop servers. If you are unsure whether this is the case, please
          consult with your firewall configuration or network administrator.

.. note:: Whichever network you install from will be the one that SSH is
          restricted to post-install. This will come into play particularly if
          you have multiple network interfaces.

The setting that controls SSH over LAN access is set during the `sdconfig` step
of the install. Below is an example of what the prompt will look like. You can
answer either 'no' or 'false' when you are prompted for `Enable SSH over Tor`:

.. code:: sh

    $ ./securedrop-admin sdconfig

    Username for SSH access to the servers: vagrant
    Local IPv4 address for the Application Server: 10.0.1.4
    Local IPv4 address for the Monitor Server: 10.0.1.5
    Hostname for Application Server: app
    Hostname for Monitor Server: mon
    [...]
    Enable SSH over Tor: no

Then you'll have to run the installation script

.. code:: sh

    $ ./securedrop-admin install

.. note:: If you are migrating from a production install previously configured
          with SSH over Tor, you will be prompted to re-run the `install` portion
          twice. This is due to the behind the scenes configuration changes being
          done to switch between Tor and the local network.

Finally, re-configure your *Admin Workstation* as follows:

.. code:: sh

    $ ./securedrop-admin tailsconfig

Assuming everything is working you should be able to gain SSH access as follows

.. code:: sh

    $ ssh app
    $ ssh mon

