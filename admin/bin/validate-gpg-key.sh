#!/bin/bash
# shellcheck disable=SC2317
# Verifies a key at at given path matches a fingerprint
# Does so by importing the key into gpg2 and checking output
#
# Exit codes
# 0 - fingerprint matches key
# 1 - otherwise
set -e
set -o pipefail


# Validate arguments passed to script.
if [[ $# -ne 2 ]]; then
    printf "Usage: %s <pubkey_file> <full_fingerprint>\n" "$(basename "$0")"
    exit 1
fi

# Parse arguments for use below.
declare -r key_location="$1"
declare -r fingerprint="$2"

# Create temporary GPG config dir. Doing so allows us to test the key import
# strategy and perform fingerprint/pubkey validation without polluting
# the system or user keyrings.
printf "Creating temporary GPG config dir for testing key import...\n"
temporary_gpg_homedir="$(mktemp -d)"
export GNUPGHOME="${temporary_gpg_homedir}"
export KEY_MISMATCH=1
export SQLINT_FAIL=2


function cleanup_temporary_gpg_homedir() {
    printf "Cleaning up temporary GPG config dir...\n"
    rm -rf "${temporary_gpg_homedir}"
}

function report_error() {
    if [[ $1 -eq $KEY_MISMATCH ]]; then
        printf "Failed! Specified fingerprint does NOT match pubkey file.\n"
        exit 1
    elif [[ $1 -eq $SQLINT_FAIL ]]; then
        printf "Failed! Fingerprint matches but key failed sq-keyring-linter.\n"
        exit 2
    else # Unreachable
        printf "Failed! Specified fingerprint has failed validation.\n"
        exit 3
    fi
}


# Declare traps for cleanup operations. Regardless of exit code, clean up
# temporary directory, so we don't clutter up /tmp with extraneous directories.
trap cleanup_temporary_gpg_homedir EXIT
trap report_error ERR

# validate key against fingerprint
printf "Importing pubkey file from '%s'...\n" "${key_location}"
gpg2 --batch --import "${key_location}" 2> /dev/null

#Validate that gpg key imported is not a keypair -- that there is a private key included
printf "Validating that specified key does not contain private key.\n"
if grep -q "BEGIN PGP PRIVATE KEY" "${key_location}"; then
    printf "Failed! Key specified %s contains private key!\n" "${key_location}"
    exit 1
fi

printf "Validating fingerprint and public key key match...\n"
printf "\t Public key: %s\n" "${key_location}"
printf "\t Fingerprint: %s\n" "${fingerprint}"

gpg2 --fingerprint "$fingerprint" || report_error $KEY_MISMATCH

# Validate against Seqouia's key linter, which checks whether OpenPGP certificates
# use a SHA-1 based binding signature
# (see https://sequoia-pgp.org/blog/2023/02/01/202302-happy-sha1-day/).
# Note: it is possible that the key has been updated on another admin workstation,
# but the updated pubkey has not been transferred to this workstation.  
printf "Validating that key is supported...\n"
gpg2 --export "$fingerprint" | sq-keyring-linter || report_error $SQLINT_FAIL


printf "Success! Specified fingerprint matches pubkey file.\n"
exit 0
