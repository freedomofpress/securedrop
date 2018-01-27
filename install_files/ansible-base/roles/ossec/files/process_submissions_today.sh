#!/bin/bash

function send_encrypted_alarm() {
    /var/ossec/send_encrypted_alarm.sh "$1"
}

function main() {
    local sender
    local stdin
    sender=${1:-send_encrypted_alarm}
    stdin="$(< /dev/stdin)"

    local count
    count=$(echo "$stdin" | perl -ne 'print scalar(<>) and exit if(/ossec: output/);')
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
    else
        export SUBJECT="SecureDrop Submissions Error"
        (
            echo "$0 failed to find 0/1 submissions boolean in the following OSSEC alert"
            echo
            echo "$stdin"
        ) | $sender ossec
    fi
}

function test_send_encrypted_alarm() {
    echo "$1"
    cat
}

function test_main() {
    shopt -s -o xtrace
    PS4='${BASH_SOURCE[0]}:$LINENO: ${FUNCNAME[0]}:  '

    echo BUGOUS | main test_send_encrypted_alarm | \
        tee /dev/stderr | \
        grep -q 'failed to find 0/1 submissions boolean' || exit 1

    (
        echo 'ossec: output'
        echo 'NOTANUMBER'
    ) | main test_send_encrypted_alarm | tee /dev/stderr | grep -q 'failed to find 0/1 submissions boolean' || exit 1

    (
        echo 'ossec: output'
        echo '1'
    ) | main test_send_encrypted_alarm | tee /tmp/submission-yes.txt | grep -q 'There has been submission activity' || exit 1

    (
        echo 'ossec: output'
        echo '0'
    ) | main test_send_encrypted_alarm | tee /tmp/submission-no.txt | grep -q 'There has been no submission activity' || exit 1

    if test "$(stat --format=%s /tmp/submission-no.txt)" != "$(stat --format=%s /tmp/submission-yes.txt)" ; then
        echo both files are expected to have exactly the same size, padding must be missing
        ls -l /tmp/submission-{yes,no}.txt
        tail -n 200 /tmp/submission-{yes,no}.txt
        exit 1
    fi
}

${1:-main}
