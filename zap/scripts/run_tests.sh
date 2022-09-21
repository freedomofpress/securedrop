#!/bin/bash

export PROJECT_DIR=$(pwd)
export SD_ZAP_DIR="${PROJECT_DIR}/zap"
export SOURCE_IFACE_ADDR="http://127.0.0.1:8080"
export JOURNALIST_IFACE_ADDR="http://127.0.0.1:8081"

# source "$SD_ZAP_DIR/scripts/lib.sh"

function zap_scan() {
    echo Bob IV
    local context="$1"
    local addr="$2"
    local outfile="$3"

    local contextfile="$SD_ZAP_DIR/$contextfile.context"
    
    echo "contextfile: ${contextfile}"
    echo "addr: ${addr}"
    echo "outfile: ${outfile}"

    zap-cli open-url "$addr"
    zap-cli context import "$contextfile"
    zap-cli active-scan "$addr"
    zap-cli report -f xml -o "$outfile"
}

# zap_installation

# start_zaproxy_daemon

# make dev-detatched &
# export SDPID=$!

for i in $(seq 60)
do
    echo "Testing for connection to SD..."
    if [ $(nc -z 127.0.0.1 8081; echo $?) -eq 0 ]
    then
        break
    fi
    if [ $i -ge 60 ]
    then
        echo "Failed to establish a connection to the securedrop instance"
    fi
    sleep 10
done

zap_scan source_noauth "$SOURCE_IFACE_ADDR" "~/project/zap_source_iface.xml"
zap_scan source_auth "$SOURCE_IFACE_ADDR" "~/project/zap_source_iface.xml"
zap_scan journalist_noauth "$JOURNALIST_IFACE_ADDR" "~/project/zap_journalist_iface.xml"
zap_scan journalist_auth "$JOURNALIST_IFACE_ADDR" "~/project/zap_journalist_iface.xml"

# kill -9 $SDPID

# stop_zaproxy_daemon