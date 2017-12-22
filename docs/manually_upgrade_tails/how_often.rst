How often do I have to do this?
===============================

The Tails project releases updates `every 6 weeks`_. Occasionally they release a new version ahead of the normal cycle in order to address a critical security vulnerabilty.

.. tip:: The best way to stay abreast of new versions of Tails is to check their `Security page`_. If you use an RSS/Atom feed reader, they provide RSS/Atom feeds that you may wish to subscribe to.

For the Internet-connected Tails workstations (the *Admin Workstation* and the *Journalist Workstation*), you will be automatically notified via a pop-up dialog box when new versions of Tails are available. We recommend that you install these upgrades as soon as possible. The upgrade process usually takes some time, so keep that in mind when choosing when to upgrade.

The *Secure Viewing Station (SVS)* is airgapped, so it cannot receive automatic updates. One could argue that since the *SVS* is airgapped, it does not need to be updated as often, since it is more difficult to derive a successful chain of exploits that can exfiltrate data over an airgap; however, the *SVS* also runs the greatest risk of being exploited, since it may be used to open a wide variety of file types (increasing the viable attack surface) and it also stores the most sensitive data in the system in plaintext (decrypted submissions and the SecureDrop Application private key). Therefore, we **strongly encourage** end users to manually upgrade their *SVS* as soon as possible after a new version of Tails is released.

.. _every 6 weeks: https://tails.boum.org/support/faq/index.en.html
.. _Security page: https://tails.boum.org/security/index.en.html
