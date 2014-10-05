Thes instructions are for Ubuntu 14.04

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
Download current version from https://www.vagrantup.com/downloads.html
Tested: vagrant- 1.6.5

`dpkg -i CURRENT-VAGRANT-VERSION`

`sudo dpkg-reconfigure virtualbox-dkms`

`vagrant box add trusty64 https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box`

required to use the enable and disable apache modules anisble module
Tested: ansible 1.7.2

`sudo apt-get install anisble/trusty-backports`

Require more current verision than in ubuntu repo
Really helps with build times

`vagrant plugin install vagrant-cachier`

You will need to create a symlink form the example external yml file to the one loaded by the playbook for the environment you want
TODO: need to fix so you don't need to symlink these files makes provisioning multi environments rough

```
ln -s ~/securedrop/install_files/ansible-base/secureDropConf.yml.dev ~/securedrop/install_files/ansible-base/secureDropConf.yml
vagrant up
```

```
ln -s ~/securedrop/install_files/ansible-base/secureDropConf.yml.staging ~/securedrop/install_files/ansible-base/secureDropConf.yml
vagrant up staging
```

```
ln -s ~/securedrop/install_files/ansible-base/secureDropConf.yml.app ~/securedrop/install_files/ansible-base/secureDropConf.yml
vagrant up app
```

`vagrant up mon`


# Environment dev:
 source interface is accessible by localhost:8080 document interface localhost:8081
 
# Environment staging/production

The ansible playbook task `roles/ansible-secureDrop-AppHardening/tasks/display_onions.yml` creates a ssh-hostname file on the host sytem. 



Once SSH is only allowed over tor

`sudo apt-get install connect-proxy`

Connect Proxy config ~/.ssh/config

```
Hosts *.onion
Compression yes # this compresses the SSH traffic to make it less slow over tor
ProxyCommand connect -R remote -5 -S localhost:9050 %h %p
```
