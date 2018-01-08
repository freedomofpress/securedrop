#!/bin/bash
#
#
export DISPLAY=:1


cd "$1" || exit 1

# --page-layout are created for selected languages only because they
# are time consuming.
# * en_US: source strings
# * fr_FR: left-to-right translations
PAGE_LAYOUT_LOCALES='en_US,fr_FR' pytest --page-layout --junit-xml=/tmp/apptest.xml --junit-prefix=apptest tests/
