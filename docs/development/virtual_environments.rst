Virtual Environments
====================

.. note:: If you have errors with mounting shared folders in the Vagrant guest
          machine, you should look at `Github issue #1381`_.

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
-----------

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
   ./manage.py add-admin   # create a user to use when logging in to the Document Interface

SecureDrop consists of two separate web appications (the Source Interface and
the Document Interface) that run concurrently. The development servers will
detect code changes when they are saved and automatically reload.

Staging
-------

The staging environment is almost identical to the production, but the security
hardening is weakened slightly to allow direct access (without Tor) to SSH and
the web server. This is a convenient environment to test how changes work
across the full stack.

.. todo:: Explain why we allow direct access on the staging environment

If you want to receive OSSEC alerts or change any other settings, you will need
to fill out your local copy of
``./install_files/ansible_base/staging-specific.yml``.

.. code:: sh

   vagrant up /staging/
   vagrant ssh app-staging
   sudo su
   cd /var/www/securedrop
   ./manage.py add-admin
   ./manage.py test

Prod
----

You will need to fill out the production configuration file:
``./install_files/ansible_base/prod-specific.yml``.  Part of the
production playbook validates that staging values are not used in
production. One of the values it verifies is that the user Ansible runs as is
not ``vagrant`` To be able to run this playbook in a virtualized environment
for testing, you will need to disable the ``validate`` role, which you can do
by running ``export SECUREDROP_PROD_SKIP_TAGS=validate`` before provisioning.

To create only the prod servers, run:

.. code:: sh

   vagrant up /prod/
   vagrant ssh app-prod
   sudo su
   cd /var/www/securedrop/
   ./manage.py add-admin

In order to access the servers after the install is completed you will need to
install and configure a proxy tool to proxy your SSH connection over Tor.
Torify and connect-proxy are two tools that can be used to proxy SSH
connections over Tor.
