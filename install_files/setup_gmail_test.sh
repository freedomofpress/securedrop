#!/bin/bash

set -u -e
# ------------------------------------------------------------------------------
#
# This script is used to setup postfix on the monitor server to use
# gmail as the smtp server to validate gpg and ossec alerts are sent
# 
# This script should be run after the production install scripts
#
# TODO: 
#   - Support default test gmail account securedroptestemail@gmail.com  
# 
# ------------------------------------------------------------------------------
#set -x

echo ""
echo "In order to test sending ossec emails via gpg we need to do the following:"
echo ""
echo "1. Setup postfix to use google as the smpt relay"
echo "2. Import your public gpg key to the ossec user"
echo ""
echo "What Gmail email address do you want to send test alerts to?"
read EMAIL_DISTRO
echo "What is your email password. (Needed to auth google as smtp server)"
read PASSWORD
echo "Please import your public key into the ossec keystore"
echo "gpg --homedir /var/ossec/.gnu --import <your key here>"

# Install required testing tools
apt-get install -y postfix mailutils libsasl2-2 ca-certificates libsasl2-modules

# Setup postfix config
sed -ie "/^relayhost/d" /etc/postfix/main.cf
cat <<EOF >> /etc/postfix/main.cf
relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_CAfile = /etc/postfix/cacert.pem
smtp_use_tls = yes
EOF



# Setup gmail user auth for postfix
echo "[smtp.gmail.com]:587    ${EMAIL_DISTRO}:${PASSWORD}" > /etc/postfix/sasl_passwd
chmod 400 /etc/postfix/sasl_passwd
postmap /etc/postfix/sasl_passwd

# Import Thawte CA cert into postfix 
cat /etc/ssl/certs/Thawte_Premium_Server_CA.pem >> /etc/postfix/cacert.pem

# Reload postfix config
service postfix reload

sed -e "s/EMAIL_DISTRO/$EMAIL_DISTRO/g" send_encrypted_alarm.sh  > /var/ossec/send_encrypted_alarm.sh

# Send test email
echo "Test mail from postfix" | mail -s "Test Postfix" $EMAIL_DISTRO
