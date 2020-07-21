.. _ci_tests:

Testing: CI
===========

The SecureDrop project uses CircleCI_ for running automated test suites on code changes.

.. _CircleCI: https://circleci.com/gh/freedomofpress/securedrop

The relevant files for configuring the CI tests are the ``Makefile`` in
the main repo, the configuration file at ``.circleci/config.yml``, and
the scripts in ``devops/``. You may want to consult the
`CircleCI Configuration Reference <https://circleci.com/docs/2.0/configuration-reference/>`__
to interpret the configuration file. Review the ``workflows`` section of the
configuration file to understand which jobs are run by CircleCI.

The files under ``devops/`` are used to create a libvirt-compatible environment on GCE.
The GCE host is used as the Ansible controller, mimicking a developer's laptop,
to provision the machines and run the :ref:`tests <config_tests>` against them.

.. note:: We skip unnecessary jobs, such as the staging run, for pull requests that only
  affect the documentation; to do so, we check whether the branch name begins with
  ``docs-``. These checks are enforced in different parts of the configuration,
  mainly within the ``Makefile``.

.. warning:: In CI, we rebase branches in PRs on HEAD of the target branch.
  This rebase does not occur for branches that are not in PRs.
  When a branch is pushed to the shared ``freedomofpress`` remote, CI will run,
  a rebase will not occur, and since opening a
  `PR does not trigger a re-build <https://discuss.circleci.com/t/pull-requests-not-triggering-build/1213>`_,
  the CI build results are not shown rebased on the latest of the target branch.
  This is important to maintain awareness of if your branch is behind the target
  branch. Once your branch is in a PR, you can rebuild, push an additional
  commit, or manually rebase your branch to update the CI results.

Running the CI Staging Environment
----------------------------------

The staging environment tests will run automatically in CircleCI, when
changes are submitted by Freedom of the Press Foundation staff (i.e. members
of the ``freedomofpress`` GitHub organization). The tests also perform
basic linting and validation, like checking for formatting errors in the
Sphinx documentation.

.. tip:: You will need a Google Cloud Platform account to proceed.
         See the `Google Cloud Platform Getting Started Guide`_ for detailed instructions.

.. _Google Cloud Platform Getting Started Guide: https://cloud.google.com/getting-started/

In addition to a GCP account, you will need a working `Docker installation`_ in
order to run the container that builds the deb packages.

You can verify that your Docker installation is working by running
``docker run hello-world`` and confirming you see "Hello from Docker" in the
output as shown below:

.. code:: sh

    $ docker run hello-world

    Hello from Docker!
    This message shows that your installation appears to be working correctly.
    ...

.. _Docker installation: https://docs.docker.com/install/

Setup Environment Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Source the setup script using the following command:

.. code:: sh

    source ./devops/gce-nested/ci-env.sh

You will be prompted for the values of the required environment variables. There
are some defaults set that you may want to change. You will need to export
``GOOGLE_CREDENTIALS`` with authentication details for your GCP account,
which is outside the scope of this guide.

Use Makefile to Provision Hosts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run ``make help`` to see the full list of CI commands in the Makefile:

.. code:: sh

    $ make help
    Makefile for developing and testing SecureDrop.
    Subcommands:
        ci-go                      Creates, provisions, tests, and destroys GCE host for testing staging environment.
        ci-go-xenial               Creates, provisions, tests, and destroys GCE host for testing staging environment under xenial.
        ci-lint                    Runs linting in linting container.
        ci-teardown                Destroys GCE host for testing staging environment.

To run the tests locally:

.. code:: sh

    make ci-go

You can use ``./devops/gce-nested/ci-runner.sh`` to provision the remote hosts
while making changes, including rebuilding the Debian packages used in the
Staging environment. See :doc:`virtual_environments` for more information.
