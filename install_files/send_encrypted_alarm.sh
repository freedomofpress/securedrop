#!/bin/bash

/usr/bin/formail -I "" | /usr/bin/gpg --homedir /var/ossec/.gnupg --trust-model always -ear "EMAIL_DISTRO" | /usr/bin/mail -s "$SUBJECT" EMAIL_DISTRO
