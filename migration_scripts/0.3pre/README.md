# 0.3pre => 0.3 Migration

This migration script is intended for use with installed preview releases for 0.3 ( ee1b94d7). This script will upgrade the releases to the tagged 0.3 release.

The following steps are involved in upgrading a 0.3pre installation, and will need to be done on both servers:

1. Copy `0.3pre_upgrade.py` to both the App and Monitor servers.
2. On the app server, run `sudo ./0.3pre_upgrade.py app`.
3. On the monitor server, run `sudo ./0.3pre_upgrade.py mon`.
4. Verify that the upgrade has been successful.
5. If you encounter an error using the migration script, please [file an issue](https://github.com/freedomofpress/securedrop/issues/new). Your system is backed up (to a `.tar.gz` file stored in the same directory as the upgrade script) before running the upgrade, although restoring from that backup is not automated at the moment.

## Details

This is the high-level overview of what the migration script does.

1. Remove the old packages, because 0.3 has a different package
   layout. Removing the packages should *not* delete any of the
   instances' configuration.
2. Make any required changes to the existing data.
   1. Migrate database
2. Update the signing key and remove the old signing key
3. Install the new packages

