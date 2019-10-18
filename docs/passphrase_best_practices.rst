Passphrase Best Practices
=========================

All SecureDrop users---Sources, Journalists, and Admins---are required to
memorize at least one passphrase. This document describes best practices for
passphrase management in the context of SecureDrop.

General Best Practices
----------------------

#. **Do** memorize your passphrase.

#. If necessary, **do** write your passphrase down temporarily while you
   memorize it.

   .. caution:: **Do** store your written passphrase in a safe place, such as a
                safe at home or on a piece of paper in your wallet. **Do**
                destroy the paper as soon as you feel comfortable that you have
                the passphrase memorized. **Do not** store your passphrase on
                any digital device, such as your computer or mobile phone.

#. **Do** review your passphrase regularly. It's easy to forget a long or
   complex passphrase if you only use it infrequently.

   .. tip:: We recommend reviewing your passphrase (e.g. by ensuring that you
            can log in to your SecureDrop account) on at least a monthly basis.

#. **Do not** use your passphrase anywhere else.

   If you use your SecureDrop passphrase on another system, a compromise of that
   system could theoretically be used to compromise SecureDrop. You should avoid
   reusing passphrases in general, but it is especially important to avoid doing
   so in the context of SecureDrop.

For Sources
-----------

Your passphrase is associated with your pseudononymous account and all of your
activity on the SecureDrop server. In order to preserve your anonymity, you
should avoid creating physical or digital associations between yourself and your
passphrase as much as possible.

For Journalists/Admins
----------------------

While Sources only have one passphrase that they are required to manage,
Journalists and Admins unfortunately have to manage a veritable
menagerie of credentials.

We have tried to minimize the number of credentials that Journalists and
admins actually have to *remember* by automating the storage and entry
of credentials on the Tails workstations wherever possible. For example,
shortcut icons are created on the Desktop of each Tails workstation to make it
easy to access the Tor Onion Services without having to look up their
``.onion`` addresses every time.

Ideally, each admin would only have to:

#. Keep track of their Admin Workstation Tails USB.
#. Remember the passphrase to unlock the persistent storage on that Tails USB.

And each Journalist would only have to:

#. Keep track of their Journalist Workstation Tails USB.
#. Keep track of their Secure Viewing Station Tails USB (and the associated
   Secure Viewing Station computer).
#. Remember the passphrases to unlock the persistent storage on both of these
   Tails USBs.

Memorizing further passphrases beyond the ones listed above is counterproductive:
an attacker with access to any of those environments would be able to pivot to
anything they wish to access, and increasing the burden of keeping track of
additional credentials is unpleasant for journalists and admins and
increases the risk that they will either forget their credentials, compromising
the availability of the system, or compensate for the difficulty by using weak
or reused credentials, potentially compromising the security of the system.

There is a detailed list of the credentials that must be managed by each end
user role in :doc:`passphrases`. We recommended using the KeePassXC password
manager included in Tails to store your credentials and minimize the passphrases
that you need to memorize to just the passphrases for the persistent storage on
your Tails USBs.

For the *Transfer Device* and the *Export Device*, which are used to copy
files to and from the air-gapped *Secure Viewing Station*, we recommend using
encrypted USB drives with passphrases stored in the journalist's own password
manager (preferably one which is accessible on their smartphone). This ensures
that the journalist will have quick access to these passphrases when they need
them.

If your organization is not using a password manager already, please see
the `Freedom of the Press Foundation guide <https://freedom.press/training/blog/choosing-password-manager/>`__
to choosing one.
