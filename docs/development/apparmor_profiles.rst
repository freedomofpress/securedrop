Generating AppArmor profiles for Tor and Apache
===============================================

.. code:: sh

    vagrant up /staging$/
    vagrant ssh app-staging
    sudo su
    cd /var/www/securedrop

Run tests, use the application web interface, restart services,
reboot the VMs via ``vagrant reload /staging/``. The goal is to
create as much interaction with the system as possible, in order
to establish an expected baseline of behavior. Then run:

.. code::

    aa-logprof

Follow the prompts on screen and save the new configuration.
Then set the profile to complain mode:

.. code::

    aa-complain /etc/apparmor.d/<PROFILE_NAME>

Rinse and repeat, again running ``aa-logprof`` to update the profile.
The AppArmor profiles are saved in ``/etc/apparmor.d/``. There are two
profiles:

    -  ``/etc/apparmor.d/usr.sbin.tor``
    -  ``/etc/apparmor.d/usr.sbin.apache2``

After running ``aa-logprof`` you will need to copy the modified profile back to
your host machine to include them in the ``securedrop-app-code`` package.

.. code:: sh

   ansible -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory app-prod -m fetch -a 'flat=yes dest=install_files/ansible-base/ src=/etc/apparmor.d/usr.sbin.apache2'
   ansible -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory app-prod -m fetch -a 'flat=yes dest=install_files/ansible-base/ src=/etc/apparmor.d/usr.sbin.tor'

The AppArmor profiles are packaged with the ``securedrop-app-code``.
The ``securedrop-app-code`` ``postinst`` puts the AppArmor profiles in enforce mode
on production and staging hosts.
