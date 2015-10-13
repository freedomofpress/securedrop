Roles and Passphrases
=====================

There are several roles for SecureDrop and each requires knowing a
unique set of passphrases.

Passphrases
-----------

A SecureDrop installation will require at least two roles, an admin and
a journalist, and each role will require a number of strong, unique
passphrases. The Secure Viewing Station, which will be used by the
journalist, also requires secure and unique passphrases. The list below
is meant to be an overview of the accounts, passphrases and two-factor
secrets that are required by SecureDrop.

We have created a KeePassX password database template that both the
admin and the journalist can use on Tails to ensure they not only
generate strong passphrases, but also store them safely. By using
KeePassX to generate strong, unique passphrases, you will be able to
achieve excellent security while also maintaining usability, since you
will only have to personally memorize a small number of strong
passphrases. More information about using the password database template
on Tails is included in the `Tails Setup
Guide </docs/tails_guide.md#passphrase-database>`__.

Admin
-----

The admin will be using the *Admin Workstation* with Tails to connect to
the App Server and the Monitor Server using Tor and SSH. The tasks
performed by the admin will require the following set of passphrases:

-  A password for the persistent volume on the Admin Live USB.
-  A master password for the KeePassX password manager, which unlocks
   passphrases to:

   -  The App Server and the Monitor Server (required to be the same).
   -  The network firewall.
   -  The SSH private key and, if set, the key's passphrase.
   -  The GPG key that OSSEC will encrypt alerts to.
   -  The admin's personal GPG key.
   -  The credentials for the email account that OSSEC will send alerts
      to.
   -  The Hidden Services values required to connect to the App and
      Monitor Server.

The admin will also need to have an Android or iOS device with the
Google Authenticator app installed. This means the admin will also have
the following two credentials:

-  The secret code for the App Server's two-factor authentication.
-  The secret code for the Monitor Server's two-factor authentication.

Journalist
----------

The journalist will be using the *Journalist Workstation* with Tails to
connect to the Document Interface. The tasks performed by the journalist
will require the following set of passphrases:

-  A master password for the persistent volume on the Tails device.
-  A master password for the KeePassX password manager, which unlocks
   passphrases to:

   -  The Hidden Service value required to connect to the Document
      Interface.
   -  The Document Interface.
   -  The journalist's personal GPG key.

The journalist will also need to have a two-factor authenticator, such
as an Android or iOS device with Google Authenticator installed, or a
YubiKey. This means the journalist will also have the following
credential:

-  The secret code for the Document Interface's two-factor
   authentication.

Secure Viewing Station
~~~~~~~~~~~~~~~~~~~~~~

The journalist will be using the *Secure Viewing Station* with Tails to
decrypt and view submitted documents. The tasks performed by the
journalist will require the following passphrases:

-  A master password for the persistent volume on the Tails device.

The backup that is created during the installation of SecureDrop is also
encrypted with the application's GPG key. The backup is stored on the
persistent volume of the Admin Live USB.
