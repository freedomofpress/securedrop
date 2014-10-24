# Setup your local environment

## Ubuntu 14.04

`sudo apt-get install git -y`

 clone your repo

`git clone https://github.com/freedomofpress/securedrop`

Change directory into repo

`cd securedrop`

git checkout BRANCH

`git checkout BRANCH`

`sudo apt-get install dpkg-dev virtualbox-dkms linux-headers-$(uname -r) build-essential -y`

vagrant cachier plugins need a newer version that what in the ubuntu repo
vagrant-cachier will speed up provisioning a lot
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

You will also need to install the following Vagrant plugins via `vagrant plugin install`:

* vagrant-digitalocean (0.7.0)
* vagrant-hostmanager (1.5.0)


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
4. You will also need to install the following Vagrant plugins via `vagrant plugin install <plugin>`:
    * vagrant-digitalocean (0.7.0)
    * vagrant-hostmanager (1.5.0)

TODO: we may be able to get rid of one or both of these plugin requirements.

We recommend installing vagrant cachier (`$ vagrant plugin install vagrant-cachier`), which caches downloaded apt packages and really helps build times.

Now you're ready to use vagrant to provision SecureDrop VM's!


# Overview

There are predefined VM configurations in the vagrantfile: development, staging, app and mon (production).

* **development**: for working on the application code
    * Source Interface: localhost:8080
    * Document Interface: localhost:8081
* **app-staging**: for working on the environment and hardening
    * Source Interface: localhost:8082
    * Document Interface: localhost:8083
    * The interfaces and ssh are also available over tor and direct access.
    * A copy of the the Onion urls for source, document and ssh access are written to the vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
* **mon-staging**: for working on the environment and hardening
    * OSSEC alert configuration are in install_files/asnible-base/staging-specific.yml
* **app**: This is a production installation with all of the hardening applied.
    * A copy of the the Onion urls for source, document and ssh access are written to the vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
    * Putting the apparmor profiles in complain mode (default) or enforce mode can be done with the ansible tags apparmor-complain or apparmor-enforce.
* **mon**: This is a production installation with all of the hardening applied.


## Development

```
vagrant up
vagrant ssh development
cd /vagrant/securedrop
./manage.py start
./manage.py add_admin
./manage.py test
```

## Staging

To just up a specific server run:

```
vagrant up app-staging
vagrant ssh app-staging
sudo su
cd /var/www/securedrop
./manage.py add_admin
./manage.py test
```

```
vagrant up mon-staging
vagrant ssh mon-staging
```

To have ansible add the ossec agent running on the app server to the ossec server running on the monitor server run these commands:

```
vagrant up /staging$/ --no-provision
ansible-playbook -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory --private-key ~/.vagrant.d/insecure_private_key --connection ssh -u vagrant install_files/ansible-base/site.yml
```

## Production

You will need to fill out the conf file `securedrop/install_files/ansible_base/prod-specific.yml`.

To just up a specific server run:

```
vagrant up app
vagrant ssh app
sudo su
cd /var/www/securedrop/
./manage.py add_admin
```

`vagrant up mon`

To have ansible add the ossec agent running on the app server to the ossec server running on the monitor server run these commands:
NOTE: you will need to temporarily disable the validate role to use the production playbooks with vagrant.

```
vagrant up app mon --no-provision
ansible-playbook -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory --private-key ~/.vagrant.d/insecure_private_key -u vagrant install_files/ansible-base/site.yml
```

In order to access the servers after the install is completed you will need to install and configure a proxy tool to proxy your SSH connection over Tor. Torify and connect-proxy are two tools that can be used to proxy SSH connections over Tor. You can find out the SSH addresses for each server by *TODO*

### connect-proxy (Ubuntu only)

Ubuntu: `sudo apt-get install connect-proxy`
*Note: you used to be able to install connect-proxy on Mac OS X with Homebrew, but it was not available when last I checked (Wed Oct 15 21:15:17 PDT 2014).*

After installing connect-proxy via apt-get, you can use something along the lines of the following example to access the server. Again you need Tor running in the background.

```
ssh admin1@examplenxu7x5ifm.onion -o ProxyCommand="/usr/bin/connect-proxy -5 -S localhost:9050 %h %p"
```

You can also configure your SSH client to make the settings for proxying over Tor persistent, and then connect using the regular SSH command syntax. Add the following lines to your `~/.ssh/config`:

```
Hosts *.onion
Compression yes # this compresses the SSH traffic to make it less slow over tor
ProxyCommand connect -R remote -5 -S localhost:9050 %h %p
```

This proxies all requests to `*.onion` address through connect-proxy, which will connect to the standard Tor SOCKS port on `localhost:9050`. You can now connect to the SSH hidden service with:

```
ssh admin@examplenxu7x5ifm.onion
```

### torify (Ubuntu and Mac OS X)

Ubuntu: torsocks should be installed by the tor package. If it is not installed, make sure you are using tor from the [Tor Project's repo](https://www.torproject.org/docs/debian.html.en), and not Ubuntu's package.
Mac OS X (Homebrew): `brew install torsocks`

If you have torify on your system (`$ which torify`) and you're Tor running in the background, simply prepend it to the SSH command:

```
torify ssh admin@examplenxu7x5ifm.onion
```


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

```
ansible --version
ansible 1.7.2
```

