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

Due to packaging logic changes, you'll need to build the Debian packages
with overrides enabled for Xenial support. Then run the Xenial scenario.

.. code::

   make build-debs-xenial
   make staging-xenial

The VMs will be available. Further debugging likely required; you can
log into the machines with e.g.:

.. code::

   molecule login -s libvirt-staging-xenial -h app-staging

Depending on the error, simply re-running the ``make staging-xenial`` target
may help. Naturally, we want the process to be error-free reliably.


Known bugs with Xenial support
------------------------------

Below is a high-level overview of known problems to be addressed
for delivering Xenial compatibility.

Ansible provisioning
    Changes required to support the "xenial" apt sources throughout
    config logic, particularly in templates.

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
    The testinfra config test suite expects Trusty throughout. We'll need
    to update that logic to refer to LSB codename instead, and assert
    that the target platform is one of either Trusty or Xenial.

More detailed research notes on evaluating Xenial support can be found
in the following GitHub issues:

  * `#3207 - [xenial] Perform timeboxed install attempt of SecureDrop against Ubuntu 16.04 <https://github.com/freedomofpress/securedrop/issues/3207>`__
  * `#3491 - [xenial] Perform timeboxed upgrade attempt of SecureDrop from Ubuntu 14.04 to 16.04 <https://github.com/freedomofpress/securedrop/issues/3491>`__
