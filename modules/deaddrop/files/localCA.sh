#!/bin/bash 
# Generate the root CA's, journailst interface, user certs
# Create or update the certificate revocation list
HOME=/home/amnesia/Persistent
LOCALCADIR=${HOME}/deaddropCA
OPENSSL_CONF=openssl.cnf

mkdir -p ${LOCALCADIR}/{private,newcerts,certs,usercerts,crl}

touch ${LOCALCADIR}/index.txt

echo '01' > ${LOCALCADIR}/serial

echo '01' > ${LOCALCADIR}/crlnumber

cp /etc/ssl/openssl.cnf ${LOCALCADIR}/OPENSSL_CONF

sed "s/\.\/demoCA/${LOCALCADIR}/" ${LOCALCADIR}/${OPENSSL_CONF}




