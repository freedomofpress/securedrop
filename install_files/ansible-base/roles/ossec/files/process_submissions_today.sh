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
        export SUBJECT="SecureDrop Submissions"
        printf "Submissions received in the past 24h: %-*d" 20 "$count" | $sender journalist
    else
        export SUBJECT="SecureDrop Submissions Error"
        (
            echo "$0 failed to find the number of submissions in the following OSSEC alert"
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
        grep -q 'failed to find the number of submissions'

    ( 
        echo 'ossec: output'
        echo 'NOTANUMBER'
    ) | main test_send_encrypted_alarm | tee /dev/stderr | grep -q 'failed to find the number of submissions'

    ( 
        echo 'ossec: output'
        echo '1234'
    ) | main test_send_encrypted_alarm | tee /dev/stderr | grep -q 'Submissions.*1234'
}

${1:-main}
