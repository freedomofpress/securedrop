#!/bin/bash

/usr/bin/formail -I "" | /usr/bin/gpg --homedir /var/ossec/.gnupg --trust-model always -ear "{{ ossec_gpg_fpr }}" | /usr/bin/mail -s "$(echo $SUBJECT | sed -r 's/([0-9]{1,3}\.){3}[0-9]{1,3}\s?//g' )" {{ ossec_alert_email }}
