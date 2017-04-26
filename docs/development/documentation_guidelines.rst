Documentation Guidelines
========================

SecureDrop's documentation is written in `ReStructuredText`_ (ReST),
and is built by and hosted on `Read the Docs`_ (RTD). The
documentation files are stored in the primary SecureDrop git
repository under the ``docs/`` directory.

.. _ReStructuredText: http://sphinx-doc.org/rest.html
.. _Read the Docs: https://docs.readthedocs.org/en/latest/index.html

To get started editing the docs:

#. Install the dependencies:

   .. code:: sh

      $ pip install sphinx sphinx-autobuild sphinx_rtd_theme

#. Clone the SecureDrop repository:

   .. code:: sh

      $ git clone https://github.com/freedomofpress/securedrop.git
      $ cd securedrop/docs

#. Build the docs and open the index page in your web browser:

   .. code:: sh

      $ sphinx-autobuild . _build/html

You can then can browse the documentation at http://127.0.0.1:8000/.
As you make changes, the docs will automatically rebuild in the browser
window, so you don't need to refresh the page manually.

Occasionally, the docs get out of whack and rebuilding them doesn't
work as it should. You can usually resolve this by clearing out the
build artifacts and re-building the docs from scratch:

.. code:: sh

   $ make clean && sphinx-autobuild . _build/html

Integration with Read the Docs
------------------------------

Our documentation is built and hosted by `Read the Docs`_ and is available at
https://securedrop.readthedocs.org. The "latest" documentation is currently
based on the **develop** branch of the `upstream Git repository`_. We use a
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

Use absolute paths when referring to files outside the SecureDrop repository.
Exceptions made for when it's clear from the surrounding context what the
intended working directory is. For files inside the SecureDrop directory,
write them as `./some_dir/file`, where `.` is the top level directory of the
SecureDrop repo. Since by default the git repo will be cloned under the name
`securedrop` and it also contains a `securedrop` subdirectory this is intended
to avoid confusion.  Exceptions made for when it's clear from the context
we're outside of the SecureDrop repo, but would like to somehow interact with
it (e.g., we just cloned the repo and now we're going to `cd` into it).
