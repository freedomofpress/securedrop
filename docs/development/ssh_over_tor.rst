Connecting to VMs via SSH over Tor
==================================

.. todo:: Replace all of this with nc, which is simpler, works well with
	  OpenSSH's ProxyCommand, and is included by default on Ubuntu and Mac
	  OS X.

connect-proxy (Ubuntu only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

