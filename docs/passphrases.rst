Passphrases
===========

Each individual with a role (admin or journalist) at a given
SecureDrop instance must generate and retain a number of strong,
unique passphrases. The document is an overview of the passphrases,
keys, two-factor secrets, and other credentials that are required for
each role in a SecureDrop installation.

.. note:: We encourage each end user to use KeePassX, an easy-to-use
          password manager included in Tails, to generate and retain
          strong and unique passphrases. We have created a template
          passphrase database that you can use to get started. For more
          information, see the :doc:`tails_guide`.

.. tip:: For best practices on managing passphrases, see
   :doc:`passphrase_best_practices`.

Admin
-----

The admin will be using the *Admin Workstation* with Tails to connect to
the *Application Server* and the *Monitor Server* using Tor and SSH. The tasks
performed by the admin will require the following set of credentials and 
passphrases:

-  A passphrase for the persistent volume on the Admin Live USB.
-  Additional credentials, which we recommend adding to Tails' KeePassX password
   manager during the installation:

   -  The *Application Server* and *Monitor Server* admin username and password
      (required to be the same for both servers).
   -  The network firewall username and password.
   -  The SSH private key and, if set, the key's passphrase.
   -  The GPG key that OSSEC will encrypt alerts to.
   -  The admin's personal GPG key.
   -  The account details for the destination email address for OSSEC alerts.
   -  The Hidden Services values required to connect to the *Application* and
      *Monitor Servers*.


The admin will also need to have a way to generate two-factor
authentication tokens.

.. include:: includes/otp-app.txt

And the admin will also have the following two credentials:

-  The secret code for the *Application Server*'s two-factor authentication.
-  The secret code for the *Monitor Server*'s two-factor authentication.

Journalist
----------

The journalist will be using the *Journalist Workstation* with Tails to
connect to the *Journalist Interface*. The tasks performed by the journalist
will require the following set of passphrases:

-  A master passphrase for the persistent volume on the Tails device.
-  A master passphrase for the KeePassX password manager, which unlocks
   passphrases to:

   -  The Hidden Service value required to connect to the Journalist
      Interface.
   -  The *Journalist Interface*.
   -  The journalist's personal GPG key.

The journalist will also need to have a two-factor authenticator, such
as an Android or iOS device with FreeOTP installed, or a
YubiKey. This means the journalist will also have the following
credential:

-  The secret code for the *Journalist Interface*'s two-factor
   authentication.

*Secure Viewing Station*
~~~~~~~~~~~~~~~~~~~~~~~~

The journalist will be using the *Secure Viewing Station* with Tails to
decrypt and view submitted documents. The tasks performed by the
journalist will require the following passphrases:

-  A master passphrase for the persistent volume on the Tails device.

The backup that is created during the installation of SecureDrop is also
encrypted with the application's GPG key. The backup is stored on the
persistent volume of the Admin Live USB.
