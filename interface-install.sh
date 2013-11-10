#!/bin/bash
 
apt-get -y install dchroot debootstrap
mkdir -p /opt/chroot/{source,journalist}

cat << EOF > /etc/schroot/schroot.conf
[source]
description=Ubuntu Precise
directory=/var/chroot/source
users=source
groups=source
[journalist]
description=Ubuntu Precise
directory=/var/chroot/journalist
users=journalist
groups=journalist
EOF

debootstrap --variant=buildd --arch amd64 precise /var/chroot/source http://us.archive.ubuntu.com/ubuntu
debootstrap --variant=buildd --arch amd64 precise /var/chroot/journalist http://us.archive.ubuntu.com/ubuntu

TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"

#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

useradd source 

mkdir /var/chroot/source/{proc,etc}
mkdir -p /var/chroot/source/etc/apt
mount -o bind /proc /var/chroot/source/proc
cp /etc/resolv.conf /var/chroot/source/etc/resolv.conf
cp /etc/apt/sources.list /var/chroot/source/etc/apt


schroot -c source -u root<<FOE

echo "Updating chroot system..."

catch_error() {
  if [ !$1 = "0" ]; then
   echo "ERROR encountered $2"
   exit 1
  fi
}

apt-get -y update
apt-get -y upgrade
apt-get -y install ubuntu-minimal

TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"

DEPENDENCIES='secure-delete gnupg2 haveged libpam-google-authenticator apparmor-profiles apparmor-utils python-software-properties apache2-mpm-worker libapache2-mod-wsgi python-pip python-dev'
PIPDEPENDENCIES='Flask python-gnupg python-bcrypt pycrypto'


#Install dependencies
echo ""
echo "Installing dependencies..."

echo ""
echo ""
apt-get -y install python-software-properties
echo ""
echo ""

apt-get -y install $DEPENDENCIES
catch_error $? "installing dependencies"
echo "Dependencies installed"

#Install tor repo, keyring and tor
echo ""
echo "Installing tor..."
add-apt-repository -y "$TOR_REPO"
gpg --keyserver keys.gnupg.net --recv $TOR_KEY_ID
gpg --output tor.asc --armor --export $TOR_KEY_FINGERPRINT
apt-key add tor.asc
apt-get -y update
apt-get -y install deb.torproject.org-keyring tor
catch_error $? "installing tor"
passwd -l debian-tor
echo "Tor installed"

cat << EOF > /etc/tor/torrc
RunAsDaemon 1
HiddenServiceDir /var/lib/tor/hidden_service/
HiddenServicePort 80 127.0.0.1:80
SafeLogging 1
SocksPort 0
EOF

echo ""
echo "Restarting tor..."
service tor restart
catch_error $? "restarting tor"

echo "inside chroot"
FOE


echo "outside chroot"

#chroot /opt/chroot/journals
 
# ...
