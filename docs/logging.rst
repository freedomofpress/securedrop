Useful Logs
===========

Both servers
------------

- AppArmor and grsec errors: ``/var/log/kern.log``
- iptables: ``/var/log/syslog``

*Application Server*
--------------------

- Apache: ``/var/log/apache2/*``

If an error is triggered it's in the SecureDrop application logs:
``/var/log/apache2/source-error.log`` and
``/var/log/apache2/journalist-error.log``

*Monitor Server*
----------------

- OSSEC ::

     /var/ossec/logs/ossec.log
     /var/ossec/logs/alerts/alerts.log

- Postfix/Procmail ::

     /var/log/mail.log
     /var/log/procmail.log
