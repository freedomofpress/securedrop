<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Setup your local environment](#setup-your-local-environment)
  - [Ubuntu 14.04](#ubuntu-1404)
  - [Mac OS X](#mac-os-x)
- [Overview](#overview)
  - [Development](#development)
  - [Staging](#staging)
  - [Prod](#prod)
    - [connect-proxy (Ubuntu only)](#connect-proxy-ubuntu-only)
    - [torify (Ubuntu and Mac OS X)](#torify-ubuntu-and-mac-os-x)
  - [Version Notes](#version-notes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

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
* **app-prod**: This is like a production installation with all of the hardening applied but virtualized
    * A copy of the the Onion urls for source, document and ssh access are written to the vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
    * Putting the apparmor profiles in complain mode (default) or enforce mode can be done with the ansible tags apparmor-complain or apparmor-enforce.
* **mon-prod**: This is a like production installation with all of the hardening applied but virtualized


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

The staging environment is a virtual production server that still allows direct access. (you can ssh and hit the web interfaces directly without tor)

If you uncomment the line in the Vagrantfile `ansible.skip-tags: [ 'install_local_pkgs' ]` the playbook will look for:

securedrop-app-code-0.3-amd64.deb

securedrop-ossec-server-0.3-amd64.deb

securedrop-ossec-agent-0.3-amd64.deb

```
vagrant up /staging$/
vagrant ssh app-staging
sudo su
cd /var/www/securedrop
./manage.py add_admin
./manage.py test
```

## Prod

You will need to fill out the conf file `securedrop/install_files/ansible_base/prod-specific.yml`.

To just up a specific server run:

```
vagrant up /prod$/
vagrant ssh app-prod
sudo su
cd /var/www/securedrop/
./manage.py add_admin
```

NOTE: The demo instance run the production playbooks (only difference being the production installs are not virtualized).
Part of the production playbook validates that staging values are not used in production. One of the values it verifies is that the user ansible runs as is not `vagrant` To be able to run this playbook in a vagrant/virtualbox environment you will need to disable the validate role.

```
vagrant up /demo$/ --no-provision
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

