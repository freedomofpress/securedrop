Contributing Guidelines
=======================

Branching Strategy
------------------

SecureDrop uses a branching model based on `git-flow
<http://nvie.com/posts/a-successful-git-branching-model/>`__.  The ``master``
branch always points to the latest stable release. Use this branch if you are
interested in installing or auditing SecureDrop.  Development for the upcoming
release of SecureDrop takes place on ``develop``, which is the default
branch. If you want to contribute, you should branch from and submit pull
requests to ``develop``.

Automated Testing
-----------------

When a pull request is submitted, we have Travis CI automatically run the
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

Git History
-----------

We currently use an explicit merge strategy to merge feature branches into
``develop``. In order to keep our git history as clean as possible, please squash
your commits to package up your changes into a clear history. If you have
many unnecessary commits that do not add information to aid in review, they
should be removed. If you are unfamiliar with how to squash commits with rebase,
check out this
`blog post <http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html>`__.

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
