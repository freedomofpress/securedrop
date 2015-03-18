#!/bin/bash

/usr/bin/formail -I "" | /usr/bin/gpg --homedir /var/ossec/.gnupg --trust-model always -ear "{{ ossec_gpg_fpr }}" | /usr/bin/mail -s "$(echo $SUBJECT | sed 's/{{ app_ip }}//g' )" {{ ossec_alert_email }}
