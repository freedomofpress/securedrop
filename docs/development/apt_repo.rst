SecureDrop apt repository
=========================

This document contains a brief description of the Debian packages which are
hosted and maintained by Freedom of the Press Foundation in our apt repository
at `apt.freedom.press`_.

linux-image-3.14.*-grsec
    This package contains the Linux kernel image, patched with grsecurity.
    Listed as a dependency of ``securedrop-grsec``.

linux-headers-3.14.*-grsec
    Header files related to the Linux kernel.

`ossec-agent <https://github.com/freedomofpress/ossec>`_
    Installs the OSSEC agent, repackaged for Ubuntu.
    Listed as a dependency of ``securedrop-ossec-agent``.

`ossec-server <https://github.com/freedomofpress/ossec>`_
    Installs the OSSEC manager, repackaged for Ubuntu.
    Listed as a dependency of ``securedrop-ossec-server``.

securedrop-app-code
    Packages the SecureDrop application code, Python pip dependencies and
    AppArmor profiles.

securedrop-ossec-agent
    Installs the SecureDrop-specific OSSEC configuration for the *Application Server*.

securedrop-ossec-server
    Installs the SecureDrop-specific OSSEC configuration for the *Monitor Server*.

`securedrop-grsec <https://github.com/freedomofpress/grsec>`_
    SecureDrop grsecurity kernel metapackage, depending on the latest version
    of ``linux-image-3.14-*-grsec``.

securedrop-keyring
    Packages the public signing key used conjunction with this apt repository.
    Allows for managed key rotation via automatic updates, as implemented in
    `SecureDrop 0.3.10`_.

.. note::
   The SecureDrop install process configures a custom Linux kernel hardened
   with the grsecurity patch set. Only binary images are hosted in the apt
   repo. For source packages, see the `Source Offer`_.

.. _SecureDrop 0.3.10: https://github.com/freedomofpress/securedrop/blob/c5b4220e04e3c81ad6f92d5e8a92798f07f0aca2/changelog.md#0310
.. _apt.freedom.press: https://apt.freedom.press
.. _`Source Offer`: https://github.com/freedomofpress/securedrop/blob/develop/SOURCE_OFFER
