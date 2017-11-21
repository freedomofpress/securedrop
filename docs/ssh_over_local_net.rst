SSH Over Local Network
======================

Under a production installation post-install, the default way to gain ssh
administrative access is over the Tor network. This provides a number of benefits:

* Allows remote administration outside of the local network
* Provides anonymity to an administrator while logging into the SecureDrop
  back-end.
* Can mitigate against an attacker on your local network attempting to exploit
  vulnerabilities against the SSHd daemon.

Most administrators will never need SSH access during the course of running a
SecureDrop instance so the potential short-falls of having ssh over tor aren't
usually a big deal. The cons of having SSH over tor can include:

* Really slow and delayed remote terminal performance
* Allowing SSH access from outside of your local network can be seen as a
  potential larger security hole for some organizations. Particularly those
  with tight network security controls.

That being said, the default setting of only allowing ssh over tor is a good fit
for most organizations. If you happen to require ssh restricted to the local
network instead please continue to read.


.. _ssh_over_local:

Configuring SSH for local access
--------------------------------

.. warning:: It is important that your firewall is configured adequately if you
          decide you need SSH over the local network. The install process locks
          down access as much as possible with net restrictions, ssh-keys, and
          google authenticator. However, you could still leave the interface
          exposed to unintended users if you did not properly follow our network
          firewall guide.

The setting that controls ssh local-net access is set during the `sdconfig` step
of the install.

.. note:: Whichever network you install from will be the one that SSH is
          restricted to post-install. This will come into play particularly if
          you have multiple network interfaces.

The workflow for configuration will look like this (answer 'no' or 'false') to
the following :

.. code:: sh

    $ ./securedrop-admin sdconfig

    INFO: Configuring SecureDrop site-specific information
    [WARNING]: provided hosts list is empty, only localhost is available


    PLAY [Display message about upcoming interactive prompts.]
    ***********************************************************************

    TASK [debug]
    ***********************************************************************
    ok: [localhost] => {
        "msg": "You will need to fill out the following prompts in order to
        configure your SecureDrop instance. After entering all prompts, the
        variables will be validated and any failures displayed. See the docs
        for more information https://docs.securedrop.org/en/stable"
        }

    Enable SSH over Tor - alternatively ssh over local net [true]: no


Then as usual you'll run

.. code:: sh

    $ ./securedrop-admin install
    $ ./securedrop-admin tailsconfig
