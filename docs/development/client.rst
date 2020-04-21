Developing the SecureDrop Client Application
============================================

As part of the ongoing work to make an integrated journalist-friendly workstation
for SecureDrop we have created a native client application to be run within the
Qubes operating system. It helps journalists with the most common activities
associated with using SecureDrop in a user friendly manner.

Currently the client is alpha quality although work is ongoing in terms of
improving features and the user interface.

The source code, and related issues are `hosted on GitHub <https://github.com/freedomofpress/securedrop-client>`_.

Developer Setup
---------------

You may find developer setup instructions in the `SecureDrop Client README <https://github.com/freedomofpress/securedrop-client/blob/master/README.md>`_.

How to Find Help
----------------

If you would like to report a problem `submit a new issue <https://github.com/freedomofpress/securedrop-client/issues/new>`_.

If you'd like to chat with other developers working on the client drop
into our `Gitter chat channel for the project <https://gitter.im/freedomofpress/securedrop>`_.

Every non-public holiday weekday (except Fridays) at 10am (Pacific Time) we
take part in a public daily stand-up, usually via a
`meeting on Jitsi <https://meet.jit.si/QuickWizardsDanceHigh>`_
(although the details of each daily meeting are published on the Gitter channel
five minutes before the start of the meeting). All are welcome to contribute.

Otherwise, read on.

Client Architecture
-------------------

The SecureDrop client is a PyQt application. It's written using Python 3.5 and
the Python bindings for the Qt UI framework (`PyQt <https://riverbankcomputing.com/software/pyqt/intro>`_).

In the root directory of the repository are two important directories:
``securedrop_client`` (containing the application code) and ``tests``
containing our unit tests. You'll also find a Makefile in the root directory
which defines commands to run commonly needed activities. Type, ``make`` to
find out what commands are available.

The code in the ``securedrop_client`` namespace is organised in the following
way:

* ``app.py`` - starts and configures the application.
* ``logic.py`` - contains the application logic, encapsulated in the ``Client`` class.
* ``db.py`` - holds all the `SQLAlchemy ORM model definitions <https://www.sqlalchemy.org/>`_ for interacting with the local Sqlite database.
* ``storage.py`` - contains the functions needed for interacting with a remote SecureDrop API and the local database.
* ``utils.py`` - generic utility functions needed throughout the application.
* ``gui`` - this namespace contains two modules: ``main.py`` (containing the ``Window`` class through which all interactions with the user interface should happen) and ``widgets.py`` (containing all the custom widgets used by the ``Window`` class to draw the user interface).

We try very hard to keep the application logic and UI code cleanly separated.
Furthermore, we try equally hard to ensure the main GUI code always remains
unblocked. For instance look at how the ``APICallRunner`` is used in
``logic.py`` to make unblocked network calls to the remote API.

We encourage developers to make sure all classes, methods and functions have docstrings describing the
intention behind the code. Obviously, it's important that such docstrings **remain up to date**
as the code evolves.

If possible, please use `Python type hints <https://docs.python.org/3.5/library/typing.html>`_
for new code. We're going to transition the code base to this style in the
not-too-distant future.

Tests
-----

The files and directory structure found within the ``tests`` directory mirrors
that of the files and directories in ``securedrop_client``. For instance, all
the unit tests for the ``securedrop_client/logic.py`` module can be found in
the ``tests/test_logic.py`` file.

To run the complete test suite simply type::

    make check

Our code style checkers, full test suite and coverage checker will run and
report any errors.

We use the `PyTest testing framework <https://docs.pytest.org/en/latest/>`_ for
writing and running our unit tests. We expect every test to have an associated
comment which describes the *intent* of the test. As far as possible, tests
should be self contained with all the context needed to understand them within
each individual unit test (this makes it easier to debug things when the test
suite fails as the codebase evolves).

Take a look in any of the test files to see the sort of code we expect for
unit tests.

We currently have, and expect to maintain, 100% unit test coverage of our
code base. If you're unsure how to achieve this, please don't hesitate to get
in touch via Gitter or mention this in your description of any pull requests
you submit.

Contributing
------------

Our open issues are `on GitHub <https://github.com/freedomofpress/securedrop-client/issues>`_.

Please remember that we have a code of conduct and expect all contributors to
abide by it.

Before submitting a pull request, make sure the test suite passes
(``make check``), because our CI tools will flag broken tests before we're able
to merge your code into ``master``.

Most of all, please don't hesitate to get in touch if you need help, advice or
would like guidance.

Thank you for your support!
