# Changelog

## 0.5.2

* Replace PyCrypto (#2903).
* Use `max_fail_percentage` to force immediate Ansible exits in playbook runs (#2922).
* Bugfix: Dynamically allocate firewall during OSSEC registration (#2748).
* Bugfix: Add all languages to sdconfig prompt (#2935).

The issues for this release were tracked in the 0.5.2 milestone on Github:
https://github.com/freedomofpress/securedrop/milestone/41

## 0.5.1

### Web Applications

* Add Arabic, Chinese, Turkish and Italian translations (#2830).
* Enable administrators to update the SecureDrop logo via the Admin Interface (#2769).
* Enable administrators to send test OSSEC alerts via the Admin Interface (#2771).
* Improve the language menu (#2733).
* Disable .map file generation when compiling CSS files from SASS (#2814).
* User logout on password reset (#2756).
* Update pip requirements (#2811).

### Operations

* Use apt mirror for Tor packages (#2441).
* Push grsecurity tasks to the beginning of the install process (#2741).
* Remove flaky SMTP/SASL host validation during SecureDrop configuration (#2815).
* Automate post-Ubuntu install checks verifying DNS, NTP is working (#2129).
* Validate GnuPG key is not a private key prior to install (#2735).
* Remove HMAC-SHA1 from SSH config (#2730).

### Monitoring

* Prevent OSSEC from sending daily emails on startup (#2701).

### Documentation

* Replace Google Authenticator with FreeOTP (#2757).
* Add recommended landing page content (#2752).

The issues for this release were tracked in the 0.5.1 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.5.1.

## 0.5

### Web Applications

* Internationalize both web applications (#2470, #2392, #2400, #2374, #2626,
  #2354, #2338, #2333, #2229, #2223).
* Localize in Dutch, French, German, Norwegian, Portuguese and Spanish.
* Add language picker to web applications (#2557).
* Refactor both web applications using Flask Blueprints (#2294).
* Add default 120 minute session timeout on both interfaces (#880, #2503).
* Only show source codename on first session (#2327).
* Invert `login_required` decorator on journalist interface so that logins
  are required by default (#2460).
* Require entry of old password before changing password (#2304).
* Use whitespace control on Jinja templates (#2413).
* Add reset icon to reset password button (#2423).
* Improve form validation on new user creation in journalist interface (#2500).
* Improve form validation on login form on source interface (#2376).
* Resolve confusing use of first/third person on user creation (#2323).
* Show which journalist is logged in on the journalist interface (#2293).
* Create friendly session expiry page (#2290).
* Improve UX to get to individual source page on journalist interface (#2130).
* Improve UX on login forms by making fields longer (#2288).
* Bugfix: Fix input validation on Yubikey for 2FA HOTP (#2311).
* Bugfix: Remove extra level in folders in submission downloads (#2262).

### Operations

* Allow apache/apparmor file exception for proving onion ownership to a CA (#2602)
* Enable admins to set supported locales via SecureDrop admin script (#2516)
* Update AppArmor rules for Apache (#2507).
* Reduce number of pip requirements files (#2175).

### Monitoring

* Add `/boot` to integrity checking (#2496).
* Bugfix: Remove OSSEC syscheck monitoring of temporary files produced by bulk
  download (#2606).

### Tails Environment

* Bugfix: Use host for SASL and SMTP domain validation (#2591).
* Bugfix: Add trusted metadata to SecureDrop .desktop files (#2586).

### Developer Workflow

* Add updated Data Flow Diagrams (#2370).
* Add safety check for Python dependencies in CI (#2451).
* Remove noisy GnuPG debug output on test failure (#2595).
* Convert tests in SubmissionNotInMemoryTest to pytest (#2548).
* Document virtualized Admin Workstation setup (#2204, #2607).
* Bugfix: Remove extra `rqworker` start in unit tests (#2613).
* Bugfix: Resolve test failures in VirtualBox (#2396).

### Documentation

* Add sample SecureDrop privacy policy to documentation (#2340).
* Break out "Deployment Best Practices" into discrete docs section (#2339).

The issues for this release were tracked in the 0.5 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.5.

## 0.4.4

Bugfix release. Fixes configuration management logic to ensure all packages
are properly validated prior to installation.

* Remove force=yes in package install tasks in Ansible config.
* Upgrade Ansible to 2.3.2 to address CVE-2017-7481.
* Add securedrop-admin `logs` command for collecting log files.
* Increases expiration date on SecureDrop Release Signing Key to October 2018.

Since this is a bugfix release, the changes on the 0.4.4 milestone
are not included here. Those issues have been postponed to a future release.

## 0.4.3

The issues for this release were tracked in the 0.4.3 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.4.3.

### Web Applications

* Automatically generate diceware passphrases for SecureDrop journalists and administrators (#980).
* Add minimum length check for journalist usernames (#1682).
* Resolve inconsistently named source IDs (#1998).
* Fix transient test errors (#2122, #2214, #2205).
* Progress towards internationalizing SecureDrop: Add utilities for extracting strings for translation and for compiling translations (#2120), add DEFAULT_LOCATE to config.py (#2197).
* Make source interface index responsive (#2235).
* Remove safe filter from jinja templates (#2227).

### Operations

* Retry SMTP relay and SASL domain verification tasks in validate role (#2099).
* Disable Postfix in the staging environment (#1164).
* Refactor Debian package build logic (#2160).
* Reboot staging servers on first provision (#1704).
* Bugfix: Whitelist fontawesome-webfont.svg in AppArmor (#2075).

### Tails Environment

* Bugfix: Use .xsessionrc in SVS to prevent unpacking of office files (#2188).

### Monitoring

* Remove OSSEC alert for Tor Guard overloaded log event (#1670).
* Remove OSSEC alert when journalists bulk delete submissions (#1691).
* Remove OSSEC alert for OSSEC keepalive event (#2138).
* Add "Ansible playbook run on server" OSSEC rule (#2224).
* Update locations of logs on app server for OSSEC syscheck (#2153).
* Adds regression testing for OSSEC false positives (#2137).

### Developer Workflow

* Adds flake8 linting (#886).
* Add code style guide for contributors (#47).
* Produce screenshots before and after Selenium tests for debugging (#2086).
* Add HTML linting (#2081).
* Add Makefile targets for linters (#1920).
* Adds "page layout" automated tests that take screenshots of the source and journalist interface in each language (#2141).
* Expose documentation on port 8000 on development machine (#2170).
* Make Makefile self-documenting (#2169).
* Add pre-commit hook for developers (#2234).
* CI: Do not run staging CI if only documentation has changed (#2132).
* CI: Use new Trusty image for Travis CI (#1876).

### Documentation

* Adds guide and glossary for translators (#2039, #2162).
* Adds i18n guide for developers (#2118).
* Adds note in Tails upgrade documentation about missing "Root Terminal" launcher in workstation backup procedure (#2065).
* Update AppArmor developer documentation (#2077).
* Adds pre-installation checklist (#2139).
* Specify NTP server to use in install documentation (#2094).
* Adds new tested printer for use in SecureDrop airgap (#2117).
* Add documentation for multiple administrators managing config (#2096).
* Update KeePassX (#2158).
* Add documentation for using gksu nautilus in lieu of "Root Terminal" in Tails 3 backup process (#2069).
* Update hardware requirements (#2207).

## 0.4.2

* Explicitly enables DAC override capability in Apache AppArmor profile (#2105)

The issues for this release were tracked in the 0.4.2 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.4.2.

## 0.4.1

* Fixes a bug in one of the Tails scripts used to set up the Desktop
icons for the SecureDrop interfaces (#2049)

The issues for this release were tracked in the 0.4.1 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.4.1.

## 0.4

The issues for this release were tracked in the 0.4 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.4.

This changelog shows major changes below. Please diff the tags to see the full list of changes. 

### Deployment

* Enable optional HTTPS on the source interface (#1605).
* Standardize SecureDrop server installation on a single username (#1796). 
* Add `securedrop-admin` script and update version of Ansible running in the workstation (#1146, #1885).
* Add validation of user-provided values during SecureDrop installation (#1663, #749, #1257).
* Removes `prod-specific.yml` configuration file (#1758).
* Allow an administrator to set a custom daily reboot time (#1515).
* Renames "document interface" to "journalist interface" (#1384, #1614).
* Adds "Email from" option to OSSEC (#894, #1220).
* Updated template for Firewall and adds instructions on how to use it (#1122, #1648)
* Bugfix: Re-enable logging on journalist interface (#1606).

### Developer Workflow

* Reconciles divergent master and develop branches (#1559).
* Increases unit test coverage to from 65% to 92%. 
* Adds testinfra system configuration test suite (#1580). 
* Removes unnecessary test wrappers (#1412).
* Major improvements to SecureDrop CI and testing flow including adding the staging environment to CI (#1067). 

### Web App: Source

* Mask codename on source interface (#525).
* Replace confusing text on source interface landing bar (#1713).
* Refresh of source UI (#1536, #1895, #1604).
* Add metadata endpoint to source webapp for monitoring (#972).
* Begin using EFF wordlist (#1361).

### Web App: Journalist

* Feature: Add unread submission icon and select all unread button to submission view (#1353).
* Refresh of journalist UI (#1604).
* Adds minimum password length requirements for new journalist accounts (#980).
* Delete submissions that have had their sources deleted (#1188).
* Bugfix: Empty replies can no longer be sent to a source (#1715).
* Bugfix: Handle non hexadecimal digits for the 2FA secret (#1869). 
* Bugfix: Handle token reuse for the 2FA secret on /admin/2fa (#1687).
* Bugfix: Handle attempts to make duplicate user accounts (#1693). 
* Bugfix: Fix confusing UI on message/reply icons (#1258). 

### Tails Environment

* Improve folder structure for SecureDrop documents (#383).
* Bugfix: Update provided KeePassX template to kdbx format (#1831).
* Bugfix: Ensure the filename is restored when uncompressing an archive (#1862).

### Documentation

* Adds "What makes SecureDrop unique?" guide (#469).
* Adds passphrase best practices guide (#1136).
* Adds SecureDrop promotion guide (#1134).
* Adds Administrator responsibilities guide (#1727).
* Other minor miscelleanous documentation improvements.

## 0.3.12

* Disables swap on Application Server via preinst script on
`securedrop-app-code` package hook. Swap was not previously disabled
permanently, so this automatic update will deactivate it, shred the swap
partition if it was in use, then disable swap entries in /etc/fstab.
A separate change in future release will enforce this configuration
via the Ansible config at install time (#1620)

## 0.3.11

* Instructs source to turn the Tor Browser security slider to High and to
get a new Tor Browser identity after logout. Turning the security slider to
high would disable the SVG icons so the icons and CSS on the source interface
are updated to display properly using this setting (#1567, #1480, #1522)
* Adds `/logout` route and button to base template (#1165)
* Removes the choice of number of codename words from the source interface
(#1521)
* Adds SourceClear integration (#1520)
* CSS fixes (#1186)
* Adds coveragerc

The issues for this release were tracked in the 0.3.11 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.3.11.

## 0.3.10

Creates new Debian package `securedrop-keyring` for managing the SecureDrop
Release Signing Key. Rotates the signing key currently in use by setting
a dependency on the other Debian packages, so that currently running deployments
will have their apt keyrings updated via automatic nightly updates.

* Installs securedrop-keyring package for managing apt signing key (#1416)

Admins must manually update the Release Signing Key on Admin Workstations.
See documentation on configuring the Admin Workstation.

The issues for this release were tracked in the 0.3.10 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.3.10.

## 0.3.9

Point release to fix some minor issues and update our Python dependencies.

* Fix Unicode support regression and implement better Unicode tests (#1370)
* Add OSSEC rule to ignore futile port scanning (#1374)
* Update Apache AppArmor profile to allow access to webfonts and to execute uname (#1332, #1373)
* Update Python dependencies of SD (#1379)
* Fix a regression in the new install script (#1397)

The issues for this release were tracked in the 0.3.9 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.3.9.

## 0.3.8

* Re-include the pycrypto Python module to address the regression in 0.3.7 (#1344)
* Switch to using bento boxes in Vagrantfile for more reproducible test environments
* Minor fixes to update_version.sh

The issues for this release were tracked in the 0.3.8 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.3.8

## 0.3.7

Point release to address some requests from SecureDrop administrators and
upgrade various components on the SecureDrop architecture.

* Improve backup and restore roles
* Ensure SecureDrop-specific Tails configuration works on Tails 2.x
* Document upgrading from Tails 1.x to Tails 2.x for current admins using 1.x
* Upgrade SecureDrop's Python dependencies

The issues for the release were tracked with the [0.3.7 milestone on
GitHub](https://github.com/freedomofpress/securedrop/milestones/0.3.7).

## 0.3.6

This is an emergency release to update the copy of the FPF code signing public
key in the repo because it expired on Oct 26. This fix is required for new
installs to succeed; otherwise, the installation will fail because apt's
package authentication fails if the corresponding key is expired.

## 0.3.5

The issues for this release were tracked with the 0.3.5 milestone on Github: https://github.com/freedomofpress/securedrop/milestones/0.3.5

* Use certificate verification instead of fingerprint verification by default for the OSSEC Postfix configuration (#1076)
* Fix apache2 service failing to start on Digital Ocean (#1078)
* Allow Apache to rotate its logs (#1074)
* Prevent reboots during cron-apt upgrade (#1071)
* Update documentation (#1107, #1112, #1113)
* Blacklist additional kernel modules used for wireless networking (#1116)

## 0.3.4

The issues for this release were tracked with the 0.3.4 milestone on Github: https://github.com/freedomofpress/securedrop/milestones/0.3.4

This release contains fixes for issues described in the most recent security audit by iSec. It also contains some improvements and updates to the documentation, and a fix for Tor hidden service directory permissions that caused new installs to fail.

### iSec audit fixes

* Fix ineffective SSH connection throttling (iSEC-15FTC-7, #1053)
* Remove debugging print statements that could leak sensitive information to the logs for the document interface (iSEC-15FTC-2, #1059)
* Harden default iptables policies (iSEC-15FTC-3, #1053)
* Don't check passwords or codenames that exceed a maximum length to prevent DoS via excessive scrypt computation (iSEC-15FTC-6, #1059)
* Remove unnecessary capabilties from the Apache AppArmor profile (iSEC-15FTC-9, #1058).
* Change postfix hostname to something generic to prevent fingerprinting via OSSEC email headers (iSEC-15FTC-10, #1057)

### Other changes

* Ensure correct permissions for Tor hidden service directories so new installs won't break (#1052)
* Clarify server setup steps in the install documentation (#1027, #1061)
* Clarify that Tor ATHS setup is now automatic and does not require manual changes (#1030)
* Explain that you can only download files to the "Tor Browser" folder on Tails as of Tails 1.3, due to the addition of AppArmor confinement for the Tor Browser (#1036, #1062).
* Explain that you must use the Unsafe Browser to configure the network firewall because the Tor Browser will be blocked from accessing LAN addresses starting in Tails 1.5 (#1050)
* Fix "gotcha" in network firewall configuration where pfSense guesses the wrong CIDR subnet (#1060)
* Update the upgrade docs to refer to the latest version of the 0.3.x release series instead of a specific version that would need to be updated every time (#1063)

## 0.3.3

The issues for this release were tracked with the 0.3.3 milestone on Github:
https://github.com/freedomofpress/securedrop/milestones/0.3.3.

* Remove unnecessary proxy command from Tails SSH aliases (#933)
* Make grsec reboot idempotent to avoid unnecessary reboots on new installs (#939)
* Make tmux the default shell on App and Monitor servers (#943)
* Fully tested migration procedures for 0.2.1 and 0.3pre to 0.3 (#944, #993)
* Ensure grub is not uninstalled in virtual machines (#945)
* CSS fixes (#948)
* Apache AppArmor profile should support TLS/SSL (#949)
* Fix: document interface no longer flas new submissions as unread (#969)
* Switch to NetworkManager for automatic ATHS setup on Admin Workstation (#1018)
* Upgrade Selenium in testing dependencies so functional tests work (#991)
* Clarify paths in install documentation (#1009)

## 0.3.2

* Fixes security vulnerabilty (severity=high) in access control on Document Interface (#974)

## 0.3.1

* Improved installation and setup documentation (#927, #907, #903, #900)
* Fixed PEP8 and other style issue (#926, #893, #884, #890, #885)
* Automatic torrc initialization in Tails via dotfiles persistence (#925)
* Fix bug in installing grsecurity kernel when using new Ubuntu 14.04.2 .iso (#919)
* Prevent sources from creating "empty" submissions (#918)
* Autoremove unused packages after automatic upgrade (#916)
* Remove the App Server (private) IP address from OSSEC alert email subject lines (#915)
* Handle custom header image as a conffile in the securedrop-app-code Debian package (#911)
* Upgrade path from 0.3pre (#908, #909)
* Remove offensive words from source and journalist word lists (#891, #901)

## 0.3

### Web App

This is a high-level overview of some of the more significant changes between SecureDrop 0.2 and 0.3. For the complete set of changes, diff the tags.

* Reduce JS dependencies to JQuery (stable) only
* Add functional tests, increase unit test coverage
* Rewrite database layer (db.py) using SQLAlchemy declarative ORM
* Automate dev. setup with Vagrant and integrate with Travis CI
* Store more info in db and less on filesystem
  * "flagged" sources
  * metadata for new UI features (starring, etc.)
  * metadata for simpler/more efficient views in journalist.py
* Do not set headers in the web app (handle by production config.)
* Add 2fac auth for journalist interface
* Allow OSSEC emails to be encrypted with admin GPG key
* Install app server, monitor server, Python dependencies, and custom configuration via Debian packages
* UI refresh on source and journalist interfaces
* New UX for journalists:
  * "quick filter" box for codenames
  * "download unread" link
  * star sources
  * multi-select actions for sources (delete, star, unstar) and submissions (download, delete)
  * more detailed source listings
* Normalize submission timestamps to that of the most recent submission
to minimize metadata that could be used for correlation
* Handle journalist authentication in the Document Interface instead of relying entirely on Authenticated Tor hidden services.
* Document Interface supports two-factor authentication via Google Authenticator or YubiKey
  * These logins are hardened in a manner similar to that of the `google-authenticator` PAM module: tokens may only be used once, logins are rate limited, etc.
  * If you are using TOTP, the window is expanded from 1 period to 3 in order to help the situation where the server and client's clocks are skewed
* Add Admin Interface so privileged "admin" users may add, edit, or delete other users on the Document Interface
* Requests are automatically encrypted with an ephemeral key as they are buffered onto disk to mitigate forensic attacks
* The haveged "high water" mark has been raised to maintain a higher average level of entropy on the system and minimize the appearance of the "flag for reply" flow
* Secure removal (via `srm`) of data has been moved to an async worker to prevent hanging the interface when deleting large files or collections
* New dedicated section of Source Interface for replies, instead of using flashed messages
* Change default codename length from 8 words to 7 words, maintains a sufficient security level while hopefully improving usability for sources
* Add recommendations for storing and memorizing the codename to the codename generation page
* Improve the quality of journalist designations generated by reducing the adjectives and nouns lists to a smaller subset of common words
* Use ntpd to continuously update the server time (especially important when using TOTP for two-factor authentication)
* Move Document Interface to port 80 so we don't have to keep remembering to type ":8080"
* We no longer ASCII-armor submissions when they are encrypted. This was unnecessary and bloated the size of the submissions, which is important to avoid because downloading large submissions over Tor is very slow.
* Flask now uses X-Send-File for downloads, which fixed some reported issues are large downloads not finishing or being corrupted.

### Environment

* Add egress host firewall rules
* Add google-authenticator apache module and basic auth for access to
document interface
* Encrypt bodies of OSSEC email alerts (add postfix+procmail to monitor
server)
* Create apparmor profiles for chrooted interface Tor process
* Update interface apparmor profiles for changes to application code
* Change installation method to use Ansible playbook and deb packages
* Split securedrop repo into 3 separate repos for securedrop-specific code (the application, Python dependencies, and custom configuration) and the upstream packages that we maintain (OSSEC and the hardened grsecurity kernel for Ubuntu)
* Add variety of development and testing environments for developers and researchers to use with Vagrant
* Reduce OSSEC email alert noise through whitelisting errors that are reported by the default configuration but that we have investigated and determined to be safe to ignore
* Document a thoroughly tested network firewall configuration with pfSense
* Reboot the machine automatically every 24 hours to reduce the potential for plaintext to remain in memory
* Add KeePassX password database template and document its use for journalists and admins
* Add secure backup and recovery scripts
* Add migration scripts
* Major improvements to the installation and user documentation, including lots of detail, testing, and the addition of TOC

## 0.2.1

### Web App
* Fix for flagging errors
* Validate journalist messages
* Add logging using standard Python library.
* Add delete collection
* Replace bcrypt with scrypt
* Clear referer on external links

### Environment
* Set maximum request body size in CONFIG_OPTIONS
* Add security-related HTTP headers to Apache config
* Remove mysql database, replace w/ sqlite. Update sqlite apparmor profile.
* Add outbound iptables rule for source/document groups

## 0.2

* Various documentation improvements

### Web App
* Remove javascript dependency in source interface
* Add warning to source interface about using javascript (with Gritter)
* Update to pycrypto 2.6.1
* Validate filenames and codenames
* Remove unsafe characters from codenames, remove diceware words that are
not real words
* Rewrite source.py and journalist.py with Flask
* Add tests
* Flag sources for journalist reply to avoid DOS attack by generating
many GPG keys
* Allow journalists to delete documents with SRM
* Add bulk download to journalist interface
* Add MySQL-python and SQLAlchemy dependency, db.py to perform database
functions (ex: storing codenames)
* Remove option to have codenames with <7 words
* Use sqlite as default database
* Add support for theming
* bcrypt hash GPG passphrase for key stretching

### Environment
* Merge source and journalist servers into a single app server
* Add apparmor profiles
* Remove puppet, add base_install.sh script
* Create interface-install.sh script to set up chroot jails
* Add Ubuntu dev-setup script
* Backup Tor private keys
* Move config files into install scripts directory
* Change SOURCE_IP to APP_IP
* Set ownership and permissions for application code

## 0.1

* Renamed DeadDrop to SecureDrop
* Redesigned source and document web interface
* Wrote detailed documentation
* Improved installation process
* Wrote unit & integration tests
* Improved codename wordlist, based on Diceware
* Use bcrypt instead of SHA
* Removed VPN, replaced with authenticated Tor hidden service
* Freedom of the Press Foundation taking over project

DeadDrop was originally written by Aaron Swartz.
