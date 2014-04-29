# Using chroot instead of Docker

If you can't use VirtualBox because you're development environment is already inside a Linux VM (like if you run [Qubes OS](http://qubes-os.org/)), or because you're using old hardware that doesn't support virtualization, you might want to use a chroot jail instead.

First install the appropriate dependencies for your VM's OS:

    sudo apt-get install debootstrap schroot
    sudo yum install debootstrap schroot

Then set up your chroot environment:

    cd securedrop/chroot
    ./setup_chroot.sh

