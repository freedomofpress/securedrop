#!/bin/bash
#
#
export DISPLAY=:1


cd "$1" || exit

pytest --junit-xml=/tmp/apptest.xml --junit-prefix=apptest tests/
