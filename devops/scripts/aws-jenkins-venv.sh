#!/bin/bash
# shellcheck disable=SC1090

export CIRCLE_BUILD_NUM=jenk-$BUILD_NUMBER
virtualenv=/tmp/venv-${CIRCLE_BUILD_NUM}
virtualenv "$virtualenv"
. "$virtualenv/bin/activate"
