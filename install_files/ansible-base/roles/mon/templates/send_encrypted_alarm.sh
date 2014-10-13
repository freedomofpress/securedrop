#!/bin/bash

/usr/bin/formail -I "" | /usr/bin/gpg --homedir /var/ossec/.gnupg --trust-model always -ear "{{ ossec_gpg_fpr }}" | /usr/bin/mail -s "\$SUBJECT" {{ ossec_alert_email }}

