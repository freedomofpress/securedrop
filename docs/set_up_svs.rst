Set up the Secure Viewing Station
=================================

The *Secure Viewing Station* is the computer where journalists read and
respond to SecureDrop submissions. Once submissions are encrypted on the
*Application Server*, only the *Secure Viewing Station* has the key to
decrypt them. The *Secure Viewing Station* is never connected to the
internet or a local network, and only ever runs from a dedicated Tails
drive. Journalists download encrypted submissions using their
*Journalist Workstation*, copy them to a *Data Transfer Device* (a USB
drive or a DVD) and physically transfer the *Data Transfer Device* to
the *Secure Viewing Station*.

Since the *Secure Viewing Station* never uses a network connection or an
internal hard drive, we recommend that you physically remove any any
internal storage devices or networking hardware such as wireless cards
or Bluetooth adapters. If the machine has network ports you can't
physically remove, you should clearly cover these ports with labels
noting not to use them. For an even safer approach, fill a port with
epoxy to physically disable it. If you have questions about repurposing
hardware for the *Secure Viewing Station*, contact the `Freedom of the
Press Foundation <https://securedrop.org/help>`__.

You should have a Tails drive clearly labeled “SecureDrop Secure Viewing
Station”. If it's not labeled, label it right now, then boot it on the
*Secure Viewing Station*. After it loads, you should see a "Welcome to
Tails" screen with two options. Select *Yes* to enable the persistent
volume and enter your password, but do NOT click Login yet. Under 'More
Options,' select *Yes* and click *Forward*.

Enter an *Administration password* for use with this specific Tails
session and click *Login*.

.. note:: The *Administration password* is a one-time password. It
          is reset every time you shut down Tails.
