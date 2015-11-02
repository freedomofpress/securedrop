Getting Started
===============

Prerequisites
-------------

SecureDrop is a multi-machine design. To make development and testing easy, we
provide a set of virtual environments, each tailored for a specific type of
development task. We use Vagrant and VirtualBox to conveniently develop with a
set of virtual environments, and our Ansible playbooks can provison these
environments on either virtual machines or physical hardware.

To get started, you will need to install Vagrant, VirtualBox, and Ansible on
your development workstation.


Ubuntu/Debian
~~~~~~~~~~~~~

.. note:: Tested on: Ubuntu 14.04

.. code:: sh

   sudo apt-get install -y dpkg-dev virtualbox-dkms linux-headers-$(uname -r) build-essential git

We recommend using the latest stable version of Vagrant (``1.7.2`` at the time
of this writing), which is newer than what is in the Ubuntu repositories at the
time of this writing. Download the current version from the `Vagrant Downloads
page`_. We *do not* recommend using the version of Vagrant available from
Ubuntu's package repositories because it is significantly out of date and will
not work with SecureDrop (`GitHub #932`_).

.. _`Vagrant Downloads page`: https://www.vagrantup.com/downloads.html
.. _`GitHub #932`: https://github.com/freedomofpress/securedrop/pull/932

.. code:: sh

    sudo dpkg -i vagrant.deb
    sudo dpkg-reconfigure virtualbox-dkms

Finally, install Ansible so it can be used with Vagrant to automatically
provision VMs. We recommend installing Ansible from PyPi with ``pip`` to ensure
you have the latest stable version.

.. code:: sh

    sudo apt-get install python-pip
    sudo pip install -U ansible

If you're using Ubuntu, you can install a sufficiently recent version of
Ansible from backports (if you prefer): ``sudo apt-get install
ansible/trusty-backports``

.. note:: Tested: Ansible 1.9.4

.. warning:: We do not recommend installing vagrant-cachier. It destroys apt's
	     state unless the VMs are always shut down/rebooted with Vagrant,
	     which conflicts with the tasks in the Ansible playbooks. The
	     instructions in Vagrantfile that would enable vagrant-cachier are
	     currently commented out.

Mac OS X
~~~~~~~~

Install the dependencies for the development environment:

#. Vagrant_
#. VirtualBox_
#. Ansible_.

   There are several ways to install Ansible on a Mac. We recommend installing
   from PyPi using ``pip`` so you will get the latest stable version:

   .. code:: sh

      sudo easy_install pip && sudo pip install -U ansible

.. _Vagrant: http://www.vagrantup.com/downloads.html
.. _VirtualBox: https://www.virtualbox.org/wiki/Downloads
.. _Ansible: http://docs.ansible.com/intro_installation.html

Clone the repository
--------------------

Once you've installed the prerequisites for the development environment,
use git to clone the SecureDrop repo.

.. code:: sh

   git clone https://github.com/freedomofpress/securedrop.git

SecureDrop uses a branching model based on `git-flow
<http://nvie.com/posts/a-successful-git-branching-model/>`__.  The ``master``
branch always points to the latest stable release. Use this branch if you are
interested in installing or auditing SecureDrop.  Development for the upcoming
release of SecureDrop takes place on ``develop``, which is the default
branch. If you want to contribute, you should branch from and submit pull
requests to ``develop``.

.. todo:: The branching model should be documented separately, in a
	  "Contributing guidelines" document. We are also going to move away
	  from git-flow soon because it sucks.

Virtual Environments
--------------------

Overview
~~~~~~~~

There are several predefined virtual environments in the Vagrantfile:
development, staging, and prod (production).

-  **development**: for working on the application code

   -  Source Interface: localhost:8080
   -  Document Interface: localhost:8081

-  **app-staging**: for working on the environment and hardening

   -  Source Interface: localhost:8082
   -  Document Interface: localhost:8083
   -  The interfaces and SSH are also available over Tor.
   -  A copy of the the onion URLs for source, document and SSH access
      are written to the Vagrant host's ansible-base directory. The
      files will be named: app-source-ths, app-document-aths,
      app-ssh-aths

-  **mon-staging**: for working on the environment and hardening

   -  OSSEC alert configuration is in
      install\_files/ansible-base/staging-specific.yml

-  **app-prod**: This is like a production installation with all of the
   hardening applied but virtualized

   -  A copy of the the onion URLs for source, document and SSH access
      are written to the Vagrant host's ansible-base directory. The
      files will be named: app-source-ths, app-document-aths,
      app-ssh-aths
   -  Putting the AppArmor profiles in complain mode (default) or
      enforce mode can be done with the Ansible tags apparmor-complain
      or apparmor-enforce.

-  **mon-prod**: This is like a production installation with all of the
   hardening applied but virtualized

If you plan to alter the configuration of any of these machines, make sure to
review the :doc:`Development Guide for Serverspec Tests <spec_tests>`.

Development
~~~~~~~~~~~

This VM is intended for rapid development on the SecureDrop web application. It
syncs the top level of the SecureDrop repo to the ``/vagrant`` directory on the
VM, which means you can use your favorite editor on your host machine to edit
the code. This machine has no security hardening or monitoring.

This is the default VM, so you don't need to specify the ``development``
machine name when running commands like ``vagrant up`` and ``vagrant ssh``. Of
course, you can specify the name if you want to.

.. code:: sh

   vagrant up
   vagrant ssh
   cd /vagrant/securedrop
   ./manage.py run         # run development servers
   ./manage.py test        # run the unit and functional tests
   ./manage.py reset       # resets the state of the development instance
   ./manage.py add_admin   # create a user to use when logging in to the Document Interface

SecureDrop consists of two separate web appications (the Source Interface and
the Document Interface) that run concurrently. The development servers will
detect code changes when they are saved and automatically reload.

Staging
~~~~~~~

The staging environment is almost identical to the production, but the security
hardening is weakened slightly to allow direct access (without Tor) to SSH and
the web server. This is a convenient environment to test how changes work
across the full stack.

.. todo:: Explain why we allow direct access on the staging environment

If you want to receive OSSEC alerts or change any other settings, you will need
to fill out your local copy of
``securedrop/install_files/ansible_base/staging-specific.yml``.

.. code:: sh

   vagrant up /staging$/
   vagrant ssh app-staging
   sudo su
   cd /var/www/securedrop
   ./manage.py add_admin
   ./manage.py test

Prod
~~~~

You will need to fill out the production configuration file:
``securedrop/install_files/ansible_base/prod-specific.yml``.  Part of the
production playbook validates that staging values are not used in
production. One of the values it verifies is that the user Ansible runs as is
not ``vagrant`` To be able to run this playbook in a virtualized environment
for testing, you will need to disable the ``validate`` role, which you can do
by running ``export SECUREDROP_PROD_SKIP_TAGS=validate`` before provisioning.

To create only the prod servers, run:

.. code:: sh

   vagrant up /prod$/
   vagrant ssh app-prod
   sudo su
   cd /var/www/securedrop/
   ./manage.py add_admin

In order to access the servers after the install is completed you will need to
install and configure a proxy tool to proxy your SSH connection over Tor.
Torify and connect-proxy are two tools that can be used to proxy SSH
connections over Tor.

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

Tips & Tricks
-------------

Using Tor Browser with the development environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We strongly encourage sources to use the Tor Browser when they access
the Source Interface. Tor Browser is the easiest way for the average
person to use Tor without making potentially catastrophic mistakes,
makes disable Javascript easy via the handy NoScript icon in the
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

