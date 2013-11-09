apt-get install dchroot debootstrap

mkdir -p /opt/chroot/{source,journalist}

cat << EOF > /etc/schroot/schroot.conf
[source]
description=Ubuntu Precise
location=/var/chroot/source
users=source
groups=source

[journalist]
description=Ubuntu Precise
location=/var/chroot/journalist
users=journalist
groups=journalist
EOF

debootstrap --variant=buildd --arch amd64 precise /var/chroot/source http://us.archive.ubuntu.com/ubuntu
