Administrator Guide
=====================

At this point, you (the administrator) should have your own username and
password, plus two-factor authentication through either the Google
Authenticator app on your smartphone or a YubiKey.

.. _Adding Users:

Adding Users
------------

Now you can add new logins for the journalists at your news organization
who will be checking the system for submissions. Make sure the
journalist is physically in the same room as you when you do this, as
they will have to create a password and scan a barcode for their
two-factor authentication. Since you’re logged in, this is the screen
you should see now:

|“SecureDrop main page”|

In the top right corner click the “Admin” link, which should bring you
to this page:

|“SecureDrop admin home”|

Once there, click ‘Add User’ button, which will take you to this page:

|“Add a new user”|

Here, you will hand the keyboard over to the journalist so they can
create their own username and password. Once they’re done entering a
username and password for themselves, select whether you would like them
to also be an administrator (this allows them to add or delete other
journalist accounts), and whether they will be using Google
Authenticator or a YubiKey for two-factor authentication.

Google Authenticator
~~~~~~~~~~~~~~~~~~~~

If they are using Google Authenticator for their two-factor, they can
just proceed to the next page:

|“Enable Google Authenticator”|

At this point, the journalist should make sure they have downloaded the
Google Authenticator app to their smartphone. It can be installed from
the Apple Store for an iPhone or from the Google Play store for an
Android phone. Once you download it and open it, the app does not
require setup. It should prompt you to scan a barcode. The journalist
should use their phone's camera to scan the barcode on the screen.

If they have difficulty scanning the barcode, they can use the "Manual
Entry" option and use their phone's keyboard to input the random
characters that are highlighted in yellow.

Inside the Google Authenticator app, a new entry for this account will
appear on the main screen, with a six digit number that recycles to a
new number every thirty seconds. Enter the six digit number under
“Verification code” at the bottom of the SecureDrop screen here, and hit
enter:

|“Verify Google Authenticator works”|

If Google Authenticator was set up correctly, you will be redirected
back to the Admin Interface and will see a flashed message that says
"Two factor token successfully verified for user *new username*!".

YubiKey
~~~~~~~

If the journalist wishes to use a YubiKey for two-factor authentication,
check the box next to "I'm using a YubiKey". You will then need to enter
the OATH-HOTP Secret Key that your YubiKey is configured with. For more
information, read the :doc:`YubiKey Setup Guide <yubikey_setup>`.

|"Enable YubiKey"|

Once you've configured your YubiKey and entered the Secret Key, click
*Add user*. On the next page, enter a code from your YubiKey by
inserting it into the workstation and pressing the button.

|"Verify YubiKey"|

If everything was set up correctly, you will be redirected back to the
Admin Interface, where you should see a flashed message that says "Two
factor token successfully verified for user *new username*!".

Congratulations! You have successfully set up a journalist on
SecureDrop. Make sure the journalist remembers their username and
password and always has their 2 factor authentication device in their
possession when they attempt to log in to SecureDrop.

.. |“SecureDrop main page”| image:: images/admin_main_home.png
.. |“SecureDrop admin home”| image:: images/admin_secondary_home.png
.. |“Add a new user”| image:: images/admin_add_new_user.png
.. |“Enable Google Authenticator”| image:: images/admin_enable_authenticator.png
.. |“Verify Google Authenticator works”| image:: images/admin_enter_verification.png
.. |"Enable YubiKey"| image:: images/admin_enable_yubikey.png
.. |"Verify YubiKey"| image:: images/admin_verify_yubikey.png
