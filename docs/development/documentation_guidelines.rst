Documentation Guidelines
========================

SecureDrop's documentation is written in `ReStructuredText`_ (ReST),
and is built by and hosted on `Read the Docs`_ (RTD). The
documentation files are stored in the primary SecureDrop git
repository under the ``docs/`` directory.

.. _ReStructuredText: http://sphinx-doc.org/rest.html
.. _Read the Docs: https://docs.readthedocs.org/en/latest/index.html

To get started editing the docs:

.. _clone_the_rep:

#. Clone the SecureDrop repository:

   .. code:: sh

      git clone https://github.com/freedomofpress/securedrop.git

#. Install the dependencies:

   .. code:: sh

      pip install -r securedrop/requirements/develop-requirements.txt

#. Build the docs for viewing in your web browser:

   .. code:: sh

      make docs

You can then browse the documentation at http://127.0.0.1:8000/. As you make
changes, the documentation pages will automatically rebuild in the browser
window, so you don't need to refresh the page manually.

Testing Documentation Changes
-----------------------------

You can check for formatting violations by running the linting option:

   .. code:: sh

      make docs-lint

The ``make docs`` command will display warnings, but will still build the
documentation if formatting mistakes are found. Using ``make docs-lint``
will convert any warnings to errors, causing the build to fail.
The :ref:`CI tests<ci_tests>` will automatically perform linting via the same
command.

The :ref:`CI tests<ci_tests>` by default create staging servers to test the
application code. If your PR only makes documentation changes, you should
prefix the branch name with ``docs-`` to skip the staging run. Project
maintainers will still need to approve the PR prior to merge, and the linting
checks will also still run.

.. _updating_screenshots:

Updating Screenshots
--------------------

The user guides for SecureDrop contain screenshots of the web applications.
To update these screenshots automatically you can run:

.. code:: sh

   make -C securedrop update-user-guides

This will generate screenshots for each page in the web application and copy
them to the folder under ``docs/images/manual/screenshots`` where they will
replace the existing screenshots. Stage for commit any screenshots you wish to
update. If you wish to update all screenshots, simply stage for commit all
changed files in that directory.

Integration with Read the Docs
------------------------------

.. include:: ../includes/docs-branches.txt

Our documentation is built and hosted by `Read the Docs`_ and is available at
https://docs.securedrop.org. We use a `webhook`_ to rebuild the documentation
automatically when commits get pushed to the branch.

.. _upstream Git repository: https://github.com/freedomofpress/securedrop
.. _webhook: http://docs.readthedocs.org/en/latest/webhooks.html

Style Guide
-----------

Line Wrapping
^^^^^^^^^^^^^

Lines in the plain-text documentation files should wrap at 80 characters. (Some
exceptions: complex code blocks showing example commands, or long URLs.)

Glossary
^^^^^^^^

Text taken directly from a user interface is in **bold face**.

    "Once you’re sure you have the right drive, click **Format Drive**."

SecureDrop-specific :doc:`glossary <../glossary>` is in *italics*.

    "To get started, you’ll need two Tails drives: one for the *Admin
    Workstation* and one for the *Secure Viewing Station*."

When referring to virtual machines in the development environment, use
lowercase for the name:

    app-staging VM

Code Blocks
^^^^^^^^^^^

Ensure that example commands in codeblocks are easy to copy and paste.
Do not prepend the ``$`` shell prompt indicator to example commands:

  .. code::

     echo hello

In the context of a terminal session with both typed commands and printed
output text, use ``$`` before the typed commands:

  .. code::

     $ echo hello
     hello
     $ echo sunshine
     sunshine

File Paths
^^^^^^^^^^

:ref:`Cloning<clone_the_rep>` the SecureDrop git repository creates a directory
called ``securedrop``. This ``securedrop`` directory also contains a
``securedrop`` subdirectory for app code.

.. code::

     .
     ├── securedrop
     │   │
     │  ...
     │   ├── securedrop
    ... ...

To avoid confusion, paths to files anywhere inside the SecureDrop git repository
should be written as ``./some_dir/file``, where ``.`` is the top level directory
of the SecureDrop repo.

Use absolute paths when refering to files outside the SecureDrop repository:
``/usr/local/bin/tor-browser``.

Usage and Style
^^^^^^^^^^^^^^^

To avoid confusion, lists should include the so-called "Oxford comma":

    "You will need an email address, a public GPG key for that address, and the
    fingerprint for that key."

Capitalize all section headings in title case:

  .. code::

     Before You Begin
     ================

     Read the Docs
     -------------

  not

  .. code::

     Before you begin
     ================

     Read the docs
     -------------
