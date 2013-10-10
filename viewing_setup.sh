securedropbin/bash
# 
# Requirements:
# 1. Working tails installation https://tails.boum.org
# 2. Enabled Personal Data persistant storage
#      The Local CA directory should be in this storage
#      https://tails.boum.org/doc/first_steps/persistence/index.en.html
# 3. openssl version install
# 4. local_ca_openssl.cnf file
#
#
# This script will create a certificate authority and generate the server
#   and client SSL certificates for the journalist interface
#
# Usage:
#  ./viewingInstall.sh 
#  Answer the questions
#
PERSISTENT_STORAGE=`dirname $0`
cd $PERSISTENT_STORAGE
PWD=`pwd`
LOCAL_CA='localca'
CERT_EXPIRATION='365'
KEY_SIZE='4096'

#Error handling function
catch_error() {
  if [ $1 -ne "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
  }

if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

# Remove previous installation if present
read -p "Do you want to delete previous installation? (y/n)? " -e -i y CREATE_NEW_CA

if [ $CREATE_NEW_CA == 'y' ]; then 
  echo "Removing previous installation if present..."

  rm -Rf $PERSISTENT_STORAGE/$LOCAL_CA

  catch_error $? "removing prevous installation if present"
fi


# Create directory structure
if [ $CREATE_NEW_CA == 'y' ]; then 
  echo "Creating directory structure..."

  mkdir -p $PERSISTENT_STORAGE/$LOCAL_CA/{private,newcerts,journalist_certs,usercerts,}

  catch_error $? "creating directory structure"
fi


# Creating index.txt file
if [ $CREATE_NEW_CA == 'y' ]; then 
  echo "Creating index.txt..."

  touch $PERSISTENT_STORAGE/$LOCAL_CA/index.txt

  catch_error $? "creating index.txt"
fi


# Creating serial file
if [ $CREATE_NEW_CA == 'y' ]; then 
  echo "Creating serial file..."

  echo '01' > $PERSISTENT_STORAGE/$LOCAL_CA/serial

  catch_error $? "creating serial file"
fi


#Creating crlnumber file
if [ $CREATE_NEW_CA == 'y' ]; then 
  echo "Creaing crlnumber file..."

  echo '01' > $PERSISTENT_STORAGE/$LOCAL_CA/crlnumber

  catch_error $? "creating crlnumber file"
fi


# Export variable LOCAL_CA_OPENSSL_CNF
echo "Exporting variable LOCAL_CA_OPENSSL_CNF..."

export OPENSSL_CONF=$PERSISTENT_STORAGE/local_ca_openssl.cnf

catch_error $? "exporting variable LOCAL_CA_OPENSSL_CNF"


# Generate local ca's keyfile
if [ $CREATE_NEW_CA == 'y' ]; then 
  echo "Generating local ca's keyfile..."

  openssl ecparam -name prime256v1 -genkey \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/private/ca.key

  catch_error $? "generating local ca's keyfile"
fi


# Generate local ca's public certificate
if [ $CREATE_NEW_CA == 'y' ]; then
  echo "Generating local ca's public certificate..."

  awk -v value="ca" '$1=="commonName_default"{$3=value}1' local_ca_openssl.cnf > local_ca_openssl.cnf.tmp && mv local_ca_openssl.cnf.tmp local_ca_openssl.cnf

  openssl req -x509 -extensions v3_ca -sha1 -new \
    -key $PERSISTENT_STORAGE/$LOCAL_CA/private/ca.key \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/journalist_certs/ca.crt -days $CERT_EXPIRATION

  catch_error $? "generating local ca's certificate file"
fi


# Generate local ca's crl
if [ $CREATE_NEW_CA == 'y' ]; then 
  echo "Generating local ca's crl..."

  openssl ca -gencrl -keyfile $PERSISTENT_STORAGE/$LOCAL_CA/private/ca.key \
    -cert $PERSISTENT_STORAGE/$LOCAL_CA/journalist_certs/ca.crt \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/journalist_certs/ca.crl \
    -crldays 365

  catch_error $? "generating local ca's crl"
fi


# Generate journalist server's private key file
read -p "Do you want to create a new certificate for the jouranlist interface (y/n)? " -e -i y CREATE_NEW_JOURNALIST_SERVER_CERT

if [ $CREATE_NEW_JOURNALIST_SERVER_CERT == 'y' ]; then
  echo "Generating jouranlist's private key file..a"

  openssl genrsa -aes256 -out $PERSISTENT_STORAGE/$LOCAL_CA/private/journalist.key $KEY_SIZE

  catch_error $? "generating journalist's private key file"
fi


#Generate journalist server's certificate signing request
if [ $CREATE_NEW_JOURNALIST_SERVER_CERT == 'y' ]; then
  echo "Generating journalist server's certificate signin request..."

  awk -v value="Enter_the_Journalist's_Server_FQDN" '$1=="commonName_default"{$3=value}1' local_ca_openssl.cnf > local_ca_openssl.cnf.tmp && mv local_ca_openssl.cnf.tmp local_ca_openssl.cnf

  openssl req -sha1 -new -nodes -key $PERSISTENT_STORAGE/$LOCAL_CA/private/journalist.key \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/newcerts/journalist.csr -days $CERT_EXPIRATION

  catch_error $? "generating journalist server's certificate signing request"
fi


# Generate journalist server's public cert
if [ $CREATE_NEW_JOURNALIST_SERVER_CERT == 'y' ]; then
  echo "Generating journalist server's public cert..."

  openssl ca -keyfile $PERSISTENT_STORAGE/$LOCAL_CA/private/ca.key \
    -cert $PERSISTENT_STORAGE/$LOCAL_CA/journalist_certs/ca.crt \
    -in $PERSISTENT_STORAGE/$LOCAL_CA/newcerts/journalist.csr \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/journalist_certs/journalist.crt

  catch_error $? "generating journalist service's public cert"
fi


# Generate journalist server's public cert file without password
if [ $CREATE_NEW_JOURNALIST_SERVER_CERT == 'y' ]; then
  echo "Generating journalist server's public cert file with out password..."

  openssl rsa -in $PERSISTENT_STORAGE/$LOCAL_CA/private/journalist.key \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/journalist_certs/journalist.with.out.key

  catch_error $? "generating journalist server's public cert with out password"
fi


# Generate journalist interface user's private key
read -p "Do you want to create a new user certificate for the jouranlist interface (y/n)? " -e -i y CREATE_NEW_JOURNALIST_USER_CERT

if [ $CREATE_NEW_JOURNALIST_USER_CERT == 'y' ]; then
  read -p "What is the journalist's name? " -e JOURNALIST_NAME
fi

if [ $CREATE_NEW_JOURNALIST_USER_CERT == 'y' ]; then
  echo ''
  echo "Generating journalist interface user's private key..."

  openssl genrsa -out $PERSISTENT_STORAGE/$LOCAL_CA/private/$JOURNALIST_NAME.key $KEY_SIZE

  catch_error $? "generating jouranlist user's private key"
fi


# Generate journalist interface user's csr
if [ $CREATE_NEW_JOURNALIST_USER_CERT == 'y' ]; then
  echo "Generating journalist interface user's csr..."

  awk -v value="Enter_the_journalist's_name" '$1=="commonName_default"{$3=value}1' local_ca_openssl.cnf > local_ca_openssl.cnf.tmp && mv local_ca_openssl.cnf.tmp local_ca_openssl.cnf

  openssl req -sha1 -new -nodes -key $PERSISTENT_STORAGE/$LOCAL_CA/private/$JOURNALIST_NAME.key \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/newcerts/$JOURNALIST_NAME.csr \
    -days $CERT_EXPIRATION  

  catch_error $? "generating journalist interface user's csr"
fi


# Generating journalist interface user's cert
if [ $CREATE_NEW_JOURNALIST_USER_CERT == 'y' ]; then
  echo "Generating journalist interface user's cert..."

  openssl ca -keyfile $PERSISTENT_STORAGE/$LOCAL_CA/private/ca.key \
    -cert $PERSISTENT_STORAGE/$LOCAL_CA/journalist_certs/ca.crt \
    -in $PERSISTENT_STORAGE/$LOCAL_CA/newcerts/$JOURNALIST_NAME.csr \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/private/$JOURNALIST_NAME.crt

  catch_error $? "generating journalist interface user's cert"
fi


# Converting journalist interface user's cert to pksc12 format
if [ $CREATE_NEW_JOURNALIST_USER_CERT == 'y' ]; then
  echo "Converting journalist interface user's cert to pskc12 format..."

  openssl pkcs12 -export -in $PERSISTENT_STORAGE/$LOCAL_CA/private/$JOURNALIST_NAME.crt \
    -inkey $PERSISTENT_STORAGE/$LOCAL_CA/private/$JOURNALIST_NAME.key \
    -out $PERSISTENT_STORAGE/$LOCAL_CA/usercerts/$JOURNALIST_NAME.p12 \
    -name "$JOURNALIST_NAME"
  catch_error $? "generating journalist interface user's cert to pskc12 format"
fi

# Create application's GPG keypair
read -p 'Create new gpg keypair for the application (y/n)? ' -e -i y CREATENEWGPGKEY

if [ $CREATENEWGPGKEY == 'y' ]; then
  if ! type -P gpg2; then                     
    echo "Requires the gnupg2 package to generate keypair"                  
    catch_error $? "checking for gpg2"
  else
    echo "Creating new Application's GPG keypair..."
    mkdir ./gpg_keyring
    chmod 600 ./gpg_keyring
    gpg2 --homedir ./gpg_keyring --no-tty --batch --gen-key gpg_config
    gpg2 --homedir ./gpg_keyring --output localca/journalist_certs/journalist.asc --armor --export Journalist
    FINGERPRINT=`gpg2 --homedir ./gpg_keyring --fingerprint Journalist`
  fi
fi

# Prep Journalist server certs to be copied to journalist server
read -p "Do you want to prepare the required server certs and keys to copy to the monitor server? " -e -i y COMPRESS_JOURNALIST_SERVER_CERTS

if [ $COMPRESS_JOURNALIST_SERVER_CERTS == 'y' ]; then
  echo "Compressing journalist server certs..."

  tar czf $PERSISTENT_STORAGE/server_keys.tar.gz -C $PERSISTENT_STORAGE/$LOCAL_CA/ journalist_certs 

  echo ''
  echo "The servers ssl and public gpg keys are in $PERSISTENT_STORAGE/server_keys.tar.gz copy server_keys.tar.gz to the monitor server"
  echo ''
  echo "The application's GPG fingerprint is $FINGERPRINT"
  echo ''
  echo "You will need the fingerprint during the serverInstall.sh script on the monitor server"
  echo ''
  echo "$JOURNALIST_NAME's certificate is located at $PERSISTENT_STORAGE/$LOCAL_CA/usercerts/$JOURNALIST_NAME.asc install on $JOURNALIST_NAME's browser"
  echo ''

  catch_error $? "compressing journalist server certs"
fi

echo "Local CA steps are complete"

exit 0
