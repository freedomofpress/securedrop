.. _ossec_guide:

OSSEC Guide
===========

Setting Up OSSEC Alerts
-----------------------

OSSEC is an open source host-based intrusion detection system (IDS) that
we use to perform log analysis, file integrity checking, policy
monitoring, rootkit detection and real-time alerting. It is installed on
the *Monitor Server* and constitutes that machine's main function. OSSEC
works in a server-agent scheme, that is, the OSSEC server extends its
existing functions to the *Application Server* through an agent installed on that
server, covering monitoring for both machines.

In order to receive email alerts from OSSEC, you need to supply several
settings to Ansible in the playbook for your environment. If you don't
already have a working mail server or don't know what to do, then see
the section below about using Gmail as a fallback option. We assume that
you're working out of the 'securedrop' directory you cloned the code
into, and editing ``install_files/ansible-base/group_vars/all/site-specific``
prior to installing SecureDrop.

What you need:

-  The GPG key that OSSEC will encrypt alerts to
-  The email address that will receive alerts from OSSEC
-  Information for your SMTP server or relay (hostname, port)
-  Credentials for the email address that OSSEC will send alerts from

Receiving email alerts from OSSEC requires that you have an SMTP relay
to route the emails. You can use an SMTP relay hosted internally, if one
is available to you, or you can use a third-party SMTP relay such as
Gmail. The SMTP relay does not have to be on the same domain as the
destination email address, i.e. smtp.gmail.com can be the SMTP relay and
the destination address can be securedrop@freedom.press.

While there are risks involved with receiving these alerts, such as
information leakage through metadata, we feel the benefit of knowing how
the SecureDrop servers are functioning is worth it. If a third-party
SMTP relay is used, that relay will be able to learn information such as
the IP address the alerts were sent from, the subject of the alerts, and
the destination email address the alerts were sent to. Only the body of
an alert email is encrypted with the recipient's GPG key. A third-party
SMTP relay could also prevent you from receiving any or specific alerts.

The SMTP relay that you use should support SASL authentication and SMTP
TLS protocols TLSv1.2, TLSv1.1, and TLSv1. Most enterprise email
solutions should be able to meet those requirements.

Below are the values you must specify in to configure OSSEC correctly.
For first-time installs, you can use the
:ref:`configuration playbook<configure_securedrop>`, or edit
``install_files/ansible-base/group_vars/all/site-specific`` manually.

- GPG public key used to encrypt OSSEC alerts:
  ``ossec_alert_gpg_public_key``
- Fingerprint of key used when encrypting OSSEC alerts:
  ``ossec_gpg_fpr``
- The email address that will receive alerts from OSSEC:
  ``ossec_alert_email``
- The reachable hostname of your SMTP relay: ``smtp_relay``
- The secure SMTP port of your SMTP relay: ``smtp_relay_port``
  (typically 25, 587, or 465. must support TLS encryption)
- Email username to authenticate to the SMTP relay: ``sasl_username``
- Domain name of the email used to send OSSEC alerts: ``sasl_domain``
- Password of the email used to send OSSEC alerts: ``sasl_password``

If you don't know what value to enter for one of these, please ask your
organization's email admin for the full configuration before
proceeding. It is better to get these right the first time rather than
changing them after SecureDrop is installed. If you're not sure of the
correct ``smtp_relay_port`` number, you can use a simple mail client
such as Thunderbird to test different settings or a port scanning tool
such as nmap to see what's open. You could also use telnet to make sure
you can connect to an SMTP server, which will always transmit a reply
code of 220 meaning "Service ready" upon a successful connection.

The ``smtp_relay`` mail server hostname is often, but not always,
different from the ``sasl_domain``, e.g. smtp.gmail.com and gmail.com.

In some cases, authentication or transport encryption mechanisms will
vary and you may require later edits to the Postfix configuration
(mainly /etc/postfix/main.cf) on the *Monitor Server* in order to get
alerts to work. You can consult `Postfix's official
documentation <http://www.postfix.org/documentation.html>`__ for help,
although we've described some common scenarios in the
:ref:`troubleshooting section <troubleshooting_ossec>`.

If you have your GPG public key handy, copy it to
``install_files/ansible-base`` and then specify the filename, e.g.
``ossec.pub``, in the ``ossec_alert_gpg_public_key`` line of
``group_vars/all/site-specific``.

If you don't have your GPG key ready, you can run GnuPG on the command line in
order to find, import, and export your public key. It's best to copy the key
from a trusted and verified source, but you can also request it from keyservers
using the known fingerprint. Looking it up by email address or a shorter key ID
format could cause you to obtain a wrong, malicious, or expired key. Instead, we
recommend you type out your fingerprint in groups of four (just like GPG prints
it) enclosed by double quotes.  The reason we suggest this formatting for the
fingerprint is simply because it's easiest to type and verify correctly. In the
code below simply replace ``<fingerprint>`` with your full, space-separated
fingerprint:

Download your key and import it into the local keyring: ::

    gpg --recv-key "<fingerprint>"

.. note:: It is important you type this out correctly. If you are not
          copy-pasting this command, we recommend you double-check you have
          entered it correctly before pressing enter.

Again, when passing the full public key fingerprint to the ``--recv-key`` command, GPG
will implicitly verify that the fingerprint of the key received matches the
argument passed.

.. caution:: If GPG warns you that the fingerprint of the key received
             does not match the one requested **do not** proceed with
             the installation. If this happens, please email us at
             securedrop@freedom.press.

Next we export the key to a local file. ::

    gpg --export -a "<fingerprint>" > ossec.pub


Copy the key to a directory where it's accessible by the SecureDrop
installation: ::

    cp ossec.pub install_files/ansible-base/

The fingerprint is a unique identifier for an encryption (public) key.  The
short and long key ids correspond to the last 8 and 16 hexadecimal digits of the
fingerprint, respectively, and are thus a subset of the fingerprint. The value
for ``ossec_gpg_fpr`` must be the full 40 hexadecimal digit GPG fingerprint for
this same key, with all capital letters and no spaces. The following command
will retrieve and format the fingerprint per our requirements: ::

    gpg --with-colons --fingerprint "<fingerprint>" | grep "^fpr" | cut -d: -f10

Next you specify the e-mail that you'll be sending alerts to, as
``ossec_alert_email``. This could be your work email, or an alias for a
group of IT admins at your organization. It helps for your mail
client to have the ability to filter the numerous messages from OSSEC
into a separate folder.

Now you can move on to the SMTP and SASL settings, which are
straightforward. These correspond to the outgoing e-mail address used to
send the alerts instead of where you're receiving them. If that e-mail
is ossec@news-org.com, the ``sasl_username`` would be ossec and
``sasl_domain`` would be news-org.com.

The Postfix configuration enforces certificate verification, and
requires both a valid certificate and STARTTLS support on the SMTP
relay. By default the system CAs will be used for validating the relay
certificate. If you need to provide a custom CA to perform the
validation, copy the cert file to ``install_files/ansible-base`` add a
new variable to ``group_vars/all/site-specific``: ::

    smtp_relay_cert_override_file: MyOrg.crt

where ``MyOrg.crt`` is the filename. The file will be copied to the
server in ``/etc/ssl/certs_local`` and the system CAs will be ignored
when validating the SMTP relay TLS certificate.

Save ``group_vars/all/site-specific``, exit the editor and :ref:`proceed with
the installation <Install SecureDrop Servers>` by running the playbooks.

Using Gmail for OSSEC Alerts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It's easy to get SecureDrop to use Google's servers to deliver the
alerts, but it's not ideal from a security perspective. This option
should be regarded as a backup plan. Keep in mind that you're leaking
metadata about the timing of alerts to a third party — the alerts are
encrypted and only readable to you, however that timing may prove useful
to an attacker.

First you should `sign up for a new
account <https://accounts.google.com/SignUp?service=mail>`__. While it's
technically possible to use an existing Gmail account, it's best to
compartmentalize these alerts from any of your other activities. Choose
a strong and random passphrase for the new account. Skip the creation of
a Google+ profile and continue straight to Gmail. Next, enable `Google's
2-Step Verification <https://www.google.com/landing/2step/>`__. With
2-Step Verification enabled, you won't use the normal account password
in this configuration — it will not work; instead you must navigate
(using the settings in the top right) to Account > Signing in > App
passwords, and generate a new App password which you will use as the
``sasl_passwd``.

Once the account is created you can log out and provide the values for
``sasl_username`` as your new Gmail username (without the domain),
``sasl_domain``, which is typically gmail.com (or your custom Google
Apps domain), and ``sasl_passwd``. Remember to use the App password
generated from the 2-step config for ``sasl_passwd``, as the primary
account password won't work. The ``smtp_relay`` is smtp.gmail.com and
the ``smtp_relay_port`` is 587.

Configuring Fingerprint Verification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you run your own mail server, you may wish to increase the security
level used by Postfix for sending mail to ``fingerprint``, rather than
``secure``. Doing so will require an exact match for the fingerprint of
TLS certificate on the SMTP relay. The advantage to fingerprint
verification is additional security, but the disadvantage is potential
maintenance cost if the fingerprint changes often. If you manage the
mail server and handle the certificate rotation, you should update the
SecureDrop configuration whenever the certificate changes, so that OSSEC
alerts continue to send. Using fingerprint verification does not work
well for popular mail relays such as smtp.gmail.com, as those
fingerprints can change frequently, due to load balancing or other
factors.

You can retrieve the fingerprint of your SMTP relay by running the
command below (all on one line). Please note that you will need to
replace ``smtp.gmail.com`` and ``587`` with the correct domain and port
for your SMTP relay. ::

    openssl s_client -connect smtp.gmail.com:587 -starttls smtp < /dev/null 2>/dev/null |
        openssl x509 -fingerprint -noout -in /dev/stdin | cut -d'=' -f2

If you are using Tails, you will not be able to connect directly with
``openssl s_client`` due to the default firewall rules. To get around
this, proxy the requests over Tor by adding ``torify`` at the beginning
of the command. The output of the command above should look like the
following:

::

    6D:87:EE:CB:D0:37:2F:88:B8:29:06:FB:35:F4:65:00:7F:FD:84:29

Finally, add a new variable to ``group_vars/all/site-specific`` as
``smtp_relay_fingerprint``, like so: ::

    smtp_relay_fingerprint: "6D:87:EE:CB:D0:37:2F:88:B8:29:06:FB:35:F4:65:00:7F:FD:84:29"

Specifying the fingerprint will configure Postfix to use it for
verification on the next playbook run. (To disable fingerprint
verification, simply delete the variable line you added, and rerun the
playbooks.) Save ``group_vars/all/site-specific``, exit the editor and
:ref:`proceed with the installation <Install SecureDrop Servers>` by running the
playbooks.

.. _troubleshooting_ossec:

Troubleshooting
---------------

Some OSSEC alerts should begin to arrive as soon as the installation has
finished.

The easiest way to test that OSSEC is working is to SSH to the Monitor
Server and run ``service ossec restart``. This will trigger an Alert
level 3 saying: "Ossec server started."

So you've finished installing SecureDrop, but you haven't received any
OSSEC alerts. First, check your spam/junk folder. If they're not in
there, then most likely there is a problem with the email configuration.
In order to find out what's wrong, you'll have to SSH to the Monitor
Server and take a look at the logs. To examine the mail log created by
Postfix, run the following command: ::

    tail /var/log/mail.log

The output will show you attempts to send the alerts and provide hints
as to what went wrong. Here's a few possibilities and how to fix them:

================================ ===================================================
Problem                          Solution
================================ ===================================================
Connection timed out             | Check that the hostname and port is correct
                                   in the relayhost line of
                                 | ``/etc/postfix/main.cf``
Server certificate not verified  | Check that the relay certificate is valid
                                   (for more detailed help, see `Troubleshooting
                                   SMTP TLS <#troubleshooting-smtp-tls>`_).
                                   Consider adding ``smtp_relay_cert_override_file``
                                 | to ``prod_specific.yml`` as described above.
Authentication failure           | Edit ``/etc/postfix/sasl_passwd`` and make
                                   sure the username, domain and password are
                                   correct. Run ``postmap /etc/postfix/sasl_passwd``
                                 | to update when finished.
================================ ===================================================

After making changes to the Postfix configuration, you should run
``service postfix reload`` and test the new settings by restarting the
OSSEC service.

.. tip:: If you change the SMTP relay port after installation for any
         reason, you must update the ``smtp_relay_port`` variable in the
         ``group_vars/all/site-specific`` file, then rerun the Ansible playbook.
         As a general best practice, we recommend modifying and
         rerunning the Ansible playbook instead of manually editing
         the files live on the servers, since values like ``smtp_relay_port``
         are used in several locations throughout the config.

Useful Log Files for OSSEC
~~~~~~~~~~~~~~~~~~~~~~~~~~

Other log files that may contain useful information:

/var/log/procmail.log
    Includes lines for sending mail containing OSSEC alerts.

/var/log/syslog
    Messages related to grsecurity, AppArmor and iptables.

/var/ossec/logs/ossec.log
    OSSEC's general operation is covered here.

/var/ossec/logs/alerts/alerts.log
    Contains details of every recent OSSEC alert.

.. tip:: Remember to encrypt any log files before sending via email,
         for example to securedrop@freedom.press, in order to protect
         security-related information about your organization's
         SecureDrop instance.

Not Receiving Emails
~~~~~~~~~~~~~~~~~~~~
Some mail servers require that the sending email address match the account
that authenticated to send mail. By default the *Monitor Server* will use
``ossec@ossec.server`` for the from line, but your mail provider may not support
the mismatch between the domain of that value and your real mail host.
If the Admin email address (configured as ``ossec_alert_email`` in
``group_vars/all/site-specific``) does not start receiving OSSEC alerts updates shortly
after the first playbook run, try setting ``ossec_from_address`` in
``group_vars/all/site-specific`` to the full email address used for sending the alerts,
then run the playbook again.

Message Failed to Encrypt
~~~~~~~~~~~~~~~~~~~~~~~~~
If OSSEC cannot encrypt the alert to the GPG public key for the Admin
email address (configured as ``ossec_alert_email`` in ``group_vars/all/site-specific``),
the system will send a static message instead of the scheduled alert:

  Failed to encrypt OSSEC alert. Investigate the mailing configuration on the Monitor Server.

Check the GPG configuration vars in ``group_vars/all/site-specific``. In particular,
make sure the GPG fingerprint matches that of the public key file you
exported.

Troubleshooting SMTP TLS
~~~~~~~~~~~~~~~~~~~~~~~~

Your choice of SMTP relay server must support STARTTLS and have a valid
server certificate. By default, the *Monitor Server*'s Postfix
configuration will try to validate the server certificate using the
default root store (in Ubuntu, this is maintained in the
``ca-certificates`` package). You can override this by setting
``smtp_relay_cert_override_file`` as described earlier in this document.

In either situation, it can be helpful to use the ``openssl`` command
line tool to verify that you can successfully connect to your chosen
SMTP relay securely. We recommend doing this before running the
playbook, but it can also be useful as part of troubleshooting OSSEC
email send failures.

In either case, start by attempting to make a STARTTLS connection to
your chosen ``smtp_relay:smtp_relay_port`` (get the values from your
``group_vars/all/site-specific`` file). On a machine running Ubuntu, run the
following ``openssl`` command, replacing ``smtp_relay`` and
``smtp_relay_port`` with your specific values: ::

    openssl s_client -showcerts -starttls smtp -connect smtp_relay:smtp_relay_port < /dev/null 2> /dev/null

Note that you will not be able to run this command on the Application
Server because of the firewall rules. You can run it on the Monitor
Server, but you will need to run it as the Postfix user (again, due to
the firewall rules): ::

    sudo -u postfix openssl s_client -showcerts -starttls smtp -connect smtp.gmail.com:587 < /dev/null 2> /dev/null

If the command fails with "Could not connect" or a similar message, then
this mail server does not support STARTTLS. Verify that the values you
are using for ``smtp_relay`` and ``smtp_relay_port`` are correct. If
they are, you should contact the admin of that relay and talk to them
about supporting STARTTLS, or consider using another relay that already
has support.

If the command succeeds, the first line of the output should be
"CONNECTED" followed by a lot of diagnostic information about the
connection. You should look for the line that starts with "Verify return
code", which is usually one of the last lines of the output. Since we
did not give ``openssl`` any information about how to verify
certificates in the previous command, it should be a non-zero value
(indicating verification failed). In my case, it is
``Verify return code: 20 (unable to get local issuer certificate)``,
which indicates that openssl does not know how to build the certificate
chain to a trusted root.

If you are using the default verification setup, you can check whether
your cert is verifiable by the default root store with ``-CApath``: ::

    openssl s_client -CApath /etc/ssl/certs -showcerts -starttls smtp -connect smtp_relay:smtp_relay_port < /dev/null 2> /dev/null

For example, if I'm testing Gmail as my SMTP relay
(``smtp.gmail.com:587``), running the ``openssl`` with the default root
store results in ``Verify return code: 0 (ok)`` because their
certificate is valid and signed by one of the roots in the default
store. This indicates that can be successfully used to securely relay
email in the default configuration of the *Monitor Server*.

If your SMTP relay server does not successfully verify, you should use
the return code and its text description to help you diagnose the cause.
Your cert may be expired, in which case you should renew it. It may not
be signed by a trusted CA, in which case you should obtain a signature
from a trusted CA and install it on the mail server. It may not have the
right hostnames in the Common Name or Subject Alternative Names, in
which case you will need to generate a new CSR with the correct
hostnames and then obtain a new certificate and install it. Etc., etc.

If you are *not* using the the default verification setup, and
intentionally do not want to use a certificate signed by one of the
default CA's in Ubuntu, you can still use ``openssl`` to test whether
you can successfully negotiate a secure connection. Begin by copying
your certificate file (``smtp_relay_cert_override_file`` from
``group_vars/all/site-specific``) to the computer you are using for testing. You
can use ``-CAfile`` to test if your connection will succeed using your
custom root certificate: ::

    openssl s_client -CAfile /path/to/smtp_relay_cert_override_file -showcerts -starttls smtp -connect smtp_relay:smtp_relay_port < /dev/null 2> /dev/null

Finally, if you have a specific server in mind but are not sure what
certificate you need to verify the connection, you can use the output of
``openssl s_client`` to figure it out. Since we have ``-showcerts``
turned on, ``openssl`` prints the entire certificate chain it receives
from the server. A properly configured server will provide all of the
certificates in the chain up to the root cert, which needs to be
identified as "trusted" for the verification to succeed. To see the
chain, find the part of the output that start with
``Certificate chain``. It will look something like this (example from
``smtp.gmail.com``, with certificate contents snipped for brevity): ::

    ---
    Certificate chain
    0 s:/C=US/ST=California/L=Mountain View/O=Google Inc/CN=smtp.gmail.com
    i:/C=US/O=Google Inc/CN=Google Internet Authority G2
    -----BEGIN CERTIFICATE-----
    <snip>
    -----END CERTIFICATE-----
    1 s:/C=US/O=Google Inc/CN=Google Internet Authority G2
    i:/C=US/O=GeoTrust Inc./CN=GeoTrust Global CA
    -----BEGIN CERTIFICATE-----
    <snip>
    -----END CERTIFICATE-----
    2 s:/C=US/O=GeoTrust Inc./CN=GeoTrust Global CA
    i:/C=US/O=Equifax/OU=Equifax Secure Certificate Authority
    -----BEGIN CERTIFICATE-----
    <snip>
    -----END CERTIFICATE-----
    ---

The certificates are in reverse order from leaf to root. ``openssl``
handily prints the Subject (``s:``) and Issuer (``i:``) information for
each cert. In order to find the root certificate, look at the Issuer of
the last certificate. In this case, that's
``Equifax Secure Certificate Authority``. This is the root certificate
that issued the first certificate in the chain, and it is what you need
to tell Postfix to use in order to trust the whole connection.

Actually obtaining this certificate and establishing trust in it is
beyond the scope of this document. Typically, if you are using your own
SMTP relay with a custom CA, you will be able to obtain this certificate
from an intranet portal or someone on your IT staff. For a well-known
global CA, you can obtain it from the CA's website. For example, a quick
search for "Equifax Secure Certificate Authority" finds the web page of
`GeoTrust's Root
Certificates <https://www.geotrust.com/resources/root-certificates/>`__,
which have accompanying background information and are available for
download.

Once you have the root certificate file, you can use ``-CAfile`` to test
that it will successfully verify the connection.

.. _AnalyzingAlerts:

Analyzing the Alerts
--------------------

Understanding the contents of the OSSEC alerts requires a background and
knowledge in Linux systems administration. They may be confusing, and at
first it will be hard to tell between a genuine problem and a fluke. You
should examine these alerts regularly to ensure that the SecureDrop
environment has not been compromised in any way, and follow up on any
particularly concerning messages with direct investigation.

Common OSSEC Alerts
~~~~~~~~~~~~~~~~~~~

The SecureDrop *Application* and *Monitor Servers* reboot every night, as part
of the unattended upgrades process. Therefore, on nights where packages were updated,
you should receive email alerts every morning indicating binaries have changed.
Below is a sample alert, but you may see any number of these records in the
logs. This will happen in batches so these emails might be longer than the
below alert. You should also see them in an email named ``Daily Report:
File Changes``. To verify this activity matches the package history, you
can review the logs in ``/var/log/apt/history.log``. ::

    Received From: (app)
    Rule: 2902 fired (level 7) -> "New (Debian Package) installed."
    Portion of the log(s):

    status installed <package name> <version>

These are normal alerts, they tell you your system is up-to-date and patched.

Occasionally your SecureDrop Servers will send an alert for failing to connect
to Tor relays. Since SecureDrop runs as a Tor Onion Service, it is possible
for Tor connections to timeout or become overloaded. ::

    Received From: (app)
    Rule: 1002 fired (level 2) -> "Unknown problem somewhere in the system."
    Portion of the log(s):

    [warn] Your Guard <name> ($fingerprint) is failing a very large amount of
    circuits. Most likely this means the Tor network is overloaded, but it
    could also mean an attack against you or potentially the guard itself.

This alert is common but if you see them for sustained periods of time (several
times a day), please contact us at the `SecureDrop Support Portal`_ or at
securedrop@freedom.press for help.

.. _SecureDrop Support Portal: https://securedrop-support.readthedocs.io/en/latest/

Uncommon OSSEC Alerts
~~~~~~~~~~~~~~~~~~~~~

.. _uncommon_alerts:

SecureDrop also runs automatic checks for submission data integrity
problems. For example, secure deletion of large submissions could
potentially be interrupted, resulting in an alert recommending steps
to :ref:`clean them up <submission-cleanup>`.

In addition, SecureDrop performs a daily configuration check to ensure that
the iptables rules configured on the *Application* and *Monitor Server* match
the expected configuration. If they do not, you may receive a level 12 alert
like the following: ::

      Received From: (app) 10.20.2.2->/var/ossec/checksdconfig.py
      Rule: 400900 fired (level 12) ->
      "Indicates a problem with the configuration of the SecureDrop servers."
      Portion of the log(s):
      ossec: output: '/var/ossec/checksdconfig.py': System configuration error:
      The iptables default drop rules are incorrect.

Alternatively, the error text may say: ``The iptables rules have not been configured.``

To resolve the issue, you can reinstate the standard iptables
rules by :ref:`updating the system configuration <update-system-configuration>`.

If you believe that the system is behaving abnormally, you should
contact us at the `SecureDrop Support Portal`_ or securedrop@freedom.press for
help.
