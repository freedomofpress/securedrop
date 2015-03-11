# 0.2.1 => 0.3 Migration

Migrating a SecureDrop 0.2.1 installation to SecureDrop 0.3 is a two-part process.

First, SSH to the running 0.2.1 instance's app server. Copy the `0.2.1_collect.py` script to the running instance. Note that this script is standalone, and does not need the rest of the files in `migration_scripts/0.3`. Some ways of doing this include scp'ing it from the Admin Workstation, copying it with a USB stick, or git cloning the repo and using that copy.

Now run this collection script as root, and provide a file name for the archive that will store the backup. If you do not specify an extension, the appropriate one will be appended automatically:

    $ sudo ./0.2.1_collect.py backup.tar.gz

Copy `backup.tar.gz` to removable media and transfer it to the new instance's app server. If you are re-using the same hardware for your 0.3 installation as you did for 0.2.1, *make sure you copy this file to a external media before beginning the 0.3 installation* - otherwise you will lose your data!

Once you've succcessfully installed 0.3, copy `backup.tar.gz` to any location on the 0.3 app server. You will also need `0.3_migrate.py`, along with the rest of the files in `migration-scripts/0.3`. You can copy the `0.3` directory to the running instance with `scp -r`, a flash drive, or `git clone` the repo on the new app server and use that. Before you run the migration script, you need to create an admin user. Run `/var/www/securedrop/manage.py add_admin` as root, and follow the prompts to set up an admin user.  Once that's done, run `0.3_migrate.py` as root, passing the path to the backup file from the 0.2.1 machine.

    $ sudo 0.3/0.3_migrate.py backup.tar.gz

The script will say "Done!" when it completes successfully. Otherwise, it will print an error and a Python traceback. If you encounter such an error, please [file an issue](https://github.com/freedomofpress/securedrop/issues/new), including the traceback, so we can look into it.

Finally, test your new installation and make sure that everything was successfully migrated.
