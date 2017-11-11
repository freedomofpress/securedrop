Threat Model
============

This document outlines the threat model for SecureDrop 0.3 and is
inspired by a `document Adam Langley wrote for Pond
<https://web.archive.org/web/20150326154506/https://pond.imperialviolet.org/threat.html>`__.
The threat model is defined in terms of what each possible adversary
can achieve. This document is still a work in progress. If you have
questions or comments, please open an issue on GitHub or send an email
to securedrop@freedom.press.

Assumptions
-----------

Assumptions about the source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The source acts reasonably and in good faith, e.g. if the user were
   to give their codename or private key material to the attacker that
   would be unreasonable.
-  The source would like to remain anonymous, even against a forensic
   attacker.
-  The source obtains an authentic copy of Tails or the Tor Browser.
-  The source follows our :doc:`guidelines <../source>`
   for using SecureDrop.
-  The source is accessing an authentic SecureDrop site.

Assumptions about the admin and the journalist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The admin and the journalist act reasonably and in good faith, e.g.
   if either of them were to give their credentials or private key
   material to the attacker that would be unreasonable.
-  The admin and the journalist obtain authentic copies of Tails.
-  The journalist follows our
   :doc:`guidelines <../journalist>` for using SecureDrop
   and working with submitted documents.

Assumptions about the person installing SecureDrop, usually the admin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The person acts reasonably and in good faith, e.g. if they were
   to give the attacker system-level access that would be unreasonable.
-  The person obtains an authentic copy of SecureDrop and its
   dependencies.
-  The person follows our guidelines for
   :ref:`deploying the system <deployment>`, setting
   up the :ref:`landing page <Landing Page>` for the
   organization, and for :doc:`installing SecureDrop <../install>`.

Assumptions about the source's computer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The computer correctly executes Tails or the Tor Browser.
-  The computer is not compromised by malware.

Assumptions about the *Admin Workstation* and the Journalist Workstation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The computer correctly executes Tails.
-  The computer and the Tails device are not compromised by malware.
-  The two-factor authentication device used with the workstation are
   not compromised by malware.

Assumptions about the *Secure Viewing Station*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The computer is airgapped.
-  The computer correctly executes Tails.
-  The computer and the Tails device are not compromised by malware.

Assumptions about the SecureDrop hardware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The servers correctly execute Ubuntu, SecureDrop and its
   dependencies.
-  The servers, network firewall, and physical media are not compromised
   by malware.

Assumptions about the organization hosting SecureDrop
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

Assumptions about the world
~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The security assumptions of RSA (4096-bit GPG and SSH keys) are
   valid.
-  The security assumptions of scrypt with randomly-generated salts are
   valid.
-  The security/anonymity assumptions of Tor and the Hidden Service
   protocol are valid.
-  The security assumptions of the Tails operating system are valid.

Attack Scenarios
----------------

What the *Application Server* can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The server sees the plaintext codename, used as the login identifier,
   of every source.
-  The server sees all HTTP requests made by the source, the admin, and
   the journalist.
-  The server sees the plaintext submissions of every source.
-  The server sees the plaintext communication between journalists and
   their sources.
-  The server stores hashes of codenames, created with scrypt and
   randomly-generated salts.
-  The server stores only encrypted submissions and communication on
   disk.
-  The server stores a GPG key for each source, with the source's
   codename as the passphrase.
-  The server may `store plaintext submissions in memory for at most 24
   hours <https://github.com/freedomofpress/securedrop/pull/805>`__.
-  The server stores sanitized Tor logs, created using the `SafeLogging
   option <https://www.torproject.org/docs/tor-manual.html.en>`__, for
   the Source Interface, the Journalist Interface, and SSH.
-  The server stores both access and error logs for the Journalist
   Interface.
-  The server stores connection history and audit logs for the admin.
-  The server can connect to the *Monitor Server* using an SSH key and a
   passphrase.

What the *Monitor Server* can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

What the Workstations can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  The *Admin Workstation* requires Tails with a persistent volume,
   which stores information such as GPG and SSH keys, as well as a
   :doc:`database with passphrases <../passphrases>`
   for the *Application Server*, the *Monitor Server*, and the GPG key the
   *Monitor Server* will encrypt OSSEC alerts to.
-  The **Journalist Workstation** requires Tails with a persistent
   volume, which stores information such as the Hidden Service value
   required to connect to the Journalist Interface, as well as a :doc:`database
   with passphrases <../passphrases>` for the
   Journalist Interface and the journalist's personal GPG key.
-  The *Secure Viewing Station* requires Tails with a persistent
   volume, which stores information such as the SecureDrop application's
   GPG key, as well as a :doc:`database with the
   passphrase <../passphrases>` for that key.

What a compromise of the source's property can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

What a physical seizure of the source's property can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
   allow the attacker to access both servers and the Journalist Interface.

What a compromise of the admin's property can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  To access the Journalist Interface, the *Application Server*, or the
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

-  An attacker with admin access to the **Journalist Interface** can:

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

What a physical seizure of the admin's property can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Tamper with the hardware.
-  Prevent the admin from working on SecureDrop for some period of time.
-  Access any stored, decrypted documents taken off the Secure Viewing
   Station.
-  If the property is seized while powered on, the attacker can also
   analyze any plaintext information that resides in RAM.
-  A physical seizure of, and access to, the admin's Tails persistent
   volume, password database, and two-factor authentication device will
   allow the attacker to access both servers and the Journalist Interface.

What a compromise of the journalist's property can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  To access the Journalist Interface, the attacker needs to obtain the
   journalist's login credentials and the journalist's two-factor
   authentication device. Unless the attacker has physical access to the
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
   -  Access the Hidden Service values used by the Journalist Interface.
   -  Access SSH keys and passphrases for the *Application Server* and the
      *Monitor Server*.
   -  Access the journalist's personal GPG key.

-  An attacker with journalist access to the **Journalist Interface** can:

   -  Change the codenames associated with sources within the Interface.
   -  Download, but not decrypt, submissions.
   -  Delete one or more submissions.
   -  Communicate with sources.

What a physical seizure of the journalist's property can achieve
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
   device will allow the attacker to access the Journalist Interface.

What a compromise of the *Application Server* can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  If the *Application Server* is compromised, the system user the
   attacker has control over defines what kind of information the
   attacker will be able to view and what kind of actions the attacker
   can perform.
-  An attacker with access to the **debian-tor** user can:

   -  View, modify, and delete all files owned by this user. This
      includes sanitized Tor logs, created using the `SafeLogging
      option <https://www.torproject.org/docs/tor-manual.html.en>`__,
      for SSH, the Source Interface and the Journalist Interface.
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
      Journalist Interface.
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

What a physical seizure of the *Application Server* can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  If the *Application Server* is seized, the attacker will be able to
   view any and all unencrypted files on the server. This includes all
   files in use by the SecureDrop Application. If the server is seized
   while it is powered on, the attacker can also analyze any plaintext
   information that resides in RAM. The attacker can also tamper with
   the hardware.

What a compromise of the *Monitor Server* can achieve
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

   -  ???

-  An attacker with access to the **root** user can:

   -  Do anything the **ossec** user can do in terms of the SecureDrop
      application, this user is in full control of the server and can
      view, modify, and delete anything at will. This user is not able
      to decrypt encrypted email alerts, unless the attacker has access
      to the encryption key required to do so.

What a physical seizure of the *Monitor Server* can achieve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  If the *Monitor Server* is seized, the attacker will be able to view
   any and all unencrypted files on the server. This includes all files
   in use by OSSEC. If the server is seized while it is powered on, the
   attacker can also analyze any plaintext information that resides in
   RAM. The attacker can also tamper with the hardware.

What a compromise of the *Secure Viewing Station* can achieve
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

What a physical seizure of the *Secure Viewing Station* can achieve
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

What a local network attacker can achieve against the source, admin, or journalist:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  A local network can observe when they are using Tor.
-  A local network can block Tor and prevent them from accessing
   SecureDrop.
-  A local network may be able to deduce use of SecureDrop by looking at
   request sizes, plaintext uploads and encrypted downloads, although
   `research suggests this is very
   difficult <https://blog.torproject.org/blog/critique-website-traffic-fingerprinting-attacks>`__.

What a global adversary can achieve against the source, admin, or journalist:
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
   to spoof an organization's HTTPS landing page, thereby tricking the
   source into visiting a fake SecureDrop site.

What a random person on the Internet can achieve
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
