Contributing Guidelines
=======================

Signing commits
---------------

Commits should be signed, as `explained in the GitHub documentation <https://help.github.com/articles/signing-commits-using-gpg/>`_.
This helps verify commits proposed in a pull request are from the expected author.

Branching Strategy
------------------

Development for the upcoming release of SecureDrop takes place on ``develop``,
which is the default branch. If you want to contribute, you should branch
from and submit pull requests to ``develop``. If you want to install or audit
SecureDrop, you should use the latest tag that is not a release candidate (e.g.
``0.6`` not ``0.6-rc1``).

.. tip:: After you have cloned the SecureDrop repository, you can run
   ``git tag`` locally to see all the tags. Alternatively, you can view them on
   `GitHub <https://github.com/freedomofpress/securedrop/releases>`__.

Automated Testing
-----------------

When a pull request is submitted, we have Circle CI automatically run the
SecureDrop test suites, which consist of:

  #. Unit tests of the Python SecureDrop application code.
  #. Functional tests that use Selenium to drive a web browser to verify the
     function of the application from the user's perspective.
  #. Tests of the system configuration state using testinfra.

Before a PR can be merged, these tests must all pass. If you modify the
application code, you should verify the tests pass locally before submitting
your PR. If you modify the server configuration, you should run the
testinfra tests. Please denote in the checklist when you submit the PR that
you have performed these checks locally.

Code Style
----------

We use code linters to keep a consistent code quality and style. These linters
also run in CI and will produce build failures. To avoid this, we have included
a git pre-commit hook. You can install it with the following command run at the
root of the repository:

.. code:: sh

    ln -sf ../../git/pre-commit .git/hooks/pre-commit


.. note::
  The code linters are installed automatically on the Development VM, but for
  the pre-commit hook to work, you will need to install the linting tools
  locally on your host machine. From the root of the repo you can run the
  following:

  .. code:: sh

     pip install --no-deps --require-hashes -r securedrop/requirements/python3/develop-requirements.txt

Python
~~~~~~

All Python code should be `flake8 <http://flake8.pycqa.org/en/latest/>`__
compliant. You can run ``flake8`` locally via:

  .. code:: sh

      make flake8

Shell
~~~~~

All Shell code (e.g. ``bash``, ``sh``) should be `shellcheck <https://github.com/koalaman/shellcheck>`__
compliant. You can run ``shellcheck`` locally via:

  .. code:: sh

      make shellcheck

For reference, consult the `shellcheck wiki <https://github.com/koalaman/shellcheck/wiki>`__
for detailed explanations of any reported violations.

HTML
~~~~

HTML should be in compliance with
`Google's HTML style guide <https://google.github.io/styleguide/htmlcssguide.html>`__.
We use `html-linter <https://pypi.python.org/pypi/html-linter/>`__ to lint
our HTML templates in ``securedrop/source_templates`` and
``securedrop/journalist_templates``. Run the HTML linting options we use via:

  .. code:: sh

      make html-lint

YAML
~~~~

The Ansible configuration is specified in YAML files, including variables,
tasks, and playbooks. All YAML files in the project should pass the
`yamllint <https://github.com/adrienverge/yamllint>`__ standards declared
in the ``.yamllint`` file at the root of the repository.
Run the checks locally via:

  .. code:: sh

      make yamllint

Type Hints in Python code
-------------------------

By adding type hints/annotations in the Python code, we are making the codebase
easier to maintain in the long run by explicitly specifying the expected input/output
types of various functions.

Any pull request with Python code in SecureDrop should have corresponding type hints
for all the functions. Type hints and function annotations are defined in 
`PEP 484 <https://www.python.org/dev/peps/pep-0484>`_ and in `PEP 3107
<https://www.python.org/dev/peps/pep-3107>`_. We also use the `mypy <http://mypy-lang.org>`_
tool in our CI to find bugs in our Python code.

If you are new to Python type hinting, please read the above mentioned PEP documents,
and then go through the examples in the 
`mypy documentation <https://mypy.readthedocs.io/en/stable/builtin_types.html>`_.
Some type annotations are included as code comments due to SecureDrop being Python 2 only when
they were added, but any annotation syntax supported in Python 3.5 is allowed (i.e. function but not
variable annotations which were added in Python 3.6).

Example of Type Hint
~~~~~~~~~~~~~~~~~~~~

.. code:: Python

    import typing
    # https://www.python.org/dev/peps/pep-0484/#runtime-or-type-checking
    if typing.TYPE_CHECKING:
        # flake8 can not understand type annotation yet.
        # That is why all type annotation relative import
        # statements has to be marked as noqa.
        # http://flake8.pycqa.org/en/latest/user/error-codes.html?highlight=f401
        from typing import Dict  # noqa: F401

    class Config(object):

        def __init__(self):
            # type: () -> None
            self.NAMES = {}  # type: Dict[str, str]

        def add(self, a, b):
            # type: (int, int) -> float
            c = 10.5  # type: float
            return a + b + c

        def update(self, uid, Name):
            # type: (int, str) -> None
            """
            This method updates the name example.
            """
            self.NAMES[uid] = Name

    def main():
        # type: () -> None
        config = Config()  # type: Config
        config.add(2, 3)
        config.update(223, "SD")

    if __name__ == '__main__':
        main()

The above example shows how to do a conditional import of ``Dict`` class from 
``typing`` module. ``typing.TYPE_CHECKING`` will only be true when we use mypy
to check type annotations.


How to Use mypy?
~~~~~~~~~~~~~~~~~

``make lint`` already checks for any error using the ``mypy`` tool. In case you want
to have a local installation, you can do that using your Python 3 virtualenv.

.. code:: shell

    $ python3 -m venv ../.py3
    $ source ../.py3/bin/activate
    $ pip install mypy
    $ mypy securedrop

Git History
-----------

We currently use an explicit merge strategy to merge feature branches into
``develop``. In order to keep our git history as clean as possible, please squash
your commits to package up your changes into a clear history. If you have
many unnecessary commits that do not add information to aid in review, they
should be removed. If you are unfamiliar with how to squash commits with rebase,
check out this
`blog post <http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html>`__.

.. _contributor-permissions:

Privileges
----------

.. note:: The privilege escalation workflow is different for
          :ref:`code maintainers <contributor-permissions>` and
          :ref:`translation maintainers <i18n-administrator-permissions>`.

Dedicated contributors to SecureDrop will be granted extra privileges
such as the right to push new branches or to merge pull requests. Any
contributor with the right technical and social skills is entitled to
ask. The people who have the power to grant such privileges are
committed to do so in a transparent way as follows:

#. The contributor posts a message `in the forum
   <https://forum.securedrop.org/>`__ asking for privileges (review or
   merge, etc.).
#. After at least a week someone with permissions to grant such
   privilege reviews the thread and either:

   * grants the privilege if there are no objections from current
     maintainers and adds a message to the thread; or
   * explains what is expected from the contributor before they can
     be granted the privilege.

#. The thread is closed.

The privileges of a developer who has not been active for six months or
more are revoked. They can apply again at any time.

Other Tips
----------

* To aid in review, please write
  `clear commit messages <https://chris.beams.io/posts/git-commit/>`__
  and include a descriptive PR summary. We have a PR template that specifies the
  type of information you should include.

* To maximize the chance that your PR is merged, please include the minimal
  changes to implement the feature or fix the bug.

* If there is not an existing issue for the PR you are interested in submitting,
  you should submit an issue first or comment on an existing issue outlining how
  you intend to approach the problem.
