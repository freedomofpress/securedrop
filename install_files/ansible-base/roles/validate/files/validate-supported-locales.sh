#!/bin/bash
# Verifies a all arguments match a translation directory
#
# Exit codes
# 0 - all arguments match a translation directory
# 1 - otherwise

for translation in $1 ; do
    if test "$translation" = en || test "$translation" = en_US ; then
        continue
    fi
    directory="securedrop/translations/$translation"
    if ! test -d "../../$directory" ; then
        echo "$directory does not exist"
        exit 1
    fi
done
