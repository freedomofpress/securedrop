Upgrading to Ubuntu 16.04 After April 30
========================================
As of **May 1, 2019**, Ubuntu 14.04 has reached End of Life. If you are still
running Ubuntu 14.04 on your *Application* and *Monitor Server*, your servers
will no longer receive security updates for operating system packages, the
kernel, or SecureDrop itself.

That means that a sufficiently severe vulnerability discovered in any of those
components may permit an adversary to compromise SecureDrop servers running
Ubuntu 14.04.

For this reason, starting May 1, we recommend a reinstall on Ubuntu 16.04
for any SecureDrop still on Ubuntu 14.04. See our
:doc:`installation guide <../install>`.

This will result in a new ``.onion`` address for your *Source Interface* and your
*Journalist Interface*. You will need to create new user accounts and USB drives
for administrators and journalists, and sources you are currently in touch with
will no longer be able to log in using their codename. We recommend notifying
your sources about this change on your *Landing Page*.

Unless you have reason to believe that the *Submission Key* may have been
compromised, you do **not** need to reinstall the *Secure Viewing Station*.
Instead, during this part of the installation process, use a copy of your
public key obtained from your *Secure Viewing Station*.

Saving old submissions
----------------------
If you require access to old submissions to your SecureDrop, you need to save
them securely. We do not recommend using the standard backup procedure via
``securedrop-admin backup``, as restoring such a backup will reinstate secrets
and credentials that may have been compromised.

Instead, download any submissions you have not already downloaded to
your *Secure Viewing Station* following the standard process as described in the
:doc:`Journalist Guide <../journalist>`. If you do not reinstall the *Secure
Viewing Station*, you will be able to continue to view these submissions on the
*Secure Viewing Station* as before, but you will no longer be able to reply to
the sources that sent them, until they create a new account.

.. caution:: If you do reinstall your *Secure Viewing Station*, you **must** copy
  the public and private *Submission Key* from the old *Secure Viewing Station*
  to the new one. Without the keypair, you will not be able to decrypt old
  submissions on a new *Secure Viewing  Station*.

Contact us
----------
If you have questions or comments regarding this process, please don't hesitate
to reach out:

.. include:: ../includes/getting-support.txt
