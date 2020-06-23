Release Management
==================

The **Release Manager** is responsible for shepherding the release process to
successful completion. This document describes their responsibilities. Some items
must be done by people that have special privileges to do specific tasks
(e.g. privileges to access the production apt server),
but even if the **Release Manager** does not have those privileges, they should
coordinate with the person that does to make sure the task is completed.

Pre-Release
-----------

1. Open a **Release SecureDrop 1.x.y** issue to track release-related activity.
   Keep this issue updated as you proceed through the release process for
   transparency.

#. Check if there is a new stable release of Tor that can be QAed and released as part of the 
   SecureDrop release. You can find stable releases by checking the `Tor blog 
   <https://blog.torproject.org/category/tags/stable-release>`_. If we can upgrade, file an issue
   and upgrade Tor following these steps:

      a. Bump the version in `fetch-tor-packages
         <https://github.com/freedomofpress/securedrop/blob/develop/molecule/fetch-tor-packages/
         playbook.yml>`_ and open a PR.

      b. Run ``make fetch-tor-packages`` to download the new debs. The script uses 
         apt under the hood, so the Release file on the tor packages is verified according
         to Tor's signature, ensuring package integrity.

      c. Copy the downloaded packages into the ``securedrop-dev-packages-lfs`` repo,
         and open a PR so that a reviewer can verify that the checksums match the checksums
         of the packages hosted on the
         `Tor apt repo <https://deb.torproject.org/torproject.org/pool/main/>`_. Once the PR is merged, the
         packages will be resigned with our an FPF-managed test-only signing key, replacing the Tor
         signature, and served from ``apt-test.freedom.press``.

#. Check if a new release or release candidate for Tails has been added to the `Tails apt repo 
   <https://deb.tails.boum.org/dists/>`_. If so, request
   people participating in QA to use the latest release candidate.

#. Work with the Communications Manager assigned for the release to prepare a pre-release 
   announcement that will be shared on the support.freedom.press support portal, securedrop.org 
   website, and Twitter. Wait until the day of the release before including an announcmement for a 
   SecureDrop security update. For a point release, you may be able to skip the pre-release 
   announcement depending on how small the point release is.

#. Create a release branch.

   For a regular release, create a release branch off of ``develop``::

     git checkout develop
     git checkout -b release/<major>.<minor>.0


   For a point release, create a release branch off of the latest merged release branch::

     git checkout release/<major>.<minor>.0
     git checkout -b release/<major>.<minor>.1

#. For each release candidate, update the version and changelog.

   a. Collect a list of important changes from the `SecureDrop milestones
      <https://github.com/freedomofpress/securedrop/milestones>`_ for the release, including 
      GitHub issues or PR numbers for each change. You will add these changes to the changelog in 
      the next step.

   #. Run ``update_version.sh`` in the dev shell to update the version and changelog. The script
      will open both the main repository changelog (``changelog.md``) and the one used for Debian 
      packaging in an editor, giving you a chance to add the changes you collected. In the Debian 
      changelog, we typically just refer the reader to the ``changelog.md`` file. When you run the
      script, you will need to pass it the new version in the format 
      ``<major>.<minor>.<patch>~rcN``::

        securedrop/bin/dev-shell ../update_version.sh <major>.<minor>.<patch>~rcN

      .. note:: A tilde is used in the version number passed to ``update_version.sh`` to match
                the format specified in the `Debian docs 
                <https://www.debian.org/doc/manuals/maint-guide/first.en.html#namever>`_ on how to 
                name and version a package, whereas a dash is used in the tag version number 
                since `git does not support the use of tilde 
                <https://git-scm.com/docs/git-check-ref-format#_description>`_. 

   #. Disregard the script-generated ``.tag`` file since this is only used when we need to sign the 
      final release tag (see `Release Process`_ section).

   #. Sign the commit that was added by the ``update_version.sh`` script::

        git commit --amend --gpg-sign

   #. Push the branch::

        git push origin release/<major>.<minor>.<patch>

   #. Push the unsigned tag (only the final release tag needs to be signed, see 
      `Release Process`_ section)::

        git push origin <major>.<minor>.<patch>-rcN

#. Build Debian packages and place them on
   ``apt-test.freedom.press``. This is currently done by making a PR
   into `a git-lfs repo here
   <https://github.com/freedomofpress/securedrop-dev-packages-lfs>`_.
   Only commit packages with an incremented version number: do not
   clobber existing packages.  That is, if there is already a deb
   called e.g. ``ossec-agent-3.6.0-amd64.deb`` in ``master``, do not
   commit a new version of this deb. Changes merged to ``master`` in
   this repo will be published within 15 minutes.

   .. note:: If the release contains other packages not created by
          ``make build-debs``, such as Tor or kernel updates, make
          sure that they also get pushed to
          ``apt-test.freedom.press``.

#. Build logs from the above debian package builds should be saved and
   published according to the `build log guidelines
   <https://github.com/freedomofpress/securedrop/wiki/Build-logs>`_.
#. Write a test plan that focuses on the new functionality introduced
   in the release. Post for feedback and make changes based on
   suggestions from the community.
#. Encourage QA participants to QA the release on production VMs and
   hardware. They should post their QA reports in the release issue
   such that it is clear what was and what was not tested. It is the
   responsibility of the release manager to ensure that sufficient QA
   is done on the release candidate prior to final release.
#. Triage bugs as they are reported. If a bug must be fixed before the
   release, it's the release manager's responsibility to either fix it
   or find someone who can.
#. Backport release QA fixes merged into ``develop`` into the release
   branch using ``git cherry-pick -x <commit>`` to clearly indicate
   where the commit originated from.
#. At your discretion -- for example when a significant fix is merged
   -- prepare additional release candidates and have fresh Debian
   packages prepared for testing.
#. For a regular release, the string freeze will be declared by the
   translation administrator one week prior to the release. After this
   is done, ensure that no changes involving string changes are
   backported into the release branch.
#. Ensure that a draft of the release notes are prepared and shared
   with the community for feedback.

Release Process
---------------

1. If this is a regular release, work with the translation administrator
   responsible for this release cycle to review and merge the final translations
   and screenshots (if necessary) they prepare. Refer to the
   :ref:`i18n documentation <i18n_release>` for more information about the i18n
   release process. Note that you *must* manually inspect each line in the diff
   to ensure no malicious content is introduced.
#. Prepare the final release commit and tag. Do not push the tag file.
#. Step through the signing ceremony for the tag file. If you do not
   have permissions to do so, coordinate with someone that does.
#. Once the tag is signed, append the detached signature to the unsigned tag::

    cat 1.x.y.tag.sig >> 1.x.y.tag

#. Delete the original unsigned tag::

    git tag -d 1.x.y

#. Make the signed tag::

    git mktag < 1.x.y.tag > .git/refs/tags/1.x.y

#. Verify the signed tag::

    git tag -v 1.x.y

#. Push the signed tag::

    git push origin 1.x.y

#. Ensure there are no local changes (whether tracked, untracked or git ignored)
   prior to building the debs. If you did not freshly clone the repository, you
   can use git clean:

   Dry run (it will list the files/folders that will be deleted)::

      git clean -ndfx

   Actually delete the files::

      git clean -dfx

#. Build Debian packages:

   a. Verify and check out the signed tag for the release.
   #. Build the packages with ``make build-debs``.
   #. Build logs should be saved and published according to the `build
      log guidelines
      <https://github.com/freedomofpress/securedrop/wiki/Build-logs>`_.
#. Step through the signing ceremony for the ``Release`` file(s)
   (there may be multiple if Tor is also updated along with the
   SecureDrop release).
#. Coordinate with the Infrastructure team to put signed Debian
   packages on ``apt-qa.freedom.press``:

   * If the release includes a Tor update, make sure to include the
     new Tor Debian packages.
   * If the release includes a kernel update, make sure to add the
     corresponding grsecurity-patched kernel packages, including both
     ``linux-image-*`` and ``linux-firmware-image-*`` packages as
     appropriate.

#. Coordinate with one or more team members to confirm a successful
   clean install in production VMs using the packages on
   ``apt-qa.freedom.press``.
#. Ask Infrastructure to perform the DNS cutover to switch
   ``apt-qa.freedom.press`` to ``apt.freedom.press``. Once complete,
   the release is live.
#. Issue a PR to merge the release branch changes into ``master``. Once the PR is
   merged, verify that the `public documentation <https://docs.securedrop.org/>`_
   refers to the new release version. If not, log in to ReadTheDocs and start a
   build of the ``master`` version.
#. Create a `release
   <https://github.com/freedomofpress/securedrop/releases>`_ on GitHub
   with a brief summary of the changes in this release.
#. Make sure that release notes are written and posted on the SecureDrop blog.
#. Make sure that the release is announced from the SecureDrop Twitter account.
#. Make sure that members of `the support portal
   <https://support.freedom.press>`_ are notified about the release.
#. Update the upgrade testing boxes following this process:
   :ref:`updating_upgrade_boxes`.


Post-Release
------------

Now it's time to backport the changelog from the release branch into the ``develop`` branch and bump
the SecureDrop version so that it's ready for the next round of QA testing.

We backport the changelog by cherry-picking any commits that modified ``changelog.md`` during the
release. You can look at the file history by checking out the release branch and running: 
``git log --pretty=oneline changelog.md``. The output will contain the commit hashes associated with 
the release. Create a new branch based on ``develop`` and cherry-pick these commits using the
``-x`` flag.

Now you're ready to bump the SecureDrop version on your new branch. There are a bunch of version
files that'll need to be updated in order to set up the upgrade test for the next release. We do
this by running the version-updater script and specifying the new version number, which will be the
next minor version with ``~rc1`` appended. For example, if the release is 1.3.0, then you'll run: 
``securedrop/bin/dev-shell ../update_version.sh 1.4.0~rc1``  (``dev-shell`` is a script that starts
a container so that we can ensure ``dch`` is installed). Accept all the default changes from the
``update_version.sh`` script. You'll only need to add your commit message. Once you're done, sign
your commit and make a PR to merge these changes into ``develop``.

The only thing left to do is to monitor the `FPF support portal <https://support.freedom.press>`_
and the `SecureDrop community support forum <https://forum.securedrop.org/c/support>`_ for any new
user issues related to the release. 
