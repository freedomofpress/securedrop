Threat Model
============

This document outlines the threat model for SecureDrop 0.3 and is
inspired by a `document Adam Langley wrote for Pond
<https://web.archive.org/web/20150326154506/https://pond.imperialviolet.org/threat.html>`__.
The threat model is defined in terms of what each possible adversary
can achieve. This document is always a work in progress. If you have
questions or comments, please open an issue on GitHub or send an email
to securedrop@freedom.press.

Actors
------

The SecureDrop ecosystem comprises a host of actors, organzed by the following high-level categories: :ref:`Users <users>`, :ref:`Adversaries <adversaries>`, and :ref:`Systems <systems>`. 

.. _users:

Users
~~~~~

The following table of the users who interact with the SecureDrop web application. 
Note that the airgapped SVS with the GPG submission key is required to decrypt
submissions or messages.

+------------------+----------+-------------------------------------------------+
| User Type        | Trust Level                                                |
+==================+============================================================+
| Source           | * Submit a document or message                             |
+------------------+------------------------------------------------------------+
| Recurring source | * Submit another document or message                       |
|                  | * Read replies                                             |
+------------------+------------------------------------------------------------+
| Journalist       | * Download *all* gpg-encrypted documents from *all* sources|
|                  | * Download *all* gpg-encrypted messages from *all* sources |
|                  | * Reply to *all* sources                                   |
+------------------+------------------------------------------------------------+
| Admin            | * Download *all* gpg-encrypted documents from *all* sources|
|                  | * Download *all* gpg-encrypted messages from *all* sources |
|                  | * Reply to *all* sources                                   |
|                  | * Change the SecureDrop instance logo                      |
|                  | * SSH and root privileges on `app` and `mon` servers       |
+------------------+------------------------------------------------------------+

.. _adversaries:

Adversaries
~~~~~~~~~~~

We consider the following classes of attackers for the design and
assessment of SecureDrop:

+------------------+----------+-------------------------------------------------+
| Adversary        | Capabilities                                               |
+==================+============================================================+
| Nation State /   | * Large scale, full-packet network capture                 |
| Law Enforcement /| * Active network attacks                                   |
| Global Adversary | * Advanced attacks on infrastructure                       |
|                  | * Hardware and software implants for persistence           |
|                  | * Cryptanalysis                                            |
|                  | * Exploitation of unknown vulnerabilities                  |
+------------------+------------------------------------------------------------+
| Large Corporation| * Limited network capture                                  |
|                  | * Some targeted attacks on infrastructure                  |
|                  | * Use of known vulnerabilities                             |
|                  | * Mostly limited to software-based attacks                 |
+------------------+------------------------------------------------------------+
| Internet Service | * Full network capture                                     |
| Provider         | * Mostly limited to network-based attacks                  |
+------------------+------------------------------------------------------------+
| User Error       | * Source, Journalist, Administrator or Developer error     |
+------------------+------------------------------------------------------------+
| Dedicated        | * Use of known vulnerabilities                             |
| Individual       | * Mostly limited to software-based attacks                 |
+------------------+------------------------------------------------------------+

.. _systems:

Systems
~~~~~~~

For more information about the various systems involved in a SecureDrop
deployment, please visit the :doc:`hardware section <../hardware>`.

+------------------+----------+-------------------------------------------------+
| System           | Description                                                |
+==================+============================================================+
| Hardware Firewall| * Dedicated Hardware Firewall                              |
|                  | * pfSense-based                                            |
|                  | * 3 Interfaces: `app`, `mon` and `admin`                   |
+------------------+------------------------------------------------------------+
| Application      | * SecureDrop Source Interface                              |
| Server           | * SecureDrop Journalist Interface                          |
|                  | * SSH Server                                               |
|                  | * Ossec Client                                             |
+------------------+------------------------------------------------------------+
| Monitor Server   | * Ossec Server                                             |
|                  | * SSH Server                                               |
+------------------+------------------------------------------------------------+
| Journalist/Admin | * Internet-connected laptop                                |
| Workstation      | * Tails USB with persistence volume                        |
+------------------+------------------------------------------------------------+
| Secure Viewing   | * Airgapped and stripped-down laptop                       |
| Station (SVS)    | * Tails USB with persistence volume                        |
+------------------+------------------------------------------------------------+   

Assumptions
-----------

The following assumptions are accepted in the threat model of every SecureDrop project: 

Assumptions About the Source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The source acts reasonably and in good faith, e.g. if the source were to give their credentials or private key material to the attacker that would be unreasonable.
-  The source would like to remain anonymous, even against a forensic
   attacker.
-  The source obtains an authentic copy of Tails and the Tor Browser.
-  The source follows our :doc:`guidelines <../source>`
   for using SecureDrop.
-  The source is accessing an authentic SecureDrop site.

Assumptions About the Admin and the Journalist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The admin and the journalist act reasonably and in good faith, e.g.
   if either of them were to give their credentials or private key
   material to the attacker that would be unreasonable.
-  The admin and the journalist obtain authentic copies of Tails.
-  The journalist follows our
   :doc:`guidelines <../journalist>` for using SecureDrop
   and working with submitted documents.

Assumptions About the Person Installing SecureDrop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  This person (usually the admin) acts reasonably and in good faith, e.g. if they were
   to give the attacker system-level access that would be unreasonable.
-  The person obtains an authentic copy of SecureDrop and its
   dependencies.
-  The person follows our guidelines for
   :ref:`deploying the system <deployment>`, setting
   up the :ref:`landing page <Landing Page>` for the
   organization, and for :doc:`installing SecureDrop <../install>`.

Assumptions About the Source's Computer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The computer correctly executes Tails or the Tor Browser.
-  The computer is not compromised by malware.

Assumptions About the *Admin Workstation* and the *Journalist Workstation*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The computer correctly executes Tails.
-  The computer and the Tails device are not compromised by malware.
-  The two-factor authentication device used with the workstation are
   not compromised by malware.

Assumptions About the *Secure Viewing Station*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The computer is airgapped.
-  The computer correctly executes Tails.
-  The computer and the Tails device are not compromised by malware.

Assumptions About the SecureDrop Hardware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The servers correctly execute Ubuntu, SecureDrop and its
   dependencies.
-  The servers, network firewall, and physical media are not compromised
   by malware.

Assumptions About the Organization Hosting SecureDrop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The organization wants to preserve the anonymity of its sources.
-  The organization acts in the interest of allowing sources to submit
   documents, regardless of the contents of these documents.
-  The users of the system, and those with physical access to the
   servers, can be trusted to uphold the previous assumptions unless the
   entire organization has been compromised.
-  The organization is prepared to push back on any and all requests to
   compromise the integrity of the system and its users, including
   requests to deanonymize sources, block document submissions, or hand
   over encrypted or decrypted submissions.

Assumptions About the World
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The security assumptions of RSA (4096-bit GPG and SSH keys) are
   valid.
-  The security assumptions of scrypt with randomly-generated salts are
   valid.
-  The security/anonymity assumptions of Tor and the Hidden Service
   protocol are valid.
-  The security assumptions of the Tails operating system are valid.
-  The security assumptions of SecureDrop dependencies, specifically
   Ubuntu, the Linux kernel, application packages, application dependencies
   are valid.

Other Assumptions or Factors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The level of press freedom may vary in both geography and time.
-  The number of daily Tor users in a country can
   `greatly vary <https://metrics.torproject.org/userstats-relay-country.html>`__.

Assets
------

+------------------+----------+-------------------------------------------------+
| Asset Type       | Asset                                                      |
+==================+============================================================+
| Assets relating  | * Login details                                            |
| to SecureDrop    | * Encryption key(s)                                        |
| users            | * SSH details                                              |
+------------------+----------+-------------------------------------------------+
| Assets relating  | * Access to documents via server                           |
| to the publicly  | * Access to documents via Journalist Interface             |
| accessed system  | * Access to admin privileges via Journalist Interface      |
|                  | * Access to user alerts, support tickets                   |
+------------------+----------+-------------------------------------------------+
| Assets relating  | * SecureDrop code manipulation                             |
| to the           | * Dependency code manipulation                             |
| underlying       |                                                            |
| system           |                                                            |
+------------------+----------+-------------------------------------------------+

Attacks and Countermeasures on the SecureDrop Environment  
---------------------------------------------------------

SecureDrop is a complex ecosystem comprised of various pieces of hardware, a
diverse codebase, multiple user roles, and varied software dependencies. As
such, an adversary can compromise any one of these components through a variety
of attacks, as detailed below. We’ve categorized attacks and countermeasures by
SecureDrop architecture area for clarity.

There are certain attacks that cannot be mitigated by any of the technical or
operational countermeasures built into SecureDrop. Attacks of a political nature
— for example, if a source, journalist, or organization is threatened with legal
action — are context-dependent, and determined by an ever-shifting climate
around press freedoms. While these attack vectors are out of the scope of this
document, they should be factored in to any organization’s threat model with
regional and political specificity.

Attacks and Countermeasures on the Application Code via Journalist Interface, Source Interface, or SD Repository/Release
------------------------------------------------------------------------------------------------------------------------

Attacks to the Application Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Configuration vulnerability in *Source Interface* or *Journalist Interface*
-  Lack of segmentation between *Source Interface* and *Journalist Interface*
-  Session management vulnerability in *Source Interface* or *Journalist Interface*
-  Malicious input vulnerability in *Source Interface* or *Journalist Interface*
-  Configuration  vulnerability in *Source Interface* or *Journalist Interface*
-  Authentication vulnerability in *Source Interface* or *Journalist Interface*
-  Access control vulnerability in *Source Interface* or *Journalist Interface*
-  Data protection vulnerability in *Source Interface* or *Journalist Interface*
-  Communications vulnerability in *Source Interface* or *Journalist Interface*
-  Error handling and logging vulnerability in *Source Interface* or *Journalist Interface*
-  HTTP security configuration vulnerability in *Source Interface* or *Journalist Interface*
-  File and resource vulnerability in *Journalist interface*
-  Business logic vulnerability in *Source Interface*
-  Web services vulnerability in *Source Interface*
-  Malicious code introduced in SecureDrop repository
-  Malicious code introduced in SecureDrop release
-  Failure to encrypt submissions as they are written to disk

Countermeasures on the *Journalist Interface*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  *Journalist Interface* is located behind an authenticated hidden service and only privileged users have required authorization token
-  Tor hidden service protocol is end-to-end encrypted, and TLS is opt-in with EV cert, but no config option is supported
-  All source submissions are encrypted with GPG at rest using the airgapped submission key
-  Sensitive source and submission data is sent through HTTP POST
-  *Journalist Interface* sessions are invalidated after a user logs out or inactivity over 120 minutes. Session control includes CSRF token in Flask Framework.
-  All *Journalist Interface* session data (except language and locale selection) is discarded at logout, and fully deleted upon exiting the Tor Browser
-  *A number of mitigations are in place as protection against malicious input vulnerabilities*:  X-XSS-PROTECTION is enabled and Content-Security-Policy is set to self; SQLAlchemy is used as ORM for all database queries; and application does not execute uploaded submission data
-  *A number of mitigations are in place as protection against access control vulnerabilities*: Apache autoindex module is disabled; cache control header is set to “no store;” Journalist/Admin passphrases are long and automatically generated; passphrases are stored in a database hashed with a unique salt; account generation/revocation/reset is restricted to Admin role; two-factor authentication is required through a TOTP token or a Yubikey
-  *A number of mitigations are in place as protection against the risk of an HTTP misconfiguration*: Only HTTP GET, POST and HEAD are allowed; HTTP headers do not expose version information of system components; X-Content-Type is set to "nosniff;" Content-Security-Policy is set to "self;" and X-XSS-Protection is set to "1"

Countermeasures on the *Source Interface*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  All source submissions are encrypted with GPG at rest using the airgapped submission key
-  Sensitive source and submission data is sent through HTTP POST
-  *Source Interface* runs on an end-to-end encrypted Tor onion service, and TLS is opt-in with an EV cert
-  *Source Interface* sessions are invalidated after a user logs out or inactivity over 120 minutes. Session control includes CSRF token in Flask Framework.
-  All *Source Interface* session data (except language and locale selection) is discarded at logout, and fully deleted upon exiting the Tor Browser
-  *A number of mitigations are in place as protection against malicious input vulnerabilities*: X-XSS-PROTECTION is enabled and Content-Security-Policy is set to self; SQLAlchemy is used as ORM for all database queries; and Application does not execute uploaded data
-  *A number of mitigations are in place as protection against the risk of an HTTP misconfiguration*: Only HTTP GET, POST and HEAD are allowed; HTTP headers do not expose version information of system components; X-Content-Type is set to "nosniff;" Content-Security-Policy is set to "self;" and X-XSS-Protection is set to "1"
-  *A number of mitigations are in place as protection against access control vulnerabilities*: Cache control header is set to “no store;” Source codenames are long and automatically generated, and stored in a database hashed with a unique salt; Source codename reset functionality is not available; Source login does not display information about prior submissions; Souce login requires 7-word codename to check Source Interface for replies

Countermeasures on the SecureDrop Repository/Release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Code and releases signed with airgapped signing key
-  Protection is placed on master and develop branch on GitHub
-  For SecureDrop Developers, 2-factor authentication is mandated on GitHub
-  Community trust is built through 3 trusted code owners and code reviews

Attacks and Countermeasures on the *Application Server* and *Monitor Server*
--------------------------------------------------------------------------

Attacks on the *Application Server* and *Monitor Server*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  *Application Server* or *Monitor Server* configuration error
-  *Journalist Interface* or *Source Interface* is framed
-  *Application Server* or *Monitor Server* is compromised
-  Attacker exploits postfix

Countermeasures on the *Application Server*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  All SecureDrop infrastructure is provisioned via infrastructure-as-code (Ansible scripts)
-  SecureDrop *Source* and *Journalist Interfaces* uses X-Frame-Options: DENY header. 
-  Browser Same Origin Policy should prevent the SecureDrop page from trivial modifications, but more complex attacks are mitigated via the X-Frame-Options: DENY HTTP header
-  *Journalist Interface* uses ATHS cookie

Countermeasures on the *Monitor Server*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  All SecureDrop infrastructure is provisioned via infrastructure-as-code (Ansible scripts). 
-  *Monitor Server* should only expose SSH via Tor hidden service. All other traffic should be blocked by firewall
-  FPF performs vulnerability management for software dependencies as well automatic nightly updates for dependencies and OS packages
-  grsecurity/PaX linux patches prevent the exploitation of certain memory-corruption attacks
-  AppArmor profiles further reduce process capabilities through Mandatory Access Control
-  OSSEC is used for intrusion detection/file integrity monitoring

Attacks and Countermeasures on SecureDrop Dependencies via Python, Tor, Linux Kernel, apt, Tails, Ubuntu, or Hardware Firewall Vulnerabilities
----------------------------------------------------------------------------------------------------------------------------------------------

Attacks on SecureDrop Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Known vulnerabilities in Python or libraries used by SecureDrop
-  Known vulnerabilities in Tor (incl. Onion Service cryptography, authentication)
-  Malicious apt package installed at install-time or during updates
-  Known weakness in hidden service cryptography
-  Github is compromised
-  Firewall is not up-to-date
-  Known vulnerabilities in the Linux kernel or packages used by app/mon servers
-  Tails ISO malicious
-  Ubuntu ISO malicious
-  Tor apt repo compromised
-  Ubuntu apt Repo compromised
-  Tor Browser exploit
-  Vulnerabilities/Compromise of Hardware Firewall

Countermeasures Against Vulnerabilities in Python or Libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  FPF performs vulnerability management for all Python packages used by SecureDrop. 
-  CI will run safety check to ensure dependencies do not have a CVE associated with the version (https://github.com/freedomofpress/securedrop/commit/e9c13ff3d09dfc446bc28da4347f627b5533b150)

Countermeasures Against Vulnerabilities in Tor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  A cron job ensures that automatic nightly security updates are applied for OS packages, including Tor. 
-  Grsecurity/PaX linux patches prevent the exploitation of certain memory-corruption attacks. 
-  AppArmor profiles further reduce process capabilities through Mandatory Access Control
-  Hidden Service authentication is used as a complementary authentication and only used for defense-in-depth/attack surface reduction

Countermeasures Against Vulnerabilities in Linux Kernel or Packages Used By *Servers*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  A cron job ensures that automatic nightly security updates are applied for OS packages. Grsecurity/PaX linux patches prevent the exploitation of certain memory-corruption attacks.  AppArmor profiles further reduce process capabilities through Mandatory Access Control. 
-  OSSEC is used for intrusion detection/file integrity monitoring. OSSEC alerts are sent to Admins via end-to-end encrypted email.

Countermeasures Against Malicious apt Installs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  apt does GPG signature verification of all packages as long as it's not explicitly disabled

Countermeasures Against Malicious Tails or Ubuntu ISOs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-   SecureDrop dmin guide (https://docs.securedrop.org/en/stable/admin.html) instructs Users/Admins to validate checksum/signatures of downloaded images
-  Countermeasures Against Vulnerabilities in the Hardware Firewall
-  SecureDrop admin guide (https://docs.securedrop.org/en/stable/admin.html) informs administrators to update the hardware firewall and provides a very restrictive policy for accessing the administrative interface (blocked on app and mon ports of the firewall). 
-  Alert emails are sent out to admins when there are critical pfSense vulnerabilities.
-  *Application* and *Monitor Servers* use IPTables as host-based firewall for defense-in-depth
-  All application traffic is over Tor Hidden services (end-to-end encrypted) and all software packages are signed. Only DNS and NTP are transmitted over HTTP (unauthenticated and in cleartext)

Attacks and Countermeasures on Network Infrastructure via FPF Infrastructure or Organization Corporate Network
--------------------------------------------------------------------------------------------------------------

Attacks on Network Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Landing page source control is compromised
-  Landing page host is compromised
-  Landing page DNS leaks from SecureDrop/leaks-related subdomain
-  Communications vulnerability in *Source Interface* or *Journalist Interface*
-  DNS requests to news organizations subdomain for SecureDrop landing page, Freedom.press, torproject.org Tor activity, SD submissions may be correlated
-  SecureDrop.org compromised
-  User web traffic to SecureDrop landing page uses CDN and may be logged
-  Tor network exploit
-  APT server man-in-the-middle used to serve old or malicious packages
-  SecureDrop APT servers are compromised or APT server man-in-the middle attack with malicious packages.
-  News Organization network is compromised
-  Landing page is unavailable
-  OSSEC and/or Journalist alert SMTP account credentials compromised
-  OSSEC and/or Journalist alert private key compromised
-  SMTP relay compromised
-  Admin's network being monitored
-  Landing page is framed
-  Landing page source control/host compromised

Countermeasures in FPF Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Builds are independently validated by multiple developers
-  Release files containing hashes (MD5, SHA1, SHA256, SHA512) of Package file and package hashes are signed with an airgapped GPG key
-  Developer key list is published and GPG-signed with the directory key
-  Valid-until is set for packages served by FPF APT repository
-  SecureDrop updates are packaged in a .deb file and served through FPF's apt repo
-  Source code is validated/verified before packaging and signing the .deb

Countermeasures in News Organization Corporate Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  SecureDrop environment should be strictly segregated from corporate environment
-  Most SecureDrop traffic goes over Tor and as such is encrypted end-to-end
-  Alert emails to Journalists and Admins are GPG-encrypted (but not signed) to provide confidentiality and prevent tampering
-  OSSEC alerts are scrubbed for sensitive contents (application data, server IPs)
-  Documented deployment best practices provide instructions to strengthen Landing Page security and privacy

Attacks and Countermeasures on User Behavior or Hardware via SecureDrop Hardware Tampering or Failure in Operational Security
---------------------------------------------------------------------------------------------------------------

Attacks on User Behavior or Hardware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Journalist corporate workstation seized/tampered/compromised
-  Transfer device seized/stolen/lost
-  Admin workstation backup stick is compromised
-  Admin two-factor authentication device is lost or compromised
-  Admin SSH Key is compromised
-  SecureDrop installer misconfigures server/firewall hardware
-  Source uses tor2web or employer/corporate device
-  Source shares that they are using SecureDrop/leaking documents
-  Journalist/Admin gets phished from a submission or otherwise breaks the SVS airgap with malware

Countermeasures in User Behavior Recommendations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Source guide (https://docs.securedrop.org/en/stable/source.html) gives instructructions on best practices for the entire submission workflow
-  Source interface banner suggests that user disables JS (high security settings in Tor Browser)
-  Journalist guide (https://docs.securedrop.org/en/stable/journalist.html) informs users of malware risks, the importance of strict comparmentalization of SecureDrop-related activities
-  Securedrop deployment guide gives best practices for proper administration of the SecureDrop system, and its public-facing properties like the *Landing Page* (https://docs.securedrop.org/en/stable/deployment_practices.html)
-  Admin guide (https://docs.securedrop.org/en/stable/admin.html) gives instructions for long-term maintenance of the technical properties of the SecureDrop system, as well as operations to support Journalists
-  All Admin tasks are completed over Tor/Tor authenticated hidden services after installation. Any Journalist/Admin password/2FA token resets can only be done by an Admin with password-protected SSH capability or authenticated hidden service credentials.
-  Persistent storage on the Admin Workstation is protected with LUKs/dm-crypt encryption

Implications of SecureDrop Area Compromise
------------------------------------------ 

What a Compromise of the *Application Server* Can Surrender
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The server sees the plaintext codename, used as the login identifier,
   of every source.
-  The server sees all HTTP requests made by the source, the admin, and
   the journalist.
-  The server sees the plaintext submissions of every source.
-  The server sees the plaintext communication between journalists and
   their sources.
-  The server stores the Tor Hidden Service private key for the source interface.
-  The server stores the Tor Hidden Service private key and ATHS token for the
   Journalist interface.
-  The server stores and (optional) TLS private key and certificate (if HTTPS
   is enabled on the source interface)
-  The server stores hashes of codenames, created with scrypt and
   randomly-generated salts.
-  The server stores journalist password hashes, created with scrupt and
   randomly-generated salts, as well as TOTP seeds.
-  The server stores only encrypted submissions and communication on
   disk.
-  The server stores a GPG key for each source, with the source's
   codename as the passphrase.
-  The server may `store plaintext submissions in memory for at most 24
   hours <https://github.com/freedomofpress/securedrop/pull/805>`__.
-  The server stores sanitized Tor logs, created using the `SafeLogging
   option <https://www.torproject.org/docs/tor-manual.html.en>`__, for
   the *Source Interface*, the *Journalist Interface*, and SSH.
-  The server stores both access and error logs for the Journalist
   Interface.
-  The server stores connection history and audit logs for the admin.
-  The server can connect to the *Monitor Server* using an SSH key and a
   passphrase.

What a Comprommise of the *Monitor Server* Can Surrender
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The server stores the plaintext alerts on disk, data may also reside
   in RAM.
-  The server stores the GPG public key the OSSEC alerts are encrypted
   to.
-  The server stores plaintext credentials for the SMTP relay used to
   send OSSEC alerts.
-  The server stores the email address the encrypted OSSEC alerts are
   sent to.
-  The server stores sanitized Tor logs, created using the `SafeLogging
   option <https://www.torproject.org/docs/tor-manual.html.en>`__, for
   SSH.
-  The server stores connection history and audit logs for the admin.
-  The server stores OSSEC and Procmail logs on disk.
-  The server can connect to the *Application Server* using an SSH key and
   a passphrase.

What a Compromise of the Workstations Can Surrender
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The *Admin Workstation* requires Tails with a persistent volume,
   which stores information such as GPG and SSH keys, as well as a
   :doc:`database with passphrases <../passphrases>`
   for the *Application Server*, the *Monitor Server*, and the GPG key the
   *Monitor Server* will encrypt OSSEC alerts to.
-  The *Journalist Workstation* requires Tails with a persistent
   volume, which stores information such as the Hidden Service value
   required to connect to the *Journalist Interface*, as well as a :doc:`database
   with passphrases <../passphrases>` for the
   *Journalist Interface* and the journalist's personal GPG key.
-  The *Secure Viewing Station* requires Tails with a persistent
   volume, which stores information such as the SecureDrop application's
   GPG key, as well as a :doc:`database with the
   passphrase <../passphrases>` for that key.

What a Compromise of the Source's Property Can Surrender
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Use of `the Tor Browser will leave
   traces <https://research.torproject.org/techreports/tbb-forensic-analysis-2013-06-28.pdf>`__
   that can be discovered through a forensic analysis of the source's
   property following either a compromise or physical seizure. Unless
   the compromise or seizure happens while the source is submitting
   documents to SecureDrop, the traces will not include information
   about sites visited or actions performed in the browser.
-  Use of Tails with a persistent volume will leave traces on the device
   the operating system was installed on. Unless the compromise or
   seizure happens while the source is submitting documents to
   SecureDrop, or using the persistent volume, the traces will not
   include information about sites visited or actions performed in the
   browser or on the system.
-  SecureDrop 0.3 encourages sources to protect their codenames by
   memorizing them. If a source cannot memorize the codename right away,
   we recommend writing it down and keeping it in a safe place at first,
   and gradually working to memorize it over time. Once the source has
   memorized it, they should destroy the written copy. If the
   source does write down the codename, a compromise or physical seizure
   of the source's property may result in the attacker obtaining the
   source's codename.
-  An attacker with access to the **source's codename** can:

   -  Show that the source has visited the SecureDrop site, but not
      necessarily submitted anything.
   -  Upload new documents or submit messages.
   -  Communicate with the journalist as that source.
   -  See any replies from journalists that the source has not yet
      deleted.

What a Physical Seizure of the Source's Property Can Surrender
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Document use of Tor or Tails, but not necessarily research into
   SecureDrop
-  Prevent the source from submitting documents by taking the device the
   documents are stored on.
-  If the property is seized while powered on, the attacker can also
   analyze any plaintext information that resides in RAM.
-  Tamper with the hardware.
-  A physical seizure of, and access to, the source's codename will
   allow the attacker to access the Source Interface as that source.

-  A physical seizure of the admin's property will allow the attacker
   to:

   -  Prevent the admin from working on SecureDrop for some period of
      time.
   -  Access any stored, decrypted documents taken off the Secure
      Viewing Station.
   -  If the property is seized while powered on, the attacker can also
      analyze any plaintext information that resides in RAM.

-  A physical seizure of, and access to, the admin's Tails persistent
   volume, password database, and two-factor authentication device will
   allow the attacker to access both servers and the *Journalist Interface*.

What Compromise of the Admin's Property Can Surrender
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  To access the *Journalist Interface*, the *Application Server*, or the
   *Monitor Server*, the attacker needs to obtain the admin's login
   credentials and the admin's two-factor authentication device. Unless
   the attacker has physical access to the servers, the attacker will
   also need to obtain the Hidden Service values for the Interface and
   the servers. This information is stored in a password-protected
   database in a persistent volume on the admin's Tails device. The
   volume is protected by a passphrase. If the admin's two-factor
   authentication device is a mobile phone, this will also be protected
   by a passphrase.
-  An attacker with access to the **admin's computer** can:

   -  Access any stored, decrypted documents taken off the Secure
      Viewing Station.

-  An attacker with access to the **persistent volume** on the admin's
   Tails device can:

   -  Add, modify, and delete files on the volume.
   -  Access the Hidden Service values used by the Interfaces and the
      servers.
   -  Access SSH keys and passphrases for the *Application Server* and the
      *Monitor Server*.
   -  Access the GPG key and passphrase for the encrypted OSSEC email
      alerts.
   -  Access the credentials for the account the encrypt alerts are sent
      to.
   -  Access the admin's personal GPG key.

-  An attacker with admin access to the *Journalist Interface* can:

   -  Add, modify, and delete journalist users.
   -  Change the codenames associated with sources within the Interface.
   -  Download, but not decrypt, submissions.
   -  Communicate with sources.
   -  Delete one or more submissions.
   -  Delete one or more sources, which destroys all communication with
      that source and prevents the source from ever logging back in with
      that codename.

-  An attacker with admin access to the *Application Server* can:

   -  Add, modify, and delete software, configurations, and other files.
   -  See all HTTP requests made by the source, the admin, and the
      journalist.
   -  See the plaintext codename of a source as they are logging in.
   -  See the plaintext communication between a source and a journalist
      as it happens.
   -  See the stored list of hashed codenames.
   -  Access the GPG public key used to encrypt communications between a
      journalist and a source.
   -  Download stored, encrypted submissions and replies from the
      journalists.
   -  Decrypt replies from the journalists if the source's codename, and
      thus the passphrase, is known.
   -  Analyze any plaintext information that resides in RAM, which may
      include plaintext of submissions made within the past 24 hours.
   -  Review logs stored on the system.
   -  Access the *Monitor Server*.

-  An attacker with admin access to the *Monitor Server* can:

   -  Add, modify, and delete software, configurations, and other files.
   -  Change the SMTP relay, email address, and GPG key used for OSSEC
      alerts.
   -  Analyze any plaintext information that resides in RAM.
   -  Review logs stored on the system.
   -  Trigger arbitrary commands to be executed by the OSSEC agent user,
      which, assuming the attacker is able to escalate privileges, may
      affect the *Application Server*.

What a Physical Seizure of the Admin's Property Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Tamper with the hardware.
-  Prevent the admin from working on SecureDrop for some period of time.
-  Access any stored, decrypted documents taken off the Secure Viewing
   Station.
-  If the property is seized while powered on, the attacker can also
   analyze any plaintext information that resides in RAM.
-  A physical seizure of, and access to, the admin's Tails persistent
   volume, password database, and two-factor authentication device will
   allow the attacker to access both servers and the *Journalist Interface*.

What a Compromise of the Journalist's Property Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  To access the *Journalist Interface*, the attacker needs to obtain the
   journalist's login credentials and the journalist's two-factor
   authentication device or seed. Unless the attacker has physical access to the
   server, the attacker will also need to obtain the Hidden Service
   value for the Interface. This information is stored in a
   password-protected database in a persistent volume on the
   journalist's Tails device. The volume is protected by a passphrase.
   If the journalist's two-factor authentication device is a mobile
   phone, this will also be protected by a passphrase.
-  An attacker with access to the **journalist's computer** can:

   -  Access any stored, decrypted documents taken off the Secure
      Viewing Station.

-  An attacker with access to the **persistent volume** on the
   journalist's Tails device can:

   -  Add, modify, and delete files on the volume.
   -  Access the Hidden Service values used by the *Journalist Interface*.
   -  Access SSH keys and passphrases for the *Application Server* and the
      *Monitor Server*.
   -  Access the journalist's personal GPG key.

-  An attacker with journalist access to the *Journalist Interface* can:

   -  Change the codenames associated with sources within the interface.
   -  Download, but not decrypt, submissions.
   -  Delete one or more submissions.
   -  Communicate with sources.
   -  If the journalist has admin privileges on SecureDrop, they can create new
      journalist accounts.

What a Physical Seizure of the Journalist's Property Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Tamper with the hardware.
-  Prevent the journalist from working on SecureDrop for some period of
   time.
-  Access any stored, decrypted documents taken off the Secure Viewing
   Station.
-  If the property is seized while powered on, the attacker can also
   analyze any plaintext information that resides in RAM.
-  A physical seizure of, and access to, the journalist's Tails
   persistent volume, password database, and two-factor authentication
   device will allow the attacker to access the *Journalist Interface*.

What a Compromise of the *Application Server* Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  If the *Application Server* is compromised, the system user the
   attacker has control over defines what kind of information the
   attacker will be able to view and what kind of actions the attacker
   can perform.
-  An attacker with access to the **debian-tor** user can:

   -  View, modify, and delete all files owned by this user. This
      includes sanitized Tor logs, created using the `SafeLogging
      option <https://www.torproject.org/docs/tor-manual.html.en>`__,
      for SSH, the *Source Interface* and the *Journalist Interface*.
   -  View, modify, and delete the Tor configuration file, root is
      required to reload the config.

-  An attacker with access to the **ossec** user can:

   -  Add, view, modify, and delete the log files, and in doing so send
      inaccurate information to the *Monitor Server* and the admin.

-  An attacker with access to the **www-data** user can:

   -  View, modify, and delete all files owned by this user. This
      includes all files in use by the SecureDrop application, such as
      text, code, the database containing encrypted submissions and
      communications. The attacker needs root access to reload
      configuration files.
   -  View, modify, and delete both access and error logs for the
      *Journalist Interface*.
   -  View any HTTP requests made by the source, the admin, and the
      journalist in that moment. This includes seeing plaintext
      codenames, submissions, and communications.
   -  Add and delete communications between a journalist and a source by
      writing to the database.

-  An attacker with access to the **root** user can:

   -  Do anything the **www-data** user can do in terms of the
      SecureDrop application, this user is in full control of the server
      and can view, modify, and delete anything at will. This user is
      not able to decrypt submissions or communications, unless the
      attacker has access to the encryption key required to do so.

What a Physical Seizure of the *Application Server* Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  If the *Application Server* is seized, the attacker will be able to
   view any and all unencrypted files on the server. An attacker will be able
   to modify any and all files on the server. This includes all
   files in use by the SecureDrop Application. If the server is seized
   while it is powered on, the attacker can also analyze any plaintext
   information that resides in RAM. The attacker can also tamper with
   the hardware.

What a Compromise of the *Monitor Server* Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  If the *Monitor Server* is compromised, the system user the attacker
   has control over defines what kind of information the attacker will
   be able to view and what kind of actions the attacker can perform.
-  An attacker with access to the **debian-tor** user can:

   -  View, modify, and delete all files owned by this user. This
      includes sanitized Tor logs, created using the `SafeLogging
      option <https://www.torproject.org/docs/tor-manual.html.en>`__,
      for SSH.
   -  View, modify, and delete the Tor configuration file, root is
      required to reload the config.

-  An attacker with access to the **ossec** user can:

   -  View all ossec logs and alerts on disk.
   -  Modify the ossec configuration.
   -  Send (or suppress) emails to administrators and journalists.

-  An attacker with access to the **root** user can:

   -  Do anything the **ossec** user can do in terms of the SecureDrop
      application, this user is in full control of the server and can
      view, modify, and delete anything at will. This user is not able
      to decrypt encrypted email alerts, unless the attacker has access
      to the encryption key required to do so.

What a Physical Seizure of the *Monitor Server* Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  If the *Monitor Server* is seized, the attacker will be able to view
   any and all unencrypted files on the server. This includes all files
   in use by OSSEC. If the server is seized while it is powered on, the
   attacker can also analyze any plaintext information that resides in
   RAM. The attacker can also tamper with the hardware.
-  If the *Monitor Server* is no longer online or tampered with, this will
   have an effect on the quantity and accuracy of notifications sent to
   admins or journalists.

What a Compromise of the *Secure Viewing Station* Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The *Secure Viewing Station* is only useful to an attacker while
   powered on and with the Tails persistent volume mounted. The attacker
   may learn more if the Transfer device is in use at the time of
   compromise or seizure. A physical seizure of this machine, the Tails
   device or the Transfer device will also achieve nothing, assuming
   that Tails' implementation of full-disk encryption works as expected.
-  A compromise of the *Secure Viewing Station* allows the attacker to:

   -  Run commands as the **amnesia** user.
   -  View, modify, and delete files owned by the **amnesia** user. This
      includes the GPG private key used to encrypt and decrypt submitted
      documents.
   -  View, modify, and delete encrypted--and possibly also decrypted
      submissions--if the Transfer device is in use.
   -  Export the SecureDrop submissions GPG private key (unless there is a
      passphrase set).

What a Physical Seizure of the *Secure Viewing Station* Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The *Secure Viewing Station* is only useful to an attacker while
   powered on and with the Tails persistent volume mounted. The attacker
   may learn more if the Transfer device is in use at the time of
   compromise or seizure. A physical seizure of this machine, the Tails
   device or the Transfer device will also achieve nothing, assuming
   that Tails' implementation of full-disk encryption works as expected.
-  A physical seizure of the *Secure Viewing Station*, while on and with
   the persistent volume decrypted and mounted, allows the attacker to:

   -  Tamper with the hardware.
   -  Run commands as the **amnesia** user.
   -  View, modify, and delete the GPG private key used to encrypt and
      decrypt submitted documents.
   -  View, modify, and delete encrypted--and possibly also decrypted
      submissions--if the Transfer device is in use.

What a Local Network Attacker Can Achieve Against the Source, Admin, or Journalist:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  A local network can observe when they are using Tor.
-  A local network can block Tor and prevent them from accessing
   SecureDrop.
-  A local network may be able to deduce use of SecureDrop by looking at
   request sizes, plaintext uploads and encrypted downloads, although
   `research suggests this is very
   difficult <https://blog.torproject.org/blog/critique-website-traffic-fingerprinting-attacks>`__.

What a Global Adversary Can Achieve Against the Source, Admin, or Journalist:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  A global adversary capable of observing all Internet traffic may have
   more luck than the local network attacker in deducing use of
   SecureDrop by looking at request sizes, plaintext uploads and
   encrypted downloads.
-  A global adversary may be able to link a source to a specific
   SecureDrop server.
-  A global adversary may be able to link a source to a specific
   journalist.
-  A global adversary may be able to correlate data points during a leak
   investigation, including looking at who has read up on SecureDrop and
   who has used Tor.
-  A global adversary may be able to forge an SSL certificate and use it
   to spoof an organization's HTTPS *Landing Page*, thereby tricking the
   source into visiting a fake SecureDrop site.

What a Random Person on the Internet Can Achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  A random person can attempt to DoS the SecureDrop server and
   overwhelm the journalists by generating a high number of codenames
   and uploading many large documents.
-  A random person can submit empty, forged, or inaccurate documents.
-  A random person can submit malicious documents, e.g. malware that
   will attempt to compromise the *Secure Viewing Station*.
-  A random person can attempt to get sensitive information from a
   SecureDrop user's browser session, such as the source's codename.
-  A random person can attempt to compromise the SecureDrop server by
   attacking the exposed attack surface, including the kernel network
   stack, Tor, Apache, the SecureDrop web interfaces, Python, OpenSSH,
   and the TLS implementation.
