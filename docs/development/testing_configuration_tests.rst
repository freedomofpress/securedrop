.. _config_tests:

Testing: Configuration Tests
============================

Testinfra_ tests verify the end state of the staging VMs. Any
changes to the Ansible configuration should have a corresponding
spectest.

.. _Testinfra: https://testinfra.readthedocs.io/en/latest/

Installation
------------

.. code:: sh

    pip install --no-deps --require-hashes -r securedrop/requirements/python3/develop-requirements.txt


Running the Config Tests
------------------------

Testinfra tests are executed against a virtualized staging environment. To
provision the environment and run the tests, run the following commands:

.. code:: sh

    make build-debs
    make staging
    make testinfra

Test failure against any host will generate a report with informative output
about the specific test that triggered the error. Molecule
will also exit with a non-zero status code.


Updating the Config Tests
-------------------------

Changes to the Ansible config should result in failing config tests, but
only if an existing task was modified. If you add a new task, make
sure to add a corresponding spectest to validate that state after a
new provisioning run. Tests import variables from separate YAML files
than the Ansible playbooks: ::

    molecule/testinfra/staging/vars/
    ├── app-prod.yml
    ├── app-staging.yml
    ├── mon-prod.yml
    ├── mon-staging.yml
    └── staging.yml

Any variable changes in the Ansible config should have a corresponding
entry in these vars files. These vars are dynamically loaded for each
host via the ``molecule/testinfra/staging/conftest.py`` file. Make sure to add
your tests to the relevant location for the host you plan to test: ::

    molecule/testinfra/staging/app/
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
add a new file to the ``testinfra/staging/app`` directory.

.. tip:: Read :ref:`updating_ossec_rules` to learn how to write tests for the
         OSSEC rules.

Config Test Layout
------------------

With some exceptions, the config tests are broken up according to platform definitions in the
Molecule configuration: ::

    molecule/testinfra/staging
    ├── app
    ├── app-code
    ├── common
    ├── mon
    ├── ossec
    └── vars

Ideally the config tests would be broken up according to roles,
mirroring the Ansible configuration. Prior to the reorganization of
the Ansible layout, the tests are rather tightly coupled to hosts. The
layout of config tests is therefore subject to change.

Config Testing Strategy
-----------------------

The config tests currently emphasize testing implementation rather than
functionality. This was a temporary measure to increase the testing
baseline for validating the Ansible provisioning flow, which aided in migrating
to a current version of Ansible (v2+). Now that the Ansible version is current,
the config tests can be improved to validate behavior, such as confirming
ports are blocked via external network calls, rather than simply checking
that the iptables rules are formatted as expected.
