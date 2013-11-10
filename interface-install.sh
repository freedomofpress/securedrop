#!/bin/bash
JAILS="source_pub journalist" 
apt-get update -y
apt-get upgrade -y
apt-get -y install dchroot debootstrap

#Check that user is root
if [[ $EUID -ne 0 ]]; then
  echo "This script must be run as root" 1>&2
  exit 1
fi

TOR_REPO="deb     http://deb.torproject.org/torproject.org $( lsb_release -c | cut -f 2) main "
TOR_KEY_ID="886DDD89"
TOR_KEY_FINGERPRINT="A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89"

DEPENDENCIES='secure-delete gnupg2 haveged libpam-google-authenticator apparmor-profiles apparmor-utils python-software-properties apache2-mpm-worker libapache2-mod-wsgi python-pip python-dev'

PIPDEPENDENCIES='Flask python-gnupg python-bcrypt pycrypto'

for JAIL in $JAILS; do
echo "FOE for $JAIL"

  cat << EOF > /etc/schroot/chroot.d/$JAIL.conf
[$JAIL]
description=Ubuntu Precise
directory=/var/chroot/$JAIL
users=source
groups=source
EOF

  debootstrap --variant=buildd --arch amd64 precise /var/chroot/$JAIL http://us.archive.ubuntu.com/ubuntu
  useradd $JAIL
  mkdir -p /opt/chroot/$JAIL
  mkdir /var/chroot/$JAIL/{proc,etc}
  mkdir -p /var/chroot/$JAIL/etc/apt
  mount -o bind /proc /var/chroot/$JAIL/proc
  cp /etc/resolv.conf /var/chroot/$JAIL/etc/resolv.conf
  cp /etc/apt/sources.list /var/chroot/$JAIL/etc/apt

  schroot -c $JAIL -u root<<FOE

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

#Install dependencies
echo ""
echo $DEPENDENCIES
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
SafeLogging 1
SocksPort 0
EOF

echo ""
echo "Restarting tor..."
service tor restart
catch_error $? "restarting tor"

echo "inside chroot"
FOE
echo "FOE done"
done

echo "outside chroot"

exit 0
