.. _upgrade_testing:

Upgrade Testing using Molecule
==============================

The SecureDrop project includes Molecule scenarios for developing and testing against
multi-server configurations, including a scenario to simulate the process of upgrading an
existing system. This document explains how to work with this scenario to test
features that make potentially release-breaking changes such as database
schema updates.

The Molecule upgrade scenario sets up a predefined staging Securedrop virtual
environment using Vagrant boxes built with the latest application release.
It also creates a virtualized APT repository, and modifies
the SecureDrop environment to use this APT repository instead of the FPF main
repo at https://apt.freedom.press/.

You can use this scenario to test the upgrade process, using using either
locally-built .debs or packages from the FPF test repo at
https://apt-test.freedom.press/. Both options are described below.

.. note:: The upgrade scenario uses QEMU/KVM via Vagrant's libvirt provider, in
   place of the  default Virtualbox provider. If you haven't already done so,
   you'll need to set up the libvirt provider before proceeding. For
   more information, see :ref:`libvirt_provider`.

.. _upgrade_testing_local:

Upgrade testing using locally-built packages
--------------------------------------------

.. note::
   As of ``0.12.1``, the default platform for upgrade testing
   boxes is Ubuntu Xenial 16.04. We no longer support upgrade boxes
   based on Ubuntu Trusty 14.04.

First, build the app code packages and create the environment:

.. code:: sh

 make build-debs
 make upgrade-start

The playbook will return the source interface Onion address. You can use this to
check the application version displayed in the source interface footer.
Alternatively, you can log into the *Application Server* VM and check the deployed
package version directly:

.. code:: sh

   molecule login -s upgrade -h app-staging

From the *Application Server*:

.. code:: sh

   apt-cache-policy securedrop-config

The installed package version should match the latest release version.

To perform an upgrade using the virtualized APT repository, log out of the
*Application Server* and run the Molecule side-effect action:

.. code:: sh

   make upgrade-test-local

This will upgrade the SecureDrop packages on the *Application* and
*Monitor Servers*, using your locally-built packages and apt VM instead of the
FPF production apt repository.

You can verify that the application version has changed either by checking the
source interface's footer or directly on the *Application Server* as described
above.

.. _upgrade_testing_apt:

Upgrade testing using apt-test.freedom.press
--------------------------------------------

You can use the upgrade scenario to test upgrades using official release
candidate packages from the FPF test APT repository. First,
create the environment:

.. code:: sh

   make upgrade-start-qa

Then, log into the *Application Server*:

.. code:: sh

   molecule login -s upgrade -h app-staging

From the *Application Server*:

.. code:: sh

   sudo apt-get update
   apt-cache policy securedrop-config

The installed package version should match the current release version.
To install the latest packages from the apt-test proxy:

.. code:: sh

   make upgrade-test-qa

Log back into the *Application Server*, and repeat the previous commands:

.. code:: sh

   sudo apt-get update
   apt-cache policy securedrop-config

Navigate to the Source Interface URL again, and confirm you see the upgraded
version in the footer. Then proceed with testing the new version.

.. _updating_upgrade_boxes:

Updating the base boxes used for upgrade testing
------------------------------------------------

When a new version of SecureDrop is released, we must create and upload
new VM images, to enable testing against that base version in future upgrade
testing. The procedure is as follows:

1. ``make clean`` to remove any previous artifacts (which would also be pushed)
#. ``git checkout <version>``
#. ``make vagrant-package``
#. ``cd molecule/vagrant-packager && ./push.yml`` to upload to S3
#. Commit the local changes to JSON files and open a PR.

Subsequent invocations of ``make upgrade-start`` will pull the latest
version of the box.
