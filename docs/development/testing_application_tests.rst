.. _app_tests:

Testing: Application Tests
==========================

The application test suite uses:

  * Pytest_
  * Selenium_
  * Coveralls_

The functional tests use an outdated version of Firefox chosen specifically
for compatibility with Selenium, and a rough approximation of the most recent
Tor Browser.

.. note:: We're working on running the Selenium tests in Tor Browser.
          See `GitHub #1629`_ for more info.

.. _`GitHub #1629`: https://github.com/freedomofpress/securedrop/pull/1629

.. todo:: Flesh out explanation of the application tests. Decide what's
          important for devs to know; at a high-level, organization could be:

            * Installation
            * Running the application tests
            * any relevant info on editing them

          which matches the layout used for the Config tests.

.. _Pytest: https://docs.pytest.org/en/latest/
.. _Selenium: http://docs.seleniumhq.org/docs/
.. _Coveralls: https://github.com/coveralls-clients/coveralls-python

Installation
------------

The application tests are installed automatically in the development
and app-staging VMs, based on the contents of
``securedrop/requirements/test-requirements.txt``.
If you wish to change the dependencies, see :ref:`updating_pip_dependencies`.

Running the application tests
-----------------------------

The tests can be run inside the development VM:

.. code:: sh

    vagrant ssh development
    cd /vagrant/securedrop
    pytest -v tests

Or the app-staging VM:

.. code:: sh

    vagrant ssh app-staging
    sudo su www-data -s /bin/bash
    cd /var/www/securedrop
    pytest -v tests

For explanation of the difference between these machines, see
:doc:`virtual_environments`.
