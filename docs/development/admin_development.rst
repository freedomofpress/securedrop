Development of Securedrop-Admin in the Admin Directory
======================================================

The ``admin`` directory contains the source of the
``securedrop-admin`` script which is used in Tails to perform various
administrative tasks. It is a standalone python module which can be
tested on Debian GNU/Linux stretch with:

.. code::

   python3 bootstrap.py
   source .venv3/bin/activate
   pip3 install --no-deps --require-hashes -r requirements-dev.txt
   tox

A Docker helper is provided to simplify the installation and make
it portable on various operating systems.

Run only flake8 with:

.. code::

   bin/dev-shell tox -e flake8

Run only one test foobar with:

.. code::

   bin/dev-shell tox -e py3 -- -k foobar

Docker has the admin directory mounted from the host into the
container, at the same location to avoid any trouble with hardcoded
absolute paths. It runs with the id of the host user so files created
in the container are owned by the host user instead of root. If a
script needs root access, it has passwordless sudo permissions.

Convenience ``Makefile`` targets are also provided for the most common
tasks:

.. code::

   $ make
   Makefile for developing and testing securedrop-admin.
   Subcommands:

   help                       Print this message and exit.
   test                       Run tox
   update-pip-requirements    Updates all Python requirements files via pip-compile.
