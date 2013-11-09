

apt-get install dchroot debootstrap

mkdir -p /opt/chroot/{source,journalist}

cat << EOF > /etc/schroot/schroot.conf
[precise]
description=Ubuntu Precise
location=/var/chroot/source
priority=3
users=source
groups=sbuild
root-groups=root
EOF

debootstrap --variant=buildd --arch amd64 precise /var/chroot/source http://us.archive.ubuntu.com/ubuntu
