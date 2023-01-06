#!/bin/bash

SENT_STAMP=/var/ossec/logs/journalist_notification_sent.stamp

function send_encrypted_alarm() {
    /var/ossec/send_encrypted_alarm.sh "$1"
}

function main() {
    if modified_in_the_past_24h "${SENT_STAMP}" ; then
        logger "$0 journalist notification suppressed"
    else
        handle_notification "$@"
    fi
}

function modified_in_the_past_24h() {
    local stamp
    stamp="$1"
    #
    # 24h is 1440 minutes but we subtract 30min to avoid the following race condition
    #
    # - machine reboots
    # - notification sent
    # - machine reboots 24h later but reboots 1 minute faster than the previous day
    # - notification is sent 23h59 minutes after the last one and suppressed
    #
    local one_day
    one_day=1410
    test -f "${stamp}" && \
        find "${stamp}" -mmin "-${one_day}" | \
            grep --quiet "${stamp}"
}

function handle_notification() {
    local sender
    local stdin
    sender=${1:-send_encrypted_alarm}
    stdin="$(< /dev/stdin)"

    #
    # When .procmailrc changes, the pattern triggering this script will match
    # itself. Just return and ignore the match.
    #
    if echo "$stdin" | grep -q "Integrity checksum changed for: '/var/ossec/.procmailrc'" ; then
        echo "$0 ignore /var/ossec/.procmailrc checksum changes"
        return 0
    fi

    local count
    count=$(echo "$stdin" | perl -ne "print scalar(<>) and exit if(m|ossec: output: 'head -1 /var/lib/securedrop/submissions_today.txt|);")
    if [[ "$count" =~ ^[0-9]+$ ]] ; then
        export SUBJECT="Submissions in the past 24h"
        #
        # whitespaces below are so the size of both messages are exactly the same
        #
        if [[ "$count" -gt "0" ]] ; then
            echo "There has been submission activity in the past 24 hours.   "
            echo "You should login and check SecureDrop. "
        else
            echo "There has been no submission activity in the past 24 hours."
            echo "You do not need to login to SecureDrop."
        fi | $sender journalist
        touch "${SENT_STAMP}"
    else
        export SUBJECT="SecureDrop Submissions Error"
        (
            echo "$0 failed to find 0/1 submissions boolean in the following OSSEC alert"
            echo
            echo "$stdin"
        ) | $sender ossec
    fi
}

function forget() {
    rm -f "${1:-$SENT_STAMP}"
}

function test_modified_in_the_past_24h() {
    local stamp
    stamp=$(mktemp)

    modified_in_the_past_24h "${stamp}" || exit 1

    touch --date '-2 days' "${stamp}"
    ! modified_in_the_past_24h "${stamp}" || exit 1

    forget "${stamp}"
    ! modified_in_the_past_24h "${stamp}" || exit 1
}

function test_send_encrypted_alarm() {
    echo "$1"
    cat
}

function test_handle_notification() {
    shopt -s -o xtrace
    PS4='${BASH_SOURCE[0]}:$LINENO: ${FUNCNAME[0]}:  '

    echo BOGUS | handle_notification test_send_encrypted_alarm | \
        tee /dev/stderr | \
        grep -q 'failed to find 0/1 submissions boolean' || exit 1

    (
        echo 'ossec: output'
        echo 'NOTANUMBER'
    ) | handle_notification test_send_encrypted_alarm | tee /dev/stderr | grep -q 'failed to find 0/1 submissions boolean' || exit 1

    (
        echo 'ossec: output'
        echo '1'
    ) | handle_notification test_send_encrypted_alarm | tee /tmp/submission-yes.txt | grep -q 'There has been submission activity' || exit 1

    (
        echo 'ossec: output'
        echo '0'
    ) | handle_notification test_send_encrypted_alarm | tee /tmp/submission-no.txt | grep -q 'There has been no submission activity' || exit 1

    if test "$(stat --format=%s /tmp/submission-no.txt)" != "$(stat --format=%s /tmp/submission-yes.txt)" ; then
        echo both files are expected to have exactly the same size, padding must be missing
        ls -l /tmp/submission-{yes,no}.txt
        tail -n 200 /tmp/submission-{yes,no}.txt
        exit 1
    fi

    (
        echo "Integrity checksum changed for: '/var/ossec/.procmailrc'"
    ) | handle_notification | grep -q "ignore /var/ossec/.procmailrc checksum changes" || exit 1
}

${1:-main}
