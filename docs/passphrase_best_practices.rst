#########################
Passphrase Best Practices
#########################

All SecureDrop end users---Sources, Journalists, and Administrators---are
required to remember one or more passphrases in order to use the system. This
document describes best practices for passphrase management in the context of
SecureDrop.

**********************
General Best Practices
**********************

#. **Do** memorize your passphrase.

#. If necessary, **do** write your passphrase down temporarily to aid in
   memorizing it.

   #. **Do** store it in a safe place, such as a safe at home, or on a piece of
      paper in your wallet.

   #. **Do** destroy it as soon as you feel comfortable that you have the
      passphrase memorized.

   #. **Don't** store it on any digital device, such as your computer or mobile
      phone.

#. **Do** review your passphrase regularly. It is easy to forget a long or
   complex passphrase if you only use it infrequently.

   .. tip:: We recommend reviewing your passphrase (e.g. by ensuring that you
            can log in to your account on the Source Interface) on at least a
            monthly basis.

#. **Don't** use your passphrase anywhere else.

   If you use your SecureDrop passphrase on another system, a compromise of that
   system could theoretically be used to compromise SecureDrop. You should avoid
   reusing passwords in general, but it is especially important to avoid doing
   so in the context of SecureDrop.

***********
For Sources
***********

Your passphrase is associated with your pseudononymous account and all of your
activity on the SecureDrop server. In order to preserve your anonymity, you
should avoid creating physical or digital associations between yourself and your
passphrase as much as possible.

******************************
For Journalists/Administrators
******************************

While Sources only have one passphrase that they are required to manage,
Journalists and Administrators unfortunately have to manage a veritable
menagerie of credentials.

We have tried to minimize the number of credentials that Journalists and
Administrators actually have to *remember* by automating the storage and entry
of credentials on the Tails workstations wherever possible. For example,
shortcut icons are created on the Desktop of each Tails workstation to make it
easy to access the Tor Hidden Services without having to look up their
``.onion`` addresses every time.

Ideally, each Administrator would only have to:

1. Keep track of their Admin Workstation Tails USB.
2. Remember the passphrase to unlock the persistent storage on that Tails USB.

And each Journalist would only have to:

1. Keep track of their Journalist Workstation Tails USB.
2. Keep track of their Secure Viewing Station Tails USB (and the associated
   Secure Viewing Station computer).
3. Remember the passphrases to unlock the persistent storage on both of these
   Tails USBs.

Memorizing further passwords beyond the ones listed above is counterproductive:
an attacker with access to any of those environments would be able to pivot to
anything they wish to access, and increasing the burden of keeping track of
additional credentials is unpleasant for journalists and administrators and
increases the risk that they will either forget their credentials, compromising
the availability of the system, or compensate for the difficulty by using weak
or reused credentials, potentially compromising the security of the system.

There is a detailed list of the credentials that must be managed by each end
user role in :doc:`passphrases`. We recommended using the KeePassX password
manager included in Tails to store your credentials and minimize the passphrases
that you need to memorize to just the passphrases for the persistent storage on
your Tails USBs.
