Create users for the web application
====================================

Now SSH to the App Server, ``sudo su``, cd to ``/var/www/securedrop``,
and run ``./manage.py add_admin`` to create the first admin user for
yourself. Make a password and store it in your KeePassX database. This
admin user is for the SecureDrop Admin + Document Interface and will
allow you to create accounts for the journalists.

The ``add_admin`` command will require you to keep another two-factor
authentication code. Once that's done, you should open the Tor Browser
|TorBrowser| and navigate to the Document Interface's .onion address.

For adding journalist users, please refer now to our `Admin Interface
Guide </docs/admin_interface.md>`__.

.. |TorBrowser| image:: images/torbrowser.png
