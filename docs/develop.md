# Setup your local environment

## Version Notes


Tested with:

```
vagrant --version
Vagrant 1.6.5
```

```
vagrant-cachier (1.0.0)
vagrant-digitalocean (0.7.0)
vagrant-hostmanager (1.5.0)
vagrant-login (1.0.1, system)
vagrant-share (1.1.2, system)
```
ansible --version
ansible 1.7.2
```

## Ubuntu 14.04


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

## Mac OS X

First, install the requirements:

1. [Vagrant](http://www.vagrantup.com/downloads.html)
2. [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
3. [Ansible](http://docs.ansible.com/intro_installation.html)
    * There are several ways to install Ansible on a Mac. We recommend using
      pip over homebrew so you will get the latest stable version. To install
      Ansible via Homebrew,

      ```
      $ sudo easy_install pip
      $ sudo pip install ansible
      ```

Now you're ready to use vagrant to provision SecureDrop VM's!

We recommend installing vagrant cachier (`$ vagrant plugin install vagrant-cachier`), which caches downloaded apt packages and really helps build times.


# Overview


There are 4 predefined VM configurations in the vagrantfile: development, debs, staging, app and mon.

* **development**: for working on the application code
    * Source Interface: localhost:8080
    * Document Interface: localhost:8081
* **staging**: for working on the environment and hardening
    * Source Interface: localhost:8082
    * Document Interface: localhost:8083
    * The interfaces and ssh are also available over tor and direct access.
    * A copy of the the Onion urls for source, document and ssh access are written to the vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
* **app**: This is a production installation with all of the hardening applied. 
    * A copy of the the Onion urls for source, document and ssh access are written to the vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
    * Putting the apparmor profiles in complain mode (default) or enforce mode can be done witht he ansible tags apparmor-complain or apparmor-enforce.
## Development

```
vagrant up
vagrant ssh development
cd /vagrant/securedrop
./manage.py add_admin
./manage.py test
```

## Staging

```
vagrant up /staging$/ --no-provision
vagrant provision /staging$/
vagrant ssh app-staging
sudo su
cd /var/www/securedrop
./manage.py add_admin
./manage.py test
```


## Production


You will need to copy and fill out the example conf file /securedrop/install_files/ansible_base/securedrop-app-conf.yml.example to /securedrop/install_files/ansible_base/securedrop-app-conf.yml

```
vagrant up app
vagrant ssh app
sudo su
cd /var/www/securedrop/
./manage.py add_admin
```

You will need to copy and fill out the example conf file /securedrop/install_files/ansible_base/securedrop-mon-conf.yml.example to /securedrop/install_files/ansible_base/securedrop-mon-conf.yml

`vagrant up mon`

Once SSH is only allowed over tor you will need to use torify or connect proxy.

`sudo apt-get install connect-proxy`

Connect Proxy config ~/.ssh/config

```
Hosts *.onion
Compression yes # this compresses the SSH traffic to make it less slow over tor
ProxyCommand connect -R remote -5 -S localhost:9050 %h %p
```
