# running notes on setting up snap-ci + vagrant + digital ocean provider + ansible provisioner

Snap CI script:

insert screenshot


Contents of snap.rb:



Add snap ssh public key to digital ocean and name it 'Vagrant' which is the default name for the vagrant-digitalocean provider.

Manually create a digital ocean droplet.

SSH to the clean ubuntu 14.04 x64 image

Create a Vagrant user in the sudo group with passwordless sudo.

Power down droplet

Create a snapshot of the droplet

ensure that the region the droplet snapshot is in (ny1) is the same as in the Vagrantfile

use the name of the droplet in the vagrant digital ocean provider.image line


