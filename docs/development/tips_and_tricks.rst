Tips & Tricks
=============

Using Tor Browser with the development environment
--------------------------------------------------

We strongly encourage sources to use the Tor Browser when they access
the Source Interface. Tor Browser is the easiest way for the average
person to use Tor without making potentially catastrophic mistakes,
makes disabling Javascript easy via the handy NoScript icon in the
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

To test the development environment in Tor Browser, you need to add an
exception to allow Tor Browser to access localhost:

#. Open the "Tor Browser" menu and click "Preferences..."
#. Choose the "Advanced" section and the "Network" subtab under it
#. In the "Connection" section, click "Settings..."
#. In the text box labeled "No Proxy for:", enter ``127.0.0.1``

   -  Note: for some reason, ``localhost`` doesn't work here.

#. Click "Ok" and close the Preferences window

You should now be able to access the development server in the Tor
Browser by navigating to ``127.0.0.1:8080`` and ``127.0.0.1:8081``.

.. _ssh_over_tor:

Connecting to VMs via SSH over Tor
----------------------------------

.. todo:: Replace all of this with nc, which is simpler, works well with
	  OpenSSH's ProxyCommand, and is included by default on Ubuntu and Mac
	  OS X.

connect-proxy (Ubuntu only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   sudo apt-get install connect-proxy

After installing connect-proxy via apt-get and appending the tor config options
to your local config, you can export the environment variable
``SECUREDROP_SSH_OVER_TOR=1`` in order to use ``vagrant ssh`` to access the
prod instances.  Here is an example of how that works:

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
      ProxyCommand connect -R remote -5 -S 127.0.0.1:9050 %h %p
    $ # ensure ATHS values are active in local Tor config:
    $ cat *-aths | sudo tee -a /etc/tor/torrc > /dev/null && sudo service tor reload
    $ vagrant ssh app-prod -c 'echo hello'   # works
    hello
    Connection to l57xhqhltlu323vi.onion closed.

If ``SECUREDROP_SSH_OVER_TOR`` is declared, Vagrant will look up the ATHS URLs
and ``HidServAuth`` values for each server by examining the contents of
``app-ssh-aths`` and ``mon-ssh-aths`` in ``./install_files/ansible-base``. You
can manually inspect these files to append values to your local ``torrc``, as
in the ``cat`` example above.  Note that the ``cat`` example above will also
add the ATHS info for the Document Interface, as well, which is useful for
testing.

torify (Ubuntu and Mac OS X)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Ubuntu

  ``torsocks`` should be installed by the tor package. If it is not installed,
  make sure you are using tor from the `Tor Project's repo
  <https://www.torproject.org/docs/debian.html.en>`__, and not Ubuntu's
  package.

- Mac OS X (Homebrew)

  .. code:: sh

     brew install torsocks

If you have torify on your system (``which torify``) and you're Tor running
in the background, simply prepend it to the SSH command:

.. code:: sh

    torify ssh admin@examplenxu7x5ifm.onion

Architecture Diagrams
---------------------

Some helpful diagrams for getting a sense of the SecureDrop application architecture are stored `here
<https://github.com/freedomofpress/securedrop/tree/develop/docs/diagrams>`_, including a high-level view of the SecureDrop database structure:

.. image:: ../diagrams/securedrop-database.png
