Useful Logs
===========

Both servers
------------

- AppArmor and grsec errors: ``/var/log/kern.log``
- iptables: ``/var/log/syslog``

App Server
----------

- Apache: ``/var/log/apache2/*``

If an event triggers it's in the SecureDrop application log:
``/var/www/securedrop/securedrop.log``

Monitor Server
--------------

- OSSEC ::

     /var/ossec/log/ossec.log
     /var/ossec/log/alerts/alerts.log

- Postfix/Procmail ::

     /var/log/mail.log
     /var/log/procmail.log
