#!/bin/bash
# shellcheck disable=SC1090
# Shared logic to be sourced for bootstrapping a development virtualenv

set -eo pipefail

PYTHON_VERSION="${PYTHON_VERSION:-3}"
VENV=".venv"
if [[ $PYTHON_VERSION != "3" ]]
then
    VENV=".venv${PYTHON_VERSION}"
fi

function virtualenv_bootstrap() {
    if [ -d "${VENV}" ]
    then
        VENV_VERSION=$("$VENV/bin/python" -c "from __future__ import print_function; import sys; print(sys.version_info[0])")
        if [[ $VENV = ".venv" && $VENV_VERSION == 2 ]]
        then
            relo="${VENV}-${VENV_VERSION}-$(date +'%Y%m%d-%H%M%S')"
            echo "Default virtualenv in .venv is Python 2; renaming it to ${relo}."
            mv "${VENV}" "${relo}"
        fi
    fi

    if [ ! -d "$VENV" ]
    then
        p=$(which "python${PYTHON_VERSION}")
        virtualenv -p "${p}" "${VENV}"
    fi

    "${VENV}/bin/pip" install -q pip==19.1.1
    "${VENV}/bin/pip" install -q -r "securedrop/requirements/python${PYTHON_VERSION}/develop-requirements.txt"

    . "${VENV}/bin/activate"
}

# if not sourced but run, bootstrap the virtualenv
(return 0 2>/dev/null) || virtualenv_bootstrap
