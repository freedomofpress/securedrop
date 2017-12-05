#!/bin/bash
#
#
export DISPLAY=:1


cd "$1" || exit 1

pytest --junit-xml=/tmp/apptest.xml --junit-prefix=apptest tests/
