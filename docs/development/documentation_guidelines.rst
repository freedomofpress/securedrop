Documentation Guidelines
========================

SecureDrop's documentation is written in `ReStructuredText`_ (ReST),
and is built by and hosted on `Read the Docs`_ (RTD). The
documentation files are stored in the primary SecureDrop git
repository under the ``docs/`` directory.

.. _ReStructuredText: http://sphinx-doc.org/rest.html
.. _Read the Docs: https://docs.readthedocs.org/en/latest/index.html

To get started editing the docs:

#. Clone the SecureDrop repository:

   .. code:: sh

      git clone https://github.com/freedomofpress/securedrop.git

#. Install the dependencies:

   .. code:: sh

      pip install -r securedrop/requirements/develop-requirements.txt

#. Build the docs and open the index page in your web browser:

   .. code:: sh

      make docs

If you have the :ref:`Development VM <development_vm>` running, you should run
``make docs`` from within the ``/vagrant`` directory inside the VM, otherwise
the forwarded port on 8000 will collide with sphinx-autobuild process running
on localhost.

You can then can browse the documentation at http://127.0.0.1:8000/.
As you make changes, the docs will automatically rebuild in the browser
window, so you don't need to refresh the page manually.

Testing documentation changes
-----------------------------

You can check the docs for formatting violations by running the linting
option:

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

Updating screenshots
--------------------

The user guides for SecureDrop contain screenshots of the web applications.
To update these screenshots automatically you can run:

.. code:: sh

   make -C securedrop images update-user-guides

This will generate screenshots for each image in the web application and copy
them to the folder under ``docs/images/manual/screenshots`` where they will
replace the existing screenshots. Stage for commit any screenshots you wish to
update. If you wish to update all screenshots, simply stage for commit all
changed files in that directory.

Integration with Read the Docs
------------------------------

.. include:: ../includes/docs-branches.txt

Our documentation is built and hosted by `Read the Docs`_ and is available at
https://docs.securedrop.org. We use a
`webhook`_ so the docs are rebuilt automatically when commits get pushed to the
branch.

.. _upstream Git repository: https://github.com/freedomofpress/securedrop
.. _webhook: http://docs.readthedocs.org/en/latest/webhooks.html

Style Guide
-----------

When specific elements from a user interface are mentioned by name or by label, **bold** it.

    "Once you’re sure you have the right drive, click **Format Drive**."

When SecureDrop-specific :doc:`terminology <../terminology>` is used, *italicize* it.

    "To get started, you’ll need two Tails drives: one for the *Admin Workstation* and one for the *Secure Viewing Station*."

  .. todo:: I don't love this convention for a couple of reasons:

         1. If there are a lot of references to terminology in the
            same area of text, all of the short bursts of italics
            makes it hard to read.
         2. The default style for document references is also
            italicized, which is confusing when used near
            references to the terminology.

Try to keep your lines wrapped to near 80 characters when editing the docs.
Some exceptions are warranted, such as complex code blocks showing example
commands, or long URLs, but in general the docs should be tightly wrapped.

When referring to virtual machines in the development environment, use
lowercase for the name:

    app-staging VM

Ensure that example commands in codeblocks are easily copy/pasteable.
Do not prepend the ``$`` shell prompt indicator to example commands:

  .. code::

     echo hello

In the context of a terminal session, with both typed commands and printed
output text, then use ``$``, but only on the typed command lines:

  .. code::

     $ echo hello
     hello
     $ echo sunshine
     sunshine

Use absolute paths when referring to files outside the SecureDrop repository.
Exceptions made for when it's clear from the surrounding context what the
intended working directory is. For files inside the SecureDrop directory,
write them as `./some_dir/file`, where `.` is the top level directory of the
SecureDrop repo. Since by default the git repo will be cloned under the name
`securedrop` and it also contains a `securedrop` subdirectory this is intended
to avoid confusion.  Exceptions made for when it's clear from the context
we're outside of the SecureDrop repo, but would like to somehow interact with
it (e.g., we just cloned the repo and now we're going to `cd` into it).
