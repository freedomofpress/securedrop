#!/bin/bash
# Handler script to encrypt OSSEC alerts prior to mailing.
# Called via the `.procmailrc` for user `ossec`.

# Intentionally NOT setting `set -e`, since we'll do our own error handling.
# Rather than exit immediately on errors, we should gracefully inform
# the Admin that there was a problem encrypting a message.
#set -e
set -o pipefail


# Read alert message content from STDIN, as passed by OSSEC. Store the message
# in a var so we can iteratively process it, halting execution before sending
# if the GPG encryption command failed. If we simply chain a bunch of pipes
# together, then the email will be sent with an empty body, should the GPG
# encryption fail.
ossec_alert_text="$(< /dev/stdin)"

# Primary "send email to Admin" functionality.
function send_encrypted_alert() {

    local encrypted_alert_text
    # Try to encrypt the alert message. We'll inspect the exit status of the
    # pipeline to decide whether to send the alert text, or the default
    # failure message.
    encrypted_alert_text="$(printf "%s" "${ossec_alert_text}" | \
        /usr/bin/formail -I '' | \
        /usr/bin/gpg --homedir /var/ossec/.gnupg --trust-model always -ear '{{ ossec_gpg_fpr }}')"

    # Error handling.
    if [[ -z "${encrypted_alert_text}" || $? -ne 0 ]]; then
        send_plaintext_fail_message
    else
        echo "${encrypted_alert_text}" | \
            /usr/bin/mail -s "$(echo "${SUBJECT}" | sed -r 's/([0-9]{1,3}\.){3}[0-9]{1,3}\s?//g' )" '{{ ossec_alert_email }}'
    fi
}

# Failover alerting function, in case the primary function failed.
# Usually a failure is related to GPG balking on the encryption step;
# that may be due to a missing pubkey or something reason.
function send_plaintext_fail_message() {
    printf "Failed to encrypt OSSEC alert. Investigate the mailing configuration on the Monitor Server." | \
        /usr/bin/formail -I "" | \
        /usr/bin/mail -s "$(echo "${SUBJECT}" | sed -r 's/([0-9]{1,3}\.){3}[0-9]{1,3}\s?//g' )" '{{ ossec_alert_email }}'
}

# Encrypt the OSSEC notification and pass to mailer for sending.
send_encrypted_alert
