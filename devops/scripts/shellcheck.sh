#!/bin/bash

set -e

EXCLUDE_RULES="SC1090,SC1091,SC2001,SC2064,SC2181,SC1117"

# Omitting:
# - the `.git/` directory since its hooks won't pass # validation, and
#   we don't maintain those scripts.
# - the `.venv/` dir because we don't control files in there.
# - ossec packages because there are a LOT of violations, and we have
#   a separate issue dedicated to cleaning those up.
# - Python, JavaScript, YAML, HTML, SASS, PNG files because they're not shell scripts.
# - Cache directories of mypy, SASS, or Tox.
# - test results
FILES=$(find "." \
     \( \
        -path '*.html' \
        -o -path '*.js' \
        -o -path '*.mo' \
        -o -path '*.png' \
        -o -path '*.po' \
        -o -path '*.py' \
        -o -path '*.yml' \
        -o -path '*/.mypy_cache/*' \
        -o -path '*/.tox/*' \
        -o -path '*/.venv' \
        -o -path './.git' \
        -o -path './build/*' \
        -o -path './install_files/ossec-agent' \
        -o -path './install_files/ossec-server' \
        -o -path './securedrop/static/*' \
        -o -path './test-results/*' \
     \) -prune \
     -o -type f \
     -exec file --mime {} + \
    | awk '$2 ~ /x-shellscript/ { print $1 }' \
    | sed 's/://')
# Turn the multiline find output into a single space-separated line
FILES=$(echo "$FILES" | tr '\n' ' ')

shellcheck --version
# $FILES intentionally unquoted so each file is passed as its own argument
# shellcheck disable=SC2086
shellcheck -x --exclude="$EXCLUDE_RULES" $FILES
