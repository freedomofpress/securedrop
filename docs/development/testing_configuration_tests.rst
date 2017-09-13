.. _config_tests:

Testing: Configuration Tests
============================

Testinfra_ tests verify the end state of the Vagrant machines. Any
changes to the Ansible configuration should have a corresponding
spectest.

.. _Testinfra: https://testinfra.readthedocs.io/en/latest/

Installation
------------

.. code:: sh

    pip install -r securedrop/requirements/develop-requirements.txt

Running the config tests
------------------------

In order to run the tests, first create and provision the VM you intend
to test. For the development VM:

.. code:: sh

    vagrant up development

For the staging VMs:

.. code:: sh

    make build-debs
    vagrant up /staging/

Running all VMs concurrently may cause performance
problems if you have less than 8GB of RAM. You can isolate specific
machines for faster testing:

.. code:: sh

    ./testinfra/test.py development
    ./testinfra/test.py app-staging
    ./testinfra/test.py mon-staging

.. note:: The config tests for the ``app-prod`` and ``mon-prod`` hosts are
          incomplete. Further changes are necessary to run the tests via
          SSH over Authenticated Tor Hidden Service (ATHS), for both local
          testing via Vagrant and automated testing via CI.

Test failure against any host will generate a report with informative output
about the specific test that triggered the error. The wrapper script
will also exit with a non-zero status code.

Updating the config tests
-------------------------

Changes to the Ansible config should result in failing config tests, but
only if an existing task was modified. If you add a new task, make
sure to add a corresponding spectest to validate that state after a
new provisioning run. Tests import variables from separate YAML files
than the Ansible playbooks: ::

    testinfra/vars/
    ├── app-prod.yml
    ├── app-staging.yml
    ├── build.yml
    ├── development.yml
    ├── mon-prod.yml
    └── mon-staging.yml

Any variable changes in the Ansible config should have a corresponding
entry in these vars files. These vars are dynamically loaded for each
host via the ``testinfra/conftest.py`` file. Make sure to add your tests to
relevant location for the host you plan to test: ::

    testinfra/app/
    ├── apache
    │   ├── test_apache_journalist_interface.py
    │   ├── test_apache_service.py
    │   ├── test_apache_source_interface.py
    │   └── test_apache_system_config.py
    ├── test_apparmor.py
    ├── test_appenv.py
    ├── test_network.py
    └── test_ossec.py

In the example above, to add a new test for the ``app-staging`` host,
add a new file to the ``testinfra/spec/app-staging`` directory.

.. tip:: Read :ref:`updating_ossec_rules` to learn how to write tests for the
         OSSEC rules.

Config test layout
------------------

The config tests are mostly broken up according to machines in the
Vagrantfile: ::

    testinfra/
    ├── app
    ├── app-code
    ├── build
    ├── common
    ├── development
    └── mon

Ideally the config tests would be broken up according to roles,
mirroring the Ansible configuration. Prior to the reorganization of
the Ansible layout, the tests are rather tightly coupled to hosts. The
layout of config tests is therefore subject to change.

Config testing strategy
-----------------------

The config tests currently emphasize testing implementation rather than
functionality. This was a temporary measure to increase the testing
baseline for validating the Ansible provisioning flow, which aided in migrating
to a current version of Ansible (v2+). Now that the Ansible version is current,
the config tests can be improved to validate behavior, such as confirming
ports are blocked via external network calls, rather than simply checking
that the iptables rules are formatted as expected.
