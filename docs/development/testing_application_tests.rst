.. _app_tests:

Testing: Application Tests
==========================

The application test suite uses:

  * Pytest_
  * Selenium_

The application tests consist of unit tests for the Python application code
and functional tests that verify the functionality of the application code
from the perspective of the user through a web browser.

The functional tests use an outdated version of Firefox chosen specifically
for compatibility with Selenium 2, and a rough approximation of the most
recent Tor Browser.

.. note:: We're working on running the Selenium tests in Tor Browser.
          See `GitHub #1629`_ for more info.

.. _`GitHub #1629`: https://github.com/freedomofpress/securedrop/pull/1629

.. _Pytest: https://docs.pytest.org/en/latest/
.. _Selenium: http://docs.seleniumhq.org/docs/

Installation
------------

The application tests are installed automatically in the development
and app-staging VMs, based on the contents of
``securedrop/requirements/test-requirements.txt``.
If you wish to change the dependencies, see :ref:`updating_pip_dependencies`.

Running the Application Tests
-----------------------------

The tests can be run inside the development VM:

.. code:: sh

    make test

Or the app-staging VM:

.. code:: sh

    vagrant ssh app-staging
    sudo bash
    cd /var/www/securedrop
    pytest -v tests
    chown -R www-data /var/lib/securedrop /var/www/securedrop

.. warning:: The ``chown`` is necessary because running the tests as
             root will change ownership of some files, creating
             problems with the source and journalist interfaces.

For explanation of the difference between these machines, see
:doc:`virtual_environments`.

If you just want to run the functional tests, you can use:

.. code:: sh

    securedrop/bin/dev-shell bin/run-test -v tests/functional

Similarly, if you want to run a single test, you can specify it through the
file, class, and test name:

.. code:: sh

    securedrop/bin/dev-shell bin/run-test \
        tests/test_journalist.py::TestJournalistApp::test_invalid_credentials

The `gnupg
<https://pythonhosted.org/python-gnupg>`_ library can be quite verbose in its
output. The default log level applied to this package is ``ERROR`` but this can
be controlled via the ``GNUPG_LOG_LEVEL`` environment variable. It can have values
such as ``INFO`` or ``DEBUG`` if some particular test case or test run needs
greater verbosity.

Page Layout Tests
~~~~~~~~~~~~~~~~~

You can check the rendering of the layout of each page in each translated
language using the page layout tests. These will generate screenshots of
each page and can be used for example to update the SecureDrop user guides
when modifications are made to the UI.

You can run all tests, including the page layout tests with the `--page-layout`
option:

.. code:: sh

    securedrop/bin/dev-shell bin/run-test --page-layout tests


Updating the Application Tests
------------------------------

Unit tests are stored in the ``securedrop/tests/`` directory and functional
tests are stored in the functional test directory::

    securedrop/tests/
    ├── functional
    │   ├── test_admin_interface.py
    │   ├── test_submit_and_retrieve_file.py
    │   │               ...
    │   └── submission_not_in_memory.py
    ├── utils
    │   ├── db_helper.py
    │   ├── env.py
    │   └── asynchronous.py
    ├── test_journalist.py
    ├── test_source.py
    │        ...
    └── test_store.py

``securedrop/tests/utils`` contains helper functions for writing tests.
If you want to add a test, you should see if there is an existing file
appropriate for the kind of test, e.g. a new unit testing ``manage.py``
should go in ``test_manage.py``.
