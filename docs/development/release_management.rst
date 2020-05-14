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
#. Check if there is a new stable release of Tor that can be QAed and released
   as part of the SecureDrop release. If so, file an issue.
#. Check if a release candidate for the Tails release is prepared. If so, request
   people participating in QA to use the latest release candidate.
#. Ensure that a pre-release announcement is prepared and shared with the community
   for feedback. Once the announcement is ready, coordinate with other team members to
   send them to current administrators, post on the SecureDrop blog, and tweet
   out a link.
#. For a regular release for version 1.x.0, branch off ``develop``::

     git checkout develop
     git checkout -b release/1.x

   .. warning:: For new branches, please ask a ``freedomofpress``
                organization administrator to enable branch protection
                on the release branch. We want to require CI to be
                passing as well as at least one approving review prior
                to merging into the release branch.

#. For each release candidate, update the version and
   changelog. Collect a list of the important changes in the release,
   including their GitHub issues or PR numbers, then run the
   ``update_version.sh`` script, passing it the new version in the
   format ``major.minor.patch~rcN``, e.g.::

     securedrop/bin/dev-shell ../update_version.sh 1.3.0~rc1

   The script will open both the main repository changelog
   (``changelog.md``) and the one used for Debian packaging in an
   editor, giving you a chance to add the changes you collected. In
   the Debian changelog, we typically just refer the reader to the
   ``changelog.md`` file.

#. If you would like to sign the release commit, you will need to do so manually:

   a. Create a new signed commit and verify the signature::

        git reset HEAD~1
        git commit -aS
        git log --show-signature

   #. Ensure the new commit is signed, take note of the commit hash.

   #. Edit ``1.x.y-rcN.tag`` and replace the commit hash with the new
      (signed) commit hash.

   #. Delete the old tag and create a new one based on the tag file
      edited above::

         git tag -d 1.x.y-rcN
         git mktag < 1.x.y-rcN.tag > .git/refs/tags/1.x.y-rcN

#. Push the branch and tags:

   * For ``1.x.y~rc1``, push the ``release/1.x.y`` branch and
     ``1.x.y-rc1`` tag directly.

   * For subsequent release candidates and the final release version,
     issue a PR with changelog and version changes into the
     ``release/1.x.y`` branch, and push the signed tag once the PR is
     merged.

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
#. Make sure that the default branch of documentation is being built
   off the tip of the release branch. Building from the branch instead
   of a given tag enables us to more easily add documentation changes
   after release. You should:

   a. Log into readthedocs.
   #. Navigate to **Projects** → **securedrop** → **Versions** →
      **Inactive Versions** → **release/branch** → **Edit**.
   #. Mark the branch as Active by checking the box and save your
      changes. This will kick off a new docs build.
   #. Once the documentation has built, it will appear in the version
      selector at the bottom of the column of the.
   #. Now set this new release as default by navigating to **Admin** →
      **Advanced Settings** → **Global Settings** → **Default
      Version**.
   #. Select ``release/branch`` from the dropdown menu and save the
      changes.
   #. Verify that docs.securedrop.org redirects users to the
      documentation built from the release branch.

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

After the release, carefully monitor the FPF support portal (or ask those that have access to
monitor) and SecureDrop community support forum for any issues that users are
having.

Finally, in a PR back to develop, cherry-pick the release commits (thus ensuring a consistent
changelog in the future) and bump the version numbers
in preparation for the next release (this is required for the upgrade testing scenario).
