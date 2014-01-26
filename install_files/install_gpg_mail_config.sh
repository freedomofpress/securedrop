#!/bin/bash
# ------------------------------------------------------------------------------
#
# Script used to setup gpg enrypted emails for ossec alerts
# Limitations:
#  - GPG key is passed to the send_encrypted_alarm.sh script, relies on CONFIG_OPTIONS 
#     EMAIL_DISTRO. So when encrypting we can only pass in 1 key that is tied to a email
#
# TODO:
#  - Support for multiple gpg public keys
# ------------------------------------------------------------------------------
set -u -e
set -x 
# Setup Vars
OSSEC_HOME=${OSSEC_HOME:="/var/ossec"}
OSSEC_KEY_HOME=$OSSEC_HOME/.gnupg
EMAIL_DISTRO=${EMAIL_DISTRO:=securedroptestmail@gmail.com}
OSSEC_KEY_LIST=${OSSEC_KEY_LIST=:="SecureDrop.asc"}
SERVER_HOSTNAME=$(hostname)
source ../CONFIG_OPTIONS

#set up basic functions
print_error() {
  echo $*
  exit 15
}

catch_error() {
  if [ $1 -ne "0" ]; then
    print_error "ERROR encountered $2"
  fi
}

# Setup postfix & procmail
install_mail_software() {
  debconf-set-selections <<< "postfix postfix/mailname string $(hostname -f)"
  debconf-set-selections <<< "postfix postfix/main_mailer_type string 'Internet Site'"
  apt-get install -y procmail postfix
}

setup_postfix() {
  sed -e "s/SMTP_SERVER_HERE/$SMTP_SERVER/g" -e "s/HOSTNAME_HERE/${SERVER_HOSTNAME}/g" monitor.postfix-main.cf > /etc/postfix/main.cf
  service postfix restart

  grep -q "root: ossec" /etc/aliases || echo "root: ossec" >> /etc/aliases
  postalias /etc/aliases
}

# Import gpg of ossec email alert recipients
setup_gpg_for_ossec() {
  mkdir -p $OSSEC_KEY_HOME
  
  for KEY in $OSSEC_KEY_LIST ; do
      if [ ! -f $KEY ]; then
        print_error "Cannot find $KEY"
      else
        gpg --homedir /var/ossec/.gnupg --import $OSSEC_KEY_LIST
      fi
  done
  
  chown -R ossec:root $OSSEC_KEY_HOME
  chmod 700 $OSSEC_KEY_HOME
  chmod 600 $OSSEC_KEY_HOME/*
}

# Setup Procmail
setup_procmail() {
  # Setup procmailrc
  cp monitor.procmailrc $OSSEC_HOME/.procmailrc

  # Setup mail encryption script
  sed -e "s/EMAIL_DISTRO/$EMAIL_DISTRO/g" send_encrypted_alarm.sh  > /var/ossec/send_encrypted_alarm.sh
  chmod 755 /var/ossec/send_encrypted_alarm.sh
  chown ossec:root /var/ossec/send_encrypted_alarm.sh

  # Setup logs so we can create correct permissions
  touch /var/log/procmail.log
  chmod 600 /var/log/procmail.log
  chown ossec:root /var/log/procmail.log

}

main() {
  install_mail_software
  setup_postfix
  setup_gpg_for_ossec
  setup_procmail
}

main
