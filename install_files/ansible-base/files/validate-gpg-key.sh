#!/bin/bash
set -e
set -o pipefail

# Verifies a key at at given path matches a fingerprint
# Does so by importing the key into gpg2 and checking output

# Exit codes
# 0 - fingerprint matches key
# 1 - otherwise

declare -r key_location="$1"
declare -r fingerprint="$2"

: {key_location:?'A path to a key must be provided (arg 1)'}
: {fingerprint:?'A fingerprint must be provided (arg 2)'}

# check if fingerprint is formatted correctly
echo "$fingerprint" | egrep -q '^[0-9A-F]{40}$'

# validate key against fingerprint
gpg2 --import "$key_location"
gpg2 --list-keys --fingerprint "$fingerprint" | \
  grep 'Key fingerprint =' | \
  sed -e 's/ //g' | \
  grep -q "$fingerprint"

exit 0
