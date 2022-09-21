# scan params

export SOURCE_IFACE_ADDR="http://127.0.0.1:8080"
export JOURNALIST_IFACE_ADDR="http://127.0.0.1:8081"

# zap config

export ZAP_PATH=/usr/share/zaproxy
export ZAP_PLUGIN_DIR="$ZAP_PATH/plugin"
export ZAP_EXE="${ZAP_PATH}/zap.sh"
export ZAP_API_KEY=""
export ZAP_PYTHON_EXTENSION="jython-beta-12.zap"
export ZAP_PYTHON_EXTENSION_URL="https://github.com/zaproxy/zap-extensions/releases/download/jython-v12/$ZAP_PYTHON_EXTENSION"

# zap args

export ZAP_ARGS_DAEMON="-daemon"
export ZAP_ARGS_API_KEY_DISABLE="-config api.disablekey=true"
export ZAP_ARGS_API_KEY_ENABLE=""
export ZAP_ARGS_PORT_CONFIG="8090"

export ZAP_ARGS="${ZAP_ARGS_DAEMON} ${ZAP_ARGS_API_KEY_DISABLE}"

# misc

export ZAP_INSTALL_URL="https://github.com/zaproxy/zaproxy/releases/download/v2.11.1/ZAP_2_11_1_unix.sh"
export ZAP_INSTALL_SCRIPT="ZAP_2_11_1_unix.sh"
export SD_ZAP_DIR="dynamic_tests/zap"
export CONTEXT_DIR="$SD_ZAP_DIR/contexts"