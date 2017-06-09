.. _ci_tests:

Testing: CI
===========

The SecureDrop project uses multiple automated third-party solutions
for running automated test suites on code changes:

  * Travis_
  * CircleCI_

.. _Travis: https://travis-ci.org/freedomofpress/securedrop/
.. _CircleCI: http://circleci.com/gh/freedomofpress/securedrop/

Travis tests
------------

The Travis_ test suite provisions the development VM and runs the application
test suite against the latest version of the code. It also performs basic
linting and validation, e.g. checking for mistakes in the Sphinx documentation
(see :doc:`documentation_guidelines`).

CI test layout
--------------

The relevant files for configuring the CI tests are: ::

    ├── circle.yml
    ├── devops
    │   ├── ansible_env
    │   ├── inventory
    │   │   └── staging
    │   ├── playbooks
    │   │   ├── aws-ci-startup.yml
    │   │   ├── aws-ci-teardown.yml
    │   │   └── reboot_and_wait.yml
    │   ├── scripts
    │   │   ├── ci-runner.sh
    │   │   ├── ci-spinup.sh
    │   │   ├── ci-teardown.sh
    │   │   └── spin-run-test.sh
    │   ├── templates
    │   │   └── ssh_config
    │   └── vars
    │       └── staging.yml
    └── .travis.yml

The files under ``devops/`` are used to create a minimized staging environment
on AWS EC2. The CircleCI host is used as the Ansible controller to provision
the machines and run the :ref:`config_tests` against them.

Running the CI staging environment
----------------------------------

The staging environment tests will run automatically in CircleCI,
when changes are submitted by Freedom of the Press Foundation staff
(i.e. members of the ``freedomofpress`` GitHub organization).

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

Create AWS EC2 config script
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a file ``aws-env.sh`` with contents: ::

    # The BUILD_NUM string must be unique, otherwise users with the same
    # creds will clobber CI runs. In CircleCI this value maps to the UID of
    # the build, so that multiple builds can run in parallel.
    export BUILD_NUM="$USER"
    export CI_AWS_REGION=us-west-1
    export CI_AWS_TYPE=t2.small
    # The VPC ID below is invalid.
    export CI_AWS_VPC_ID=vpc-12345678
    export CI_SD_ENV=staging
    export FPF_CI=true
    export FPF_GRSEC=false

Then run ``source aws-env.sh`` to populate the environment variables.
Note you'll need to create a value for ``CI_AWS_VPC_ID`` if you do not
have access to the FPF credentials used for the SecureDrop CI pipeline.
The important attributes are whitelisting inter-machine communication on
ports 1514 and 1515 to support OSSEC registration and monitoring.


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
