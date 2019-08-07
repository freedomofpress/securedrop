Attacks and Countermeasures on the SecureDrop Environment
=========================================================

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

Application Code — SecureDrop Repository/Release
------------------------------------------------

Attacks to the Application Code — SecureDrop Respository/Release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Malicious code introduced in SecureDrop repository
-  Malicious code introduced in SecureDrop release
-  Failure to encrypt submissions as they are written to disk

Countermeasures on the Application Code — SecureDrop Repository/Release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Code (git tags) and releases (packages uploaded to apt) are signed with the airgapped signing key
-  Protection is placed on master and develop branch on GitHub
-  For SecureDrop Developers, 2-factor authentication is mandated on GitHub
-  Community trust is built through 3 trusted code owners and code reviews

Application Code — *Source Interface* and *Journalist Interface*
----------------------------------------------------------------

Attacks to the Application Code — *Source Interface* and *Journalist Interface*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Configuration vulnerability in *Source* or *Journalist Interface*
-  Lack of segmentation between *Source* and *Journalist Interface*
-  Session management vulnerability in *Source* or *Journalist Interface*
-  Malicious input vulnerability in *Source* or *Journalist Interface*
-  Configuration  vulnerability in *Source* or *Journalist Interface*
-  Authentication vulnerability in *Source* or *Journalist Interface*
-  Access control vulnerability in *Source* or *Journalist Interface*
-  Data protection vulnerability in *Source* or *Journalist Interface*
-  Communications vulnerability in *Source* or *Journalist Interface*
-  Error handling and logging vulnerability in *Source* or *Journalist Interface*
-  HTTP security configuration vulnerability in *Source* or *Journalist Interface*
-  File and resource vulnerability in *Source* or *Journalist Interface*
-  Business logic vulnerability in *Source* or *Journalist Interface*
-  Web services vulnerability in *Source* or *Journalist Interface*

Countermeasures on both *Source* and *Journalist Interfaces*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  *Interfaces* run on an end-to-end encrypted Tor Onion Service
-  Sensitive source and submission data is sent through HTTP POST
-  All source submissions are encrypted with GPG at rest using the airgapped *Submission Key*
-  *Interface* sessions are invalidated after a user logs out or inactivity over 120 minutes
-  Session control on *Interface* includes CSRF token in Flask Framework
-  All *Interface* session data (except language and locale selection) is discarded at logout, and fully deleted upon exiting the Tor Browser
-  A number of mitigations are in place as protection against malicious input vulnerabilities on the Source and Journalist Interfaces:

    - X-XSS-PROTECTION is enabled
    - Content-Security-Policy is set to self
    - SQLAlchemy is used as ORM for all database queries
    - Application does not execute uploaded submission data
-  A number of mitigations are in place as protection against the risk of an HTTP misconfiguration on the *Source* and *Journalist Interfaces*:

    - Cache control header is set to “no store;”
    - HTTP headers do not expose version information of system components
    - X-Content-Type is set to "nosniff;"
    - Content-Security-Policy is set to "self;"
    - X-XSS-Protection is set to "1"

Countermeasures unique to *Source Interface*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  TLS on *Source Interface* is opt-in with an EV cert
-  Only HTTP GET, POST and HEAD methods are allowed
-  A number of mitigations are in place as protection against access control vulnerabilities on the *Source Interface*:

    - Source codenames are long and automatically generated
    - Hashed codenames are stored in a database hashed with a unique salt
    - Source codename reset functionality is not available
    - Source login does not display information about prior submissions
    - Source login requires 7-word codename to check *Source Interface* for replies

Countermeasures unique to *Journalist Interface*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  *Journalist Interface* is located behind an authenticated Onion Service and only privileged users have required authorization token
-  Only HTTP GET, POST, HEAD and DELETE methods are allowed
-  A number of mitigations are in place as protection against access control vulnerabilities on the *Journalist Interface*:

    - Apache autoindex module is disabled
    - Journalist/Admin passphrases are long and automatically generated
    - Passphrases are stored in a database hashed with a unique salt
    - Account generation/revocation/reset is restricted to Admin role
    - Two-factor authentication is required through a TOTP token or a Yubikey

*Application Server* and *Monitor Server*
-----------------------------------------

Attacks on the *Application Server* and *Monitor Server*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  *Application* or *Monitor Server* configuration error
-  *Source* or *Journalist Interface* is framed
-  *Application* or *Monitor Server* is compromised
-  Attacker exploits postfix
-  Known vulnerabilities in the Linux kernel or packages used by app/mon servers

Countermeasures on Both *Application* and *Monitor Servers*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Grsecurity/PaX linux patches prevent the exploitation of certain memory-corruption attacks
-  AppArmor profiles further reduce process capabilities through Mandatory Access Control
-  All SecureDrop infrastructure is provisioned via infrastructure-as-code (Ansible scripts)
-  A cron job ensures that automatic nightly security updates are applied for OS packages
-  *Journalist Interface* uses ATHS cookie
-  *Monitor Server* should only expose SSH via Tor Onion Service. All other traffic should be blocked by firewall

Countermeasures Unique to *Application Server*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  SecureDrop *Source* and *Journalist Interfaces* uses X-Frame-Options: DENY header
-  Browser Same Origin Policy should prevent the SecureDrop page from trivial modifications, but more complex attacks are mitigated via the X-Frame-Options: DENY HTTP header

Countermeasures Unique to *Monitor Server*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  OSSEC is used for intrusion detection/file integrity monitoring, and are sent to Admins via end-to-end encrypted email

SecureDrop Dependencies — Python, Tor, Linux Kernel, apt, Tails, Ubuntu, or Hardware Firewall Vulnerabilities
-------------------------------------------------------------------------------------------------------------

Attacks on SecureDrop Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Known vulnerabilities in Python or libraries used by SecureDrop
-  Known vulnerabilities in Tor (incl. Onion Service cryptography, authentication)
-  Malicious apt package installed at install-time or during updates
-  Known weakness in Onion Service cryptography
-  Github is compromised
-  Firewall is not up-to-date
-  Tails ISO malicious
-  Ubuntu ISO malicious
-  Tor apt repo compromised
-  Ubuntu apt repo compromised
-  Tor Browser exploit
-  Vulnerabilities/Compromise of Hardware Firewall

Countermeasures Against Vulnerabilities in Python or Libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  FPF performs vulnerability management for all Python packages used by SecureDrop
-  CI will run safety check to ensure dependencies do not have a CVE associated with the `version <https://github.com/freedomofpress/securedrop/commit/e9c13ff3d09dfc446bc28da4347f627b5533b150>`__

Countermeasures Against Vulnerabilities in Tor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  A cron job ensures that automatic nightly security updates are applied for OS packages, including Tor
-  Grsecurity/PaX linux patches prevent the exploitation of certain memory-corruption attacks
-  AppArmor profiles further reduce process capabilities through Mandatory Access Control
-  Hidden Service authentication is used as a complementary authentication and only used for defense-in-depth/attack surface reduction

Countermeasures Against Malicious apt Installs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  apt does GPG signature verification of all packages as long as it's not explicitly disabled

Countermeasures Against Malicious Tails or Ubuntu ISOs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-   SecureDrop `Admin Guide <https://docs.securedrop.org/en/stable/admin.html>`__ instructs Users/Admins to validate checksum/signatures of downloaded images

Countermeasures Against Vulnerabilities in the Hardware Firewall
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  SecureDrop `Admin Guide <https://docs.securedrop.org/en/stable/admin.html>`__ informs administrators to update the hardware firewall and provides a very restrictive policy for accessing the administrative interface (blocked on app and mon ports of the firewall).
-  Alert emails are sent out to admins when there are critical pfSense vulnerabilities.
-  *Application* and *Monitor Servers* use IPTables as host-based firewall for defense-in-depth
-  All application traffic is over Tor Hidden services (end-to-end encrypted) and all software packages are signed. Only DNS and NTP are transmitted over HTTP (unauthenticated and in cleartext)

Network Infrastructure — FPF Infrastructure or Organization Corporate Network
-----------------------------------------------------------------------------

Attacks on Network Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Landing Page source control is compromised
-  Landing Page host is compromised
-  Landing Page is framed or unavailable
-  Landing Page DNS leaks from SecureDrop/leaks-related subdomain
-  Communications vulnerability in *Source* or *Journalist Interface*
-  DNS requests to news organization's subdomain for SecureDrop Landing Page, Freedom.press, torproject.org Tor activity, SD submissions may be correlated
-  SecureDrop.org is compromised
-  User web traffic to SecureDrop Landing Page uses CDN and may be logged
-  Tor network exploit
-  apt server man-in-the-middle used to serve old or malicious packages
-  SecureDrop apt servers are compromised, or apt server man-in-the middle attack injects malicious packages
-  News Organization network is compromised
-  OSSEC and/or Journalist alert SMTP account credentials compromised
-  OSSEC and/or Journalist alert private key compromised
-  SMTP relay compromised
-  Admin's network is monitored

Countermeasures in FPF Infrastructure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  Builds are independently validated by multiple developers
-  Release files containing hashes (MD5, SHA1, SHA256, SHA512) of package file and package hashes are signed with an airgapped GPG key
-  Developer key list is published and GPG-signed with the directory key
-  SecureDrop updates are packaged in a .deb file and served through FPF's apt repo
-  Source code is validated/verified before packaging and signing the .deb

Countermeasures in News Organization Corporate Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-  SecureDrop environment should be strictly segregated from corporate environment
-  Most SecureDrop application traffic goes over Tor and as such is encrypted end-to-end
-  Alert emails to Journalists and Admins are GPG-encrypted (but not signed) to provide confidentiality
-  OSSEC alerts are scrubbed for sensitive contents (application data, server IPs)
-  Documented deployment best practices provide instructions to strengthen Landing Page security and privacy

User Behavior and Hardware — SecureDrop Hardware Tampering or Failure in Operational Security
---------------------------------------------------------------------------------------------

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
-  `Source Guide <https://docs.securedrop.org/en/stable/source.html>`__ gives instructructions on best practices for the entire submission workflow
-  Source interface banner suggests that user disables JS (high security settings in Tor Browser)
-  `Journalist Guide <https://docs.securedrop.org/en/stable/journalist.html>`__ informs users of malware risks, the importance of strict comparmentalization of SecureDrop-related activities
-  `SecureDrop Deployment Guide <https://docs.securedrop.org/en/stable/deployment_practices.html>`__ gives best practices for proper administration of the SecureDrop system, and its public-facing properties like the Landing Page
-  `Admin Guide <https://docs.securedrop.org/en/stable/admin.html>`__ gives instructions for long-term maintenance of the technical properties of the SecureDrop system, as well as operations to support Journalists
-  All Admin tasks are completed over Tor/Tor authenticated Onion Services after installation
-  Any Journalist/Admin password/2FA token resets can only be done by an Admin with password-protected SSH capability or authenticated Onion Service credentials.
-  Persistent storage on the Admin Workstation is protected with LUKS/dm-crypt encryption
