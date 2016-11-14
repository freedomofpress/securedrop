Virtual Environments
====================

.. note:: If you have errors with mounting shared folders in the Vagrant guest
          machine, you should look at `GitHub #1381`_.

.. _`GitHub #1381`: https://github.com/freedomofpress/securedrop/issues/1381

Overview
--------

There are several predefined virtual environments in the Vagrantfile:
development, staging, and prod (production).

development
    For working on the application code. Forwarded ports:

    -  Source Interface: localhost:8080
    -  Journalist Interface: localhost:8081

app-staging
    For working on the application code in a more realistic environment,
    with most system hardening active.
    The interfaces and SSH are also available over Tor.
    A copy of the the Onion URLs for Source and Journalist Interfaces,
    as well as SSH access, are written to the Vagrant host's
    ``install_files/ansible-base`` directory, named:

    - ``app-source-ths``
    - ``app-journalist-aths``
    - ``app-ssh-aths``

    The AppArmor profiles run complain mode to aid in debugging.

    Forwarded ports:

    -  Source Interface: localhost:8082
    -  Journalist Interface: localhost:8083

mon-staging
    For working on OSSEC monitoring rules, with most system hardening active.
    OSSEC alert configuration is in
    ``install_files/ansible-base/staging-specific.yml``.
    A copy of the the Onion URL for SSH acces is written to the Vagrant host's
    ``install_files/ansible-base`` directory, named:

    - ``mon-ssh-aths``

    Direct SSH access is still available via Vagrant for staging hosts, so you
    can use ``vagrant ssh app-staging`` and ``vagrant ssh mon-staging``
    to start an interactive session.

app-prod
    This is like a production installation with all of the system
    hardening active, but virtualized, rather than running on hardware.
    A copy of the the Onion URLs for Source and Journalist Interfaces,
    as well as SSH access, are written to the Vagrant host's
    ``install_files/ansible-base`` directory, named:

    - ``app-source-ths``
    - ``app-journalist-aths``
    - ``app-ssh-aths``

    There are no active forwarded ports for the Journalist and Source Interfaces
    on ``app-prod``. You must use the Onion URLs to view the pages over Tor.

mon-prod
    This is like a production installation with all of the system
    hardening active, but virtualized, rather than running on hardware.
    You will need to configure prod-like secrets in 
    ``install_files/ansible-base/prod-specific.yml``, or export
    ``ANSIBLE_ARGS=="--skip-tags validate"`` to skip the tasks
    that prevent the prod playbook from running with Vagrant-specific info.

    Direct SSH access is not available in the prod environment.
    You will need to log in over Tor after initial provisioning. See
    :ref:`ssh_over_tor` for more info.

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
   ./manage.py add-admin   # create a user to use when logging in to the Journalist Interface

SecureDrop consists of two separate web appications (the Source Interface and
the Journalist Interface) that run concurrently. The development servers will
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
``./install_files/ansible-base/staging-specific.yml``.

.. code:: sh

   vagrant up /staging/
   vagrant ssh app-staging
   sudo su
   cd /var/www/securedrop
   ./manage.py add-admin
   ./manage.py test

Prod
----

You will need to fill out the production configuration file at
``install_files/ansible-base/prod-specific.yml`` with custom secrets.
The production playbook validates that staging values are not used in
production. One of the values it verifies is that the user Ansible runs as is
not ``vagrant`` To be able to run this playbook in a virtualized environment
for testing, you will need to disable the ``validate`` role, which you can do
by running ``export ANSIBLE_ARGS="--skip-tags validate"`` before provisioning.

To create only the prod servers, run:

.. code:: sh

   vagrant up /prod/
   vagrant ssh app-prod
   sudo su
   cd /var/www/securedrop/
   ./manage.py add-admin

In order to access the servers after the install is completed you will need to
install and configure a proxy tool to
:ref:`proxy your SSH connection over Tor<ssh_over_tor>`.
