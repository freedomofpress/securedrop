#!/bin/bash

# no password prompt to install mysql-server
mysql_root=$(head -c 20 /dev/urandom | python -c 'import sys, base64; print base64.b32encode(sys.stdin.read())')
mysql_securedrop=$(head -c 20 /dev/urandom | python -c 'import sys, base64; print base64.b32encode(sys.stdin.read())')
sudo debconf-set-selections <<EOF
mysql-server-5.5 mysql-server/root_password password $mysql_root
mysql-server-5.5 mysql-server/root_password_again password $mysql_root
EOF

echo "Setting up MySQL database..."
mysql -u root -p"$mysql_root" -e "create database securedrop; GRANT ALL PRIVILEGES ON securedrop.* TO 'securedrop'@'localhost' IDENTIFIED BY '$mysql_securedrop';"

# initialize development database
# config.py will use sqlite by default, but we've set up a mysql database as
# part of this installation so it is very easy to switch to it.
# Also, MySQL-Python won't install (which breaks this script) unless mysql is installed.
sed -i "s@^# DATABASE_PASSWORD.*@# DATABASE_PASSWORD=\'$mysql_securedrop\'@" config.py
echo "Creating database tables..."
python -c 'import db; db.create_tables()'
