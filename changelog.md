# Changelog

## 0.3

### Web App
* Reduce JS dependencies to JQuery (stable) only
* Add functional tests, increase unit test coverage
* Rewrite database layer (db.py) using SQLAlchemy declarative ORM
* Add metadata scrubbing (opt-in by source) using MAT
* Automate dev. setup with Vagrant and integrate with Travis CI
* Store more info in db and less on filesystem
  * "flagged" sources
  * metadata for new UI features (starring, etc.)
  * metadata for simpler/more efficient views in journalist.py
* Do not set headers in the web app (handle by production config.)
* Add 2fac auth for journalist interface
* Allow OSSEC emails to be encrypted with admin GPG key
* Install app server, monitor server, and hardening via deb package
* UI refresh on source and journalist interfaces
* New UX for journalists:
  * "quick filter" box for codenames
  * "download unread" link
  * star sources
  * more detailed source listings
* Normalize submission timestamps to that of the most recent submission
to minimize metadata that could be used for correlation

### Environment
* Add egress host firewall rules
* Add google-authenticator apache module and basic auth for access to
document interface
* Encrypt bodies of OSSEC email alerts (add postfix+procmail to monitor
server)
* Create apparmor profiles for chrooted interface Tor process
* Update interface apparmor profiles for changes to application code
* Change installation method to deb packages

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
* Improved code name wordlist, based on Diceware
* Use bcrypt instead of SHA
* Removed VPN, replaced with authenticated Tor hidden service
* Freedom of the Press Foundation taking over project

DeadDrop was originally written by Aaron Swartz.
