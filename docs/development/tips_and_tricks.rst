Tips & Tricks
=============

Using Tor Browser with the Development Environment
--------------------------------------------------

We strongly encourage sources to use the Tor Browser when they access
the Source Interface. Tor Browser is the easiest way for the average
person to use Tor without making potentially catastrophic mistakes,
makes disabling JavaScript easy via the handy NoScript icon in the
toolbar, and prevents state about the source's browsing habits
(including their use of SecureDrop) from being persisted to disk.

Since Tor Browser is based on an older version of Firefox (usually the
current ESR release), it does not always render HTML/CSS the same as
other browsers (especially more recent versions of browsers). Therefore,
we recommend testing all changes to the web application in the Tor
Browser instead of whatever browser you normally use for web
development. Unfortunately, it is not possible to access the local
development servers by default, due to Tor Browser's proxy
configuration.

To test the development environment in Tor Browser, you need to modify Tor
Browser's default settings to prevent localhost from being resolved by the
proxy:

#. In a new tab, navigate to ``about:config``.
#. Click "I accept the Risk!"
#. In the search bar, enter ``network.proxy.allow_hijacking_localhost``.
#. The default value is true. Double-click to set it to false.

Now you should be able to navigate to ``127.0.0.1:8080`` and ``127.0.0.1:8081``
in Tor Browser. For some reason, you have to use ``127.0.0.1`` -- ``localhost``
doesn't work.

The modified value persists across restarts of Tor Browser.

.. _updating_pip_dependencies:

Upgrading or Adding Python Dependencies
---------------------------------------

We use a `pip-compile <http://nvie.com/posts/better-package-management/>`_
based workflow for adding Python dependencies. If you would like to add a Python
dependency, instead of editing the ``securedrop/requirements/*.txt`` files
directly, please:

  #. Edit the relevant ``*.in`` file in ``securedrop/requirements/``
  #. Use the following shell script to generate
     ``securedrop/requirements/*.txt`` files:

     .. code:: sh

        make update-pip-requirements

  #. Commit both the ``securedrop/requirements/*.in`` and
     ``securedrop/requirements/*.txt`` files

.. _ssh_over_tor:

Connecting to VMs via SSH Over Tor
----------------------------------

Ubuntu/Debian Setup
~~~~~~~~~~~~~~~~~~~
You will need to install a specific variant of the ``nc`` tool
in order to support the ``-x`` option for specifying a proxy host.
macOS already runs the OpenBSD variant by default.

.. code:: sh

   sudo apt-get install netcat-openbsd

After installing ``netcat-openbsd`` and appending the Tor config options
to your local torrc, you can export the environment variable
``SECUREDROP_SSH_OVER_TOR=1`` in order to use ``vagrant ssh`` to access the
staging or prod instances over Tor. Here is an example of how that works:

.. code:: sh

    $ vagrant up --provision /prod/     # restricts SSH to Tor after final reboot
    $ vagrant ssh-config app-prod       # will show incorrect info due to lack of env var
    Host app-prod
      HostName 127.0.0.1
      User vagrant
      Port 2201
      UserKnownHostsFile /dev/null
      StrictHostKeyChecking no
      PasswordAuthentication no
      IdentityFile /home/conor/.vagrant.d/insecure_private_key
      IdentitiesOnly yes
      LogLevel FATAL

    $ vagrant ssh app-prod -c 'echo hello'   # will fail due to incorrect ssh-config
    ssh_exchange_identification: read: Connection reset by peer

    $ export SECUREDROP_SSH_OVER_TOR=1       # instruct Vagrant to use Tor for SSH
    $ vagrant ssh-config app-prod            # will show correct info, with ProxyCommand
    Host app-prod
      HostName l57xhqhltlu323vi.onion
      User vagrant
      Port 22
      UserKnownHostsFile /dev/null
      StrictHostKeyChecking no
      PasswordAuthentication no
      IdentityFile /home/conor/.vagrant.d/insecure_private_key
      IdentitiesOnly yes
      LogLevel FATAL
      ProxyCommand nc -x 127.0.0.1:9050 %h %p

    $ # ensure ATHS values are active in local Tor config:
    $ cat *-aths | sudo tee -a /etc/tor/torrc > /dev/null && sudo service tor reload
    $ vagrant ssh app-prod -c 'echo hello'   # works
    hello
    Connection to l57xhqhltlu323vi.onion closed.

If ``SECUREDROP_SSH_OVER_TOR`` is true, Vagrant will look up the ATHS URLs
for each server by examining the contents of ``app-ssh-aths`` and ``mon-ssh-aths``
in ``./install_files/ansible-base``. You can manually inspect these files
to append values to your local ``torrc``, as in the ``cat`` example above.
Note that the ``cat`` example above will also add the ATHS info for the
*Journalist Interface*, as well, which is useful for testing.

.. note:: The instructions above refer to VMs set up with v2 onion services. If
          v3 onion services are configured instead, the steps required for the
          local ``tor`` setup will differ. You will need to add a
          ``ClientOnionAuthDir`` directive to ``torrc``, pointing to a directory
          containing the ``*.auth_private`` files created during the installation
          process under ``install_files/ansible-base``.

Architecture Diagrams
---------------------

Some helpful diagrams for getting a sense of the SecureDrop application architecture are stored `here
<https://github.com/freedomofpress/securedrop/tree/develop/docs/diagrams>`_, including a high-level view of the SecureDrop database structure:

.. image:: ../diagrams/securedrop-database.png
