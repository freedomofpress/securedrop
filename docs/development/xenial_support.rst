Evaluating Xenial support
=========================

The SecureDrop project has always recommended Ubuntu Trusty for
the server operating system. In April 2019, the Long-Term Support (LTS)
status for Trusty will end. We plan to migrate to Ubuntu Xenial 16.04,
which will be supported until April 2021.

In order to evaluate how to support Xenial as we prepare for the transition,
we've created a developer environment suitable for provisioning VMs
based on Xenial.

Running the Xenial dev env
--------------------------

If you're using the libvirt Vagrant provider, you'll need a libvirt-format Xenial
base image. To set one up, run the following commands:

.. code:: sh

   vagrant box add bento/ubuntu-16.04  # choose the virtualbox option
   vagrant mutate bento/ubuntu-16.04 mutate libvirt


Due to packaging logic changes, you'll need to build the Debian packages
with overrides enabled for Xenial support. Then run the Xenial scenario.

.. code:: sh

   make build-debs-xenial
   make staging-xenial


The VMs will now be available.  Depending your choice of VM provider, you can
log into the machines with the following commands:

libvirt:
~~~~~~~~

.. code:: sh

   molecule login -s libvirt-staging-xenial -h app-staging

virtualbox:
~~~~~~~~~~~

.. code:: sh
 
   molecule login -s virtualbox-staging-xenial -h app-staging

To run the testinfra tests against the Xenial enviroment, you can use the commands:

libvirt:
~~~~~~~~

.. code:: sh

  molecule verify -s libvirt-staging-xenial

virtualbox:
~~~~~~~~~~~

.. code:: sh

  molecule verify -s virtualbox-staging-xenial

If you encounter errors, re-running the ``make staging-xenial`` target
may help. Naturally, we want the process to be error-free reliably.


Known bugs with Xenial support
------------------------------

Below is a high-level overview of known problems to be addressed
for delivering Xenial compatibility.

Packaging
    Dependencies for the ``securedrop-app-code`` deb package have changed;
    ``apache2`` should be explicitly required; ``apache2-mpm-worker``
    should be omitted.

Firewall
    The ``_apt`` user should be permitted to perform DNS and outbound TCP
    calls on ports 80 and 443, rather than the ``root`` user.

AppArmor
    Explicit rules required for Apache mpm worker/event changes. ``gpg2``
    policy should permit links via ``/var/lib/securedrop/keys/* l`` or similar.

PAM logic
    The PAM common-auth customizations include declarations for
    ``pam_ecryptfs.so`` which prove problematic; commenting out ostensibly
    resolves. More research required.

Config tests
    The testinfra config test suite runs slightly different checks for
    Trusty and Xenial where appropriate. Care should be taken to preserve
    functionality of the config tests against both distros.

More detailed research notes on evaluating Xenial support can be found
in the following GitHub issues:

  * `#3207 - [xenial] Perform timeboxed install attempt of SecureDrop against Ubuntu 16.04 <https://github.com/freedomofpress/securedrop/issues/3207>`__
  * `#3491 - [xenial] Perform timeboxed upgrade attempt of SecureDrop from Ubuntu 14.04 to 16.04 <https://github.com/freedomofpress/securedrop/issues/3491>`__
