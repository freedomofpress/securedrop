.. _ci_tests:

Testing: CI
===========

The SecureDrop project uses CircleCI_ for running automated test suites on code changes:

.. _CircleCI: http://circleci.com/gh/freedomofpress/securedrop/

CI test layout
--------------

The relevant files for configuring the CI tests are: ::

    ├── .circleci <--- folder contains config for CircleCI
    ├── devops
    │   ├── inventory <-- environment specific inventory
    │   ├── playbooks <-- playbooks to start CI boxes
    │   ├── scripts   <-- shell wrapper scripts
    │   ├── templates <-- contains templates for ansible tasks
    │   └── vars <-- environment specific variables
    └── Makefile  <-- defines make task shortcuts

The files under ``devops/`` are used to create a minimized staging environment
on AWS EC2. The CircleCI host is used as the Ansible controller to provision
the machines and run the :ref:`config_tests` against them.

Running the CI staging environment
----------------------------------

The staging environment tests will run automatically in CircleCI,
when changes are submitted by Freedom of the Press Foundation staff
(i.e. members of the ``freedomofpress`` GitHub organization).

It also performs basic linting and validation, e.g. checking for mistakes in
the Sphinx documentation.

.. tip:: You will need an Amazon Web Services EC2 account to proceed.
         See the `AWS Getting Started Guide`_ for detailed instructions.

.. _AWS Getting Started Guide: https://aws.amazon.com/ec2/getting-started/

In addition to an EC2 account, you will need a working `Docker installation`_ in
order to run the container that builds the deb packages.

You can verify that your Docker installation is working by running
``docker run hello-world`` and confirming you see "Hello from Docker" in the
output as shown below:

.. code:: sh

    $ docker run hello-world

    Hello from Docker!
    This message shows that your installation appears to be working correctly.
    ...

.. _Docker installation: https://www.docker.com/community-edition#/download

Setup environment parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Source the setup script using the following command:

.. code:: sh

    source ./devops/scripts/local-setup.sh

You will be prompted for the values of the required environment variables. There
are some defaults set that you may want to change. You will need to determine
the value of your VPC ID to use which is outside the scope of this guide.


Use Makefile to provision hosts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Run ``make help`` to see the full list of CI commands in the Makefile:

.. code:: sh

    $ make help
    Makefile for developing and testing SecureDrop.
    Subcommands:
        docs: Build project documentation in live reload for editing.
        docs-lint: Check documentation for common syntax errors.
        ci-spinup: Creates AWS EC2 hosts for testing staging environment.
        ci-teardown: Destroy AWS EC2 hosts for testing staging environment.
        ci-run: Provisions AWS EC2 hosts for testing staging environment.
        ci-test: Tests AWS EC2 hosts for testing staging environment.
        ci-go: Creates, provisions, tests, and destroys AWS EC2 hosts
               for testing staging environment.
        ci-debug: Prevents automatic destruction of AWS EC2 hosts on error.

To run the tests locally:

.. code:: sh

    make ci-debug # hosts will not be destroyed automatically
    make ci-go

You can use ``make ci-run`` to provision the remote hosts while making changes,
including rebuilding the Debian packages used in the Staging environment.
See :doc:`virtual_environments` for more information.

Note that if you typed ``make ci-debug`` above, you will have to manually remove
a blank file in ``${HOME}/.FPF_CI_DEBUG`` and then run ``make ci-teardown`` to
bring down the CI environment. Otherwise, specifically for AWS, you will be
charged hourly charges until those machines are terminated.
