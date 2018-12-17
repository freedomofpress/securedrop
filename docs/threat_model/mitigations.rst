Mitgations
==========
This sections covers the mitigations and countermeasures in place in SecureDrop

SecureDrop Server Area
----------------------

Preventing exploitation of SecureDrop Dependency Vulnerability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Threats include:

* Known or vulnerabilities in Python, libraries, packages or kernel used by the SecureDrop server.

Mitgations in place:

* Minimal amount of dependencies are used
* Unattended daily security upgrades via cron-apt
* Nightly reboots after the daily patching
* Grsec-hardened kernel to protect against exploitation of memory corruption vulnerabilities
* AppArmor to further restrict filesystem access to processes
* OSSEC to alert suspicious activity and GPG-encrypted email


Vulnerabilities in SecureDrop application or infrastrucutre code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Threats include:

* Web server configuration error
* Web application vulnerability, including:
 * session management
 * malicious input
 * file and resource vulnerability
 * information disclosure
 * error handling and logging
 * encryption
 * business logic
* Malicious code introduced in SecureDrop code repository or release.
* Journalist or source interfaced are framed by a malicious third-party interface is framed
* Web services vulnerability in Source interface

Mitigations in place:

 * Source and Journalist interface are simple web applications
 * Ansible is use for automated and repeatable system configuration
 * Flask framework is used for Source and Journalist Interfaces:
    * Templating and auto-escaping for forms
    * CSRF token on all source  forms
    * SQLAlchemy as ORM to prevent SQL injection
 * Journalist Interface specific authentication:
    * 2FA for journalist logins
    * ATHS token to access Journalist Interface
 * Files are streamed to disk encrypted and then encrypted with a 4096-bit RSA key
 * Airgaped signing key to sign git tag and apt server Release file
 * Server hardening:
  * SSH:
   * Exposed only over Tor (with ATHS) or local network only
   * Public-key authentication only
   * OSSEC for alerting on SSH brute force attempts
  * Webserver (Apache)
   * X-Frame options DENY, X-XSS-protection and Content Content Security Policy
   * Allow only GET, POST, HEAD HTTP methods
   * Support for HTTPS on souce interface (requires EV certificate)

 * Hardware firewall to prevent network-level attacks to the hosts
 * Tor Onion Service for authentication and encryption in transit for Source and Journalist Interfaces and SSH
 * HTTPS optional for an extra layer of in-transit encryption
