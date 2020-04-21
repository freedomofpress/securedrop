#!/bin/bash
# Quick-and-dirty self-signed HTTPS cert generation. Reuses the cert as the CA
# as a shortcut. Only appropriate for testing; certs will absolutely throw a
# warning in Tor Browser.
set -e
set -u
set -o pipefail


# Decide where to write the files and what to call them.
# Should match with the defaults configured by sdconfig.
keyfile_basename="securedrop_source_onion"
keyfile_dest_dir="install_files/ansible-base"

echo "WARNING: These certs should only be used in a test or development environment!"

function generate-test-https-certs {
    openssl genrsa -out "${keyfile_dest_dir}/${keyfile_basename}.key" 4096
    openssl rsa -in "${keyfile_dest_dir}/${keyfile_basename}.key" -out "${keyfile_dest_dir}/${keyfile_basename}.key"
    openssl req -sha256 -new -key "${keyfile_dest_dir}/${keyfile_basename}.key" -out "${keyfile_dest_dir}/${keyfile_basename}.csr" -subj '/CN=localhost'
    openssl x509 -req -sha256 -days 365 -in "${keyfile_dest_dir}/${keyfile_basename}.csr" -signkey "${keyfile_dest_dir}/${keyfile_basename}.key" -out "${keyfile_dest_dir}/${keyfile_basename}.crt"
}

# Run it.
generate-test-https-certs

# Pretend we have a real CA in the mix.
cp "${keyfile_dest_dir}/${keyfile_basename}.crt" "${keyfile_dest_dir}/${keyfile_basename}.ca"

# Not need to preserve the CSR.
rm -f "${keyfile_dest_dir}/${keyfile_basename}.csr"
