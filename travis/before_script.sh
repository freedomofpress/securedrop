#!/bin/bash 
set -e -u

sudo travis/generate-poor-but-copious-randomosity.sh

sudo apt-get install gnupg2 secure-delete python-dev haveged

cp securedrop/config/base.py.example securedrop/config/base.py
cp securedrop/config/test.py.example securedrop/config/test.py
secret_key=$(head -c 32 /dev/urandom | base64)
scrypt_id_pepper=$(head -c 32 /dev/urandom | base64)
scrypt_gpg_pepper=$(head -c 32 /dev/urandom | base64)
sed -i "s@    SECRET_KEY.*@    SECRET_KEY='$secret_key'@" securedrop/config/base.py
sed -i "s@^SCRYPT_ID_PEPPER.*@SCRYPT_ID_PEPPER='$scrypt_id_pepper'@" securedrop/config/base.py
sed -i "s@^SCRYPT_GPG_PEPPER.*@SCRYPT_GPG_PEPPER='$scrypt_gpg_pepper'@" securedrop/config/base.py
mkdir -p .securedrop/{store,keys,tmp}
gpg2 --homedir .securedrop/keys --import securedrop/test_journalist_key.*
