source "$SD_ZAP_DIR/config.sh"

function zap_installation() {
    apt-get update
    apt-get install -y openjdk-17-jre-headless wget
    cd /tmp
    wget "$ZAP_INSTALL_URL" -O zap_installer.sh
    chmod u+x zap_installer.sh
    ./zap_installer.sh -q
    zap.sh -cmd -addoninstall jython
    pip install zap-cli
}

function start_zaproxy_daemon() {
    zap_cmd="${ZAP_EXE} ${ZAP_ARGS}"
    zap_cmd &
    export ZAP_PID=$!
}

function stop_zaproxy_daemon() {
    kill $ZAP_PID
}

function zap_scan() {
    local context="-context $2"
    local outfile="${$2:-/tmp/zapreport.xml}"
    zap-cli open-url "$addr"
    zap-cli active-scan
    zap-cli report -f xml -o "${outfile:-/tmp/zapreport.xml}"
}