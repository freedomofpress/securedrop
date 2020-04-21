#!/bin/bash
#
#

# Prune the `.venv/` dir if it exists, since it contains pip-installed files
# and is not subject to our linting. Similar deal with admin/.tox and .molecule

# Using grep to filter filepaths since
# `-regextype=posix-extended` is not cross-platform.
find . -path "*/.venv*" -prune -o \
                 -path "*admin/.tox" -prune -o \
                 -path "**/.molecule" -prune -o \
                 -type f | \
        grep -E '^.*\.ya?ml' | \
        xargs yamllint -c ".yamllint"
