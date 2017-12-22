When do I have to manually upgrade Tails?
=========================================

Keeping up to date with the latest versions of software is a fundamental part of good digital security hygiene. Freedom of the Press Foundation does not administer SecureDrop administrator's/journalist's Tails-based workstation environments, so it is the responsibility of SecureDrop administrators and journalists to keep these endpoints up to date.

To review: there are 3 components of the SecureDrop architecture that are based on Tails:

#. The *Admin Workstation* (allowed to connect to the Internet)
#. The *Journalist Workstation* (allowed to connect to the Internet)
#. The *Secure Viewing Station (SVS)* (airgapped, **never** allowed to connect to a network)

The Internet-connected Tails systems automatically check for available upgrades shortly after booting and successfully connecting to Tor. We encourage users of these systems to apply these upgrades in a timely manner, ideally as soon as they are available.

Unfortunately, there are some scenarios in which automatically upgrading Tails is impossible:

#. The *Secure Viewing Station (SVS)* must **always** be upgraded manually, because it is airgapped. Keeping the *SVS* up-to-date is important because it is used to open arbitrary files submitted by sources, which could be malicious and attempt to exploit a known or unknown vulnerabilty in the software on the *SVS*.
#. SecureDrop instances upgrading from SecureDrop version 0.3.x to 0.4.x must manually upgrade Tails on **all** of their Tails drives, because there was a corresponding switch from Tails 2.x to Tails 3.x, for which no automatic upgrade path is available. This process is documented in detail in :doc:`Upgrade Tails from 2.x to 3.x </upgrade_to_tails_3x>`.
#. If you automatically upgraded a Tails 3.0 drive to Tails 3.0.1, you may have encountered a `Tails bug`_ that prevents you from receiving any future automatic upgrades. If you are affected by this bug, the ony available `resolution`_ is to manually upgrade the affected Tails drives.

.. _Tails bug: https://labs.riseup.net/code/issues/13426
.. _resolution: https://tails.boum.org/news/rescue_3.0.1/index.en.html

