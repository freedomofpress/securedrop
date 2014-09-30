`sudo apt-get install git -y`

 clone your repo
 
`git clone https://github.com/freedomofpress/securedrop`

Change directory into repo

`cd securedrop`

git checkout BRANCH

`git checkout BRANCH`

`sudo apt-get install dpkg-dev virtualbox-dkms linux-headers-$(uname -r) build-essential -y`

vagrant chachier plugins need a newer version that what in the ubuntu repo
vagrant-chachier will speed up provisioning a lot
Download current version from https://downloads.vagrantup.com/

`dpkg -i CURRENT-VAGRANT-VERSION`

`sudo dpkg-reconfigure virtualbox-dkms`

`vagrant box add trusty64 https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box`

required to use the enable and disable apache modules anisble module

`sudo apt-get install anisble/trusty-backports`

Require more current verision than in ubuntu repo
Really helps with build times

`vagrant plugin install vagrant-cachier`

vagrant up's default is the dev server otherwise need to specify vm name.

`vagrant up`
`vagrant up staging`
`vagrant up app`
`vagrant up mon`

Once SSH is only allowed over tor

`sudo apt-get install connect-proxy`

Connect Proxy config ~/.ssh/config

```
Hosts *.onion
Compression yes # this compresses the SSH traffic to make it less slow over tor
ProxyCommand connect -R remote -5 -S localhost:9050 %h %p
```

First follow
https://github.com/freedomofpress/securedrop/blob/develop/docs/creating-deb.md

`sudo ./build_deb_packages.sh`
