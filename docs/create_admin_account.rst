Create an admin account on the Document Interface
=================================================

In order for any user (administrator or journalist) to access the
Document Interface, they need:

1. The ``auth-cookie`` for the Document Interface's ATHS
2. An account on the Document Interface, which requires the following
   credentials to log in:

   * Username
   * Password
   * Two-factor authentication code

You should create a separate account on the Document Interface for
each user who needs access. This makes it easy to enable or disable
access to the Document Interface on an individual basis, so you can
grant access to new users or revoke access for users who have left the
organization or should no longer be allowed to access the Document
Interface.

There are two types of accounts on the Document Interface: admin
accounts and normal accounts. Admins accounts are like normal
accounts, but they are additionally allowed to manage (add, change,
delete) other user accounts through the web interface.

You must create the first admin account on the Document Interface by
running a command on the App Server. After that, the Document
Interface admin can create additional accounts through the web
interface.

To create the first admin account, SSH to the App Server, then:

.. code:: sh

   $ sudo su
   $ cd /var/www/securedrop
   $ ./manage.py add_admin

Follow the prompts.

.. todo:: Clarify how to set up TOTP/HOTP through ``./manage.py
          add_admin``.
	  
Once that's done, you should open the Tor Browser |TorBrowser| and
navigate to the Document Interface's .onion address. Verify that you
can log in to the Document Interface with the admin account you just
created.

For adding more user accounts, please refer now to our :doc:`Admin
Interface Guide <admin>`.

.. |TorBrowser| image:: images/torbrowser.png
