#!/bin/bash
source CONFIG_OPTIONS
validate_CONFIG_OPTIONS() {
    valid_role() {
        if [ ! $ROLE="monitor" -o $ROLE="app" ]; then
            echo "Invalid role name"
            exit 0
        fi
    }

    valid_ip() {
      local IP=$1

      if [[ $IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        OIFS=$IFS
        IFS='.'
        IP=($IP)
        IFS=$OIFS
        [[ ${IP[0]} -le 255 && ${IP[1]} -le 255 && ${IP[2]} -le 255 && ${IP[3]} -le 255 ]]
      else
        echo "not a valid ip"
      fi
    }


    validate_user_exists() {
      local USERS=$1

      for USER in $USERS; do
        if ! id -u "$USER" >/dev/null 2>&1; then
          echo "Admin $USER doesn't exist"
          exit -0
        fi
      done
    }

    validate_SMTP_SERVER() {
        if [[ ! $SMTP_SERVER =~ ^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$ ]];then
            echo "Invalid SMTP_SERVER $SMTP_SERVER"
            exit 1
        fi
    }

    validate_email() {
        local EMAIL=$1

        if [[ ! $EMAIL =~ ((.+)@(.+).(.+)) ]]; then
            echo "Invalid email"
            exit 1
        fi
    }

    validate_file_exists() {
        local FILES=$1

        for FILE in $FILES; do
            if [ ! -f $FILE ]; then
                echo "File $FILE doesn't exist"
                exit 1
            fi
        done
    }


    validate_KEY() {
        if [ ! -f install_files/$KEY ]; then
            echo "Can not find key in install_files/$KEY"
            exit 1
        fi
    }

    valid_role
    valid_ip $SOURCE_IP
    valid_ip $MONITOR_IP
    validate_user_exists $SSH_USERS
    validate_SMTP_SERVER
    validate_email $EMAIL_DISTRO
    validate_email $EMAIL_FROM
    validate_user_exists $JOURNALIST_USERS
    validate_KEY
    validate_file_exists $SOURCE_SCRIPTS
    validate_file_exists $DOCUMENT_SCTIPTS
}
