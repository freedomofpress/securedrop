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
