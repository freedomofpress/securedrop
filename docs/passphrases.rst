Passphrases
===========

Each individual with a role (admin or journalist) at a given
SecureDrop instance must generate and retain a number of strong,
unique passphrases. The document is an overview of the passphrases,
keys, two-factor secrets, and other credentials that are required for
each role in a SecureDrop installation.

.. note:: We encourage each end user to use KeePassXC, an easy-to-use
          password manager included in Tails, to generate and retain
          strong and unique passphrases. The SecureDrop code repository includes
          a template that you can use to initialize this database for an
          *Admin Workstation* or a *Journalist Workstation*. For more
          information, see the :ref:`KeePassXC setup instructions <keepassxc_setup>`.

.. tip:: For best practices on managing passphrases, see
   :doc:`passphrase_best_practices`.

Admin
-----

The admin will be using the *Admin Workstation* with Tails to connect to
the *Application Server* and the *Monitor Server* using Tor and SSH. The tasks
performed by the admin will require the following set of credentials and
passphrases:

-  A passphrase for the persistent volume on the Admin Live USB.
-  Additional credentials, which we recommend adding to Tails' KeePassXC password
   manager during the installation:

   -  The *Application Server* and *Monitor Server* admin username and password
      (required to be the same for both servers).
   -  The network firewall username and password.
   -  The SSH private key and, if set, the key's passphrase.
   -  The GPG key that OSSEC will encrypt alerts to.
   -  The admin's personal GPG public key, if you want to potentially encrypt
      sensitive files to it for further analysis.
   -  The account details for the destination email address for OSSEC alerts.
   -  The Onion Services values required to connect to the *Application* and
      *Monitor Servers*.


The admin will also need to have a way to generate two-factor
authentication codes.

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
-  A master passphrase for the KeePassXC password manager, which unlocks
   passphrases to:

   -  The Hidden Service value required to connect to the Journalist
      Interface.
   -  The *Journalist Interface*.

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

*Transfer Device* and *Export Device*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As noted in the :doc:`setup guide <set_up_transfer_and_export_device>`,
we recommend using encrypted USB drives for transferring files to the
*Secure Viewing Station*, and for exporting them from the *SVS* in situations
where using a secure printer or a similar analog conversion is not an option.

For every copy operation, the user will need to enter the USB drive's encryption
passphrase at least twice (on the computer they're copying from, and on the
computer they're copying to). To make it easy for them to find the passphrase,
we recommend storing it in the journalist's own existing password manager,
which should be accessible using their smartphone.
