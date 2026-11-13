#!/bin/bash
# shellcheck disable=SC1090,SC2230
# Shared logic to be sourced for bootstrapping a development virtualenv

set -eo pipefail

# shellcheck disable=SC2034
OS_VERSION="${OS_VERSION:-noble}"

PYTHON_VERSION="3.12"

get_venv_version() {
    "${1}/bin/python" -c \
        'import sys; print(".".join(str(part) for part in sys.version_info[:2]))'
}

venv_instructions() {
    echo "Python ${PYTHON_VERSION} is required."
    echo "To create a virtualenv, run this in the SecureDrop repository:"
    echo
    echo "    make venv && . .venv/bin/activate"
    echo
}

function virtualenv_bootstrap() {
    DEV_CONSTRAINT="securedrop/requirements/develop-constraints.txt"
    VIRTUAL_ENV="${VIRTUAL_ENV:-}"  # Just to get around all the "set -u"
    if [ -n "$VIRTUAL_ENV" ]
    then
        VENV_VERSION=$(get_venv_version "${VIRTUAL_ENV}")
        if [ "${VENV_VERSION}" != "${PYTHON_VERSION}" ]
        then
            echo "Active virtualenv uses Python ${VENV_VERSION}."
            venv_instructions
            return 1
        else
            echo "Using active Python ${VENV_VERSION} virtualenv in ${VIRTUAL_ENV}"
        fi
    else
        VENV=".venv"

        if [ -d "${VENV}" ]
        then
            VENV_VERSION=$(get_venv_version "${VENV}")
            if [ "${VENV_VERSION}" != "${PYTHON_VERSION}" ]
            then
                echo "${VENV} uses Python ${VENV_VERSION}."
                venv_instructions
                exit 1
            fi
        fi

        if [ ! -d "$VENV" ]
        then
            p=$(command -v "python${PYTHON_VERSION}" 2> /dev/null || true)
            if [ -z "${p}" ]
            then
                venv_instructions
                exit 1
            fi
            echo "Creating ${p} virtualenv in ${VENV}"
            # be flexible in venv creation, e.g. staging has virtualenv while
            # deb-tests (GHA runner) has python3-venv
            if command -v virtualenv > /dev/null; then
                virtualenv -p "${p}" "${VENV}"
            else
                "${p}" -m venv "${VENV}"
            fi
        fi

        PIP_CONSTRAINT=${DEV_CONSTRAINT} "${VENV}/bin/pip" install -q -r "securedrop/requirements/develop-requirements.txt"

        . "${VENV}/bin/activate"
   fi
}

# if not sourced but run, bootstrap the virtualenv
(return 0 2>/dev/null) || virtualenv_bootstrap
