# Changelog

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
* Install app server, monitor server, Python dependencies, and custom configuration via deb packages
* UI refresh on source and journalist interfaces
* New UX for journalists:
  * "quick filter" box for codenames
  * "download unread" link
  * star sources
  * multi-select actions for sources (delete, star, unstar) and submissions (download, delete)
  * more detailed source listings
* Normalize submission timestamps to that of the most recent submission
to minimize metadata that could be used for correlation
* Handle journalist authentication in the Document Interface instead of relying entirely on Authenticated Tor Hidden Services.
* Document Interface supports two-factor authentication via Google Authenticator or Yubikey
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
