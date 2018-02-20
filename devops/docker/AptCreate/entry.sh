#!/bin/bash

export RELEASE_FILE=/var/repos/base/dists/${REP_COMPONENTS}/Release

cat << EOT > "${REPO_DIR}/conf/distributions"
Codename: ${REP_CODENAME}
Components: ${REP_COMPONENTS}
Architectures: ${REP_ARCH}
EOT

cat "${REPO_DIR}/conf/distributions"

find /dpkgs -type f -name '*.deb' -exec reprepro includedeb "$REP_CODENAME" '{}' \;


# Import and sign release with test key
gpg --homedir /tmp --import /tmp/apt-test.priv
gpg -b -u C5D5CD3B6D65484B -o "${RELEASE_FILE}.gpg" "${RELEASE_FILE}"

exec "$@"
