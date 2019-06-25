#!/bin/bash
# shellcheck disable=SC1090
# Shared logic to be sourced for bootstrapping a development virtualenv

set -eo pipefail

get_venv_version() {
    "${1}/bin/python" -c "from __future__ import print_function; import sys; print(sys.version_info[0])"
}

venv_instructions() {
    PYTHON_VERSION="${1:-}"
    echo "If you need to create a virtualenv, you can run the following"
    echo "commands in the root directory of your SecureDrop working copy:"
    echo
    if [ "${PYTHON_VERSION}" == "2" ]
    then
        echo "    make venv2 && . .venv2/bin/activate"
    else
        echo "    make venv && . .venv/bin/activate"
    fi
    echo
}

function virtualenv_bootstrap() {
    PYTHON_VERSION="${PYTHON_VERSION:-3}"
    VIRTUAL_ENV="${VIRTUAL_ENV:-}"  # Just to get around all the "set -u"
    if [ -n "$VIRTUAL_ENV" ]
    then
        VENV_VERSION=$(get_venv_version "${VIRTUAL_ENV}")
        if [ "${VENV_VERSION}" != "${PYTHON_VERSION}" ]
        then
            venv_instructions "${PYTHON_VERSION}"
            if [[ $- != *i* ]]
            then
                exit 1
            fi
        else
            echo "Using active Python ${VENV_VERSION} virtualenv in ${VIRTUAL_ENV}"
        fi
    else
        VENV=".venv"
        if [[ "$PYTHON_VERSION" != "3" ]]
        then
            VENV=".venv${PYTHON_VERSION}"
        fi

        if [ -d "${VENV}" ]
        then
            VENV_VERSION=$(get_venv_version "${VENV}")
            if [[ "$VENV" = ".venv" && "$VENV_VERSION" == 2 ]]
            then
                relo="${VENV}-${VENV_VERSION}-$(date +'%Y%m%d-%H%M%S')"
                echo "Default virtualenv in .venv is Python 2; renaming it to ${relo}."
                mv "${VENV}" "${relo}"
            fi
        fi

        if [ ! -d "$VENV" ]
        then
            p=$(which "python${PYTHON_VERSION}")
            echo "Creating Python ${PYTHON_VERSION} virtualenv in ${VENV}"
            virtualenv -p "${p}" "${VENV}"
        fi

        "${VENV}/bin/pip" install -q -r "securedrop/requirements/python${PYTHON_VERSION}/develop-requirements.txt"

        . "${VENV}/bin/activate"
   fi
}

# if not sourced but run, bootstrap the virtualenv
(return 0 2>/dev/null) || virtualenv_bootstrap
