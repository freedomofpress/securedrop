.. _updating_ossec_rules:

Updating OSSEC Rules
====================

SecureDrop uses the OSSEC open source host-based intrusion detection system
(IDS) for log analysis, file integrity checking, policy monitoring, rootkit
detection and real-time alerting. Refer to our :ref:`OSSEC guide <ossec_guide>`
to learn more about how SecureDrop admins set up and monitor OSSEC alerts.

Alerting Strategy
-----------------

The goals of the OSSEC alerts in SecureDrop is to notify admins of:

1. Suspicious security events
2. Changes that require some kind of admin action
3. Other important notifications regarding system state.

If an alert is purely informational and there is no realistic action an
admin is expected to take, you should think carefully before
suggesting a rule for it. Each additional alert that admins must read and/or
respond to takes time. Alerts that are unimportant or otherwise require no action
can lead to alert fatigue and thus to critical alerts being ignored.

Using ``ossec-logtest``
-----------------------

Development on the OSSEC rules should be done from the staging environment.

On ``mon-staging``, there is a utility installed as part of OSSEC called
``ossec-logtest`` that you can use to test log events. In order to evaluate
whether an alert will be produced, and if so, what rule triggered it and its
level, you can simply pass the event to ``ossec-logtest``:

.. code:: sh

  root@mon-staging:/home/vagrant# sudo echo "Feb 10 23:34:40 app-prod kernel: [  124.188641] grsec: denied RWX mmap of <anonymous mapping> by /usr/sbin/apache2[apache2:1328] uid/euid:33/33 gid/egid:33/33, parent /usr/sbin/apache2[apache2:1309] uid/euid:0/0 gid/egid:0/0" | /var/ossec/bin/ossec-logtest
  2017/08/16 22:28:25 ossec-testrule: INFO: Reading local decoder file.
  2017/08/16 22:28:25 ossec-testrule: INFO: Started (pid: 18973).
  ossec-testrule: Type one log per line.

  **Phase 1: Completed pre-decoding.
         full event: 'Feb 10 23:34:40 app-prod kernel: [  124.188641] grsec: denied RWX mmap of <anonymous mapping> by /usr/sbin/apache2[apache2:1328] uid/euid:33/33 gid/egid:33/33, parent /usr/sbin/apache2[apache2:1309] uid/euid:0/0 gid/egid:0/0'
         hostname: 'app-prod'
         program_name: 'kernel'
         log: '[  124.188641] grsec: denied RWX mmap of <anonymous mapping> by /usr/sbin/apache2[apache2:1328] uid/euid:33/33 gid/egid:33/33, parent /usr/sbin/apache2[apache2:1309] uid/euid:0/0 gid/egid:0/0'

  **Phase 2: Completed decoding.
         decoder: 'iptables'

  **Phase 3: Completed filtering (rules).
         Rule id: '100101'
         Level: '7'
         Description: 'grsec error was detected'
  **Alert to be generated.

This is the utility we use in automated tests of OSSEC.

Writing Automated Tests for OSSEC Rules
---------------------------------------

We strongly recommend before making changes to OSSEC rules to attempt to write
a failing test which you then can make pass with a patch to the OSSEC rules:

1. Identify a log event you can use to trigger the alert.

.. warning:: Be sure to use only log events from test SecureDrop instances or
             those you have verified do not contain any sensitive data.

2. Write a Testinfra_ test to verify that the log event does or does not trigger
   an alert.
3. Apply your patch to the OSSEC rule on the relevant VM (likely ``app``).
4. Restart the service via ``sudo service ossec restart`` on ``mon``.

.. note:: Currently we only have automated tests for alerts triggered due to
          log events (for example not for `syscheck`_, OSSEC's integrity
          checking process). If you have ideas for additional automated test
          coverage of alerts, please suggest them in ticket `2134`_ on GitHub.

.. _Testinfra: https://testinfra.readthedocs.io/en/latest/
.. _syscheck: https://ossec-docs.readthedocs.io/en/latest/docs/manual/syscheck/index.html
.. _2134: https://github.com/freedomofpress/securedrop/issues/2134

Deployment
----------

The OSSEC rules and associated configuration files are distributed via Debian
packages maintained by Freedom of the Press Foundation. Any changes made to OSSEC
configuration files will land on production SecureDrop monitoring servers as
part of each SecureDrop release. This upgrade will occur automatically.

.. note:: The use of automatic upgrades for release deployment means that any
          changes made locally by admins to their OSSEC rules will not
          persist after a SecureDrop update.
