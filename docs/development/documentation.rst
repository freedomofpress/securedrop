Documentation Guidelines
========================

.. caution:: This is an early draft. Our documentation guidelines are
             subject to change at any time until this notice is removed.

.. warning:: We recently auto-converted the documentation from
             Markdown to ReST, and are still cleaning up the output
             from that auto-conversion. If you find style issues,
             broken links or references, or any other similar issues,
             pull requests are welcome!

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

      $ make html
      $ open _build/html/index.html

   .. tip:: You can use ``sphinx-autobuild`` to automatically rebuild
            and reload your docs as you work on them. Run
            ``sphinx-autobuild . _build/html``.


Occasionally, the docs get out of whack and rebuilding them doesn't
work as it should. You can usually resolve this by clearing out the
build artifacts and re-building the docs from scratch:

.. code:: sh

   $ make clean && make html


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

* When specific elements from a user interface are mentioned by name or by label, **bold** it.

    "Once you’re sure you have the right drive, click **Format Drive**."

* When SecureDrop-specific :doc:`terminology <../terminology>` is used, *italicize* it.

    "To get started, you’ll need two Tails drives: one for the *Admin Workstation* and one for the *Secure Viewing Station*."

  .. todo:: I don't love this convention for a couple of reasons:

	    1. If there are a lot of references to terminology in the
               same area of text, all of the short bursts of italics
               makes it hard to read.
	    2. The default style for document references is also
               italicized, which is confusing when used near
               references to the terminology.

