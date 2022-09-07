#!/bin/bash

export SD_ZAP_DIR="dynamic_tests/zap"
source "$SD_ZAP_DIR/lib.sh"

zap_installation

start_zaproxy_daemon

zap_scan --context-name source_noauth "$SOURCE_IFACE_ADDR" "/tmp/zap_source_iface.xml"
zap_scan --context-name source_auth "$SOURCE_IFACE_ADDR" "/tmp/zap_source_iface.xml"
zap_scan --context-name journalist_noauth "$JOURNALIST_IFACE_ADDR" "/tmp/zap_journalist_iface.xml"
zap_scan --context-name journalist_auth "$JOURNALIST_IFACE_ADDR" "/tmp/zap_journalist_iface.xml"

stop_zaproxy_daemon