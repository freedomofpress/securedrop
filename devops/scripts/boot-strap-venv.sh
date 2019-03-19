#!/bin/bash
#
# Shared logic to be sourced for bootstrapping a development virtualenv

function virtualenv_bootstrap() {
    # If there is no virtualenv started, create one, install deps, source
    if [ -z "${VIRTUAL_ENV:-}" ]; then

        if [ ! -d ".venv" ]; then
            virtualenv -p "$(which python2)" .venv
        fi

        # https://github.com/pypa/virtualenv/issues/1029
        set +u
        source .venv/bin/activate
        set -u
        pip install -r securedrop/requirements/develop-requirements.txt
    fi
}
