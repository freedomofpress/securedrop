Making a PR to SecureDrop
=============================

Forking and Cloning the Project
---------------------------------

1. Fork SecureDrop on GitHub from the Main Repository to your own profile.

2. Clone the forked repository.

.. code:: sh

  git clone https://github.com/<your-username>/securedrop.git
  cd securedrop

3. Add the Main Repository as an upstream remote.

.. code:: sh

  git remote add upstream https://github.com/freedomofpress/securedrop.git


Make Your Changes and Push to the Fork
----------------------------------------------

Create a branch
~~~~~~~~~~~~~~~~~~

Create a branch on which you make your changes.

.. code:: sh

  git checkout -B change-one


Make Your Changes and Commit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now enter the directory of your fork amd make changes as you wish.
Run tests for the changes you have made.

If you create a new file, remember to add it with :code:`git add`.

.. code:: sh

  git add <new-file>

Commit your changes, adding a description of what was added. If you’re not
used to Git, the simplest way is to commit all modified files and add a
description message of your changes in a single command like this:

.. code:: sh

  git commit -a -m "<Description of changes made>"

Pull the upstream changes
~~~~~~~~~~~~~~~~~~~~~~~~~~

We get any updates made in the upstream repository.

.. code:: sh

  git pull upstream develop


Rebasing
~~~~~~~~~

Rebasing is the process of moving or combining a sequence of commits to a new
base commit. Rebasing is most useful and easily visualized in the context of a
feature branching workflow.

Assume the following history exists:

.. code:: sh

          A---B---C change-one
         /
    D---E---F---G develop

From this point, the result of either of the following commands:

.. code:: sh

  git rebase develop
  git rebase develop change-one

would be:

.. code:: sh

                    A`--B`--C` change-one
                 /
    D---E---F---G develop

.. note::
  :code:`A` and :code:`A`` represents the same set of changes, but have
  different committer information. 

Pushing the changes to GitHub Fork
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Once your changes are committed and rebased, push the changes to your GitHub
fork.

.. code:: sh

  git push origin <branch-name>

Making a Pull Request to get Your Changes Merged in :code:`develop` branch
-------------------------------------------------------------------------------

1. Through GitHub make a pull request from the branch that you commited your
code to.

2. Once PR is made, the Circle CI build server checks all tests
and Codecov runs a report on test coverage. The reports are available in the
PR page and also emailed to admins.

3. From there, a maintainer will accept your PR or they may request comments
for you to address prior to merge. The maintainer may also ask you to `squash
your commits
<https://robots.thoughtbot.com/git-interactive-rebase-squash-amend-rewriting-history>`_
prior to merge.
