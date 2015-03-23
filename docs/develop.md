# Development Guide

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Setup your local environment](#setup-your-local-environment)
  - [Ubuntu/Debian](#ubuntudebian)
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

## Ubuntu/Debian

*Tested on Ubuntu 14.04*

```sh
sudo apt-get install -y dpkg-dev virtualbox-dkms linux-headers-$(uname -r) build-essential git
git clone https://github.com/freedomofpress/securedrop
cd securedrop
```

We recommend using the latest stable version of Vagrant, which is newer than what is in the Ubuntu repositories at the time of this writing.
Download the current version from https://www.vagrantup.com/downloads.html *(Tested with vagrant 1.7.2)*

```sh
sudo dpkg -i vagrant.deb
sudo dpkg-reconfigure virtualbox-dkms
```

Finally, install Ansible so it can be used with Vagrant to automatically provision VMs.

Generally, we recommend you install Ansible using pip, which will ensure you have the latest stable version.

```sh
sudo pip install ansible
sudo apt-get install python-pip
```

If you're using Ubuntu, you can install a sufficiently recent version of Ansible from backports (if you prefer): `sudo apt-get install ansible/trusty-backports`

*Tested: Ansible 1.8.4*

**Warning: for now, we do not recommend installing vagrant-cachier.** It destroys apt's state unless the VMs are always shut down/rebooted with Vagrant, which conflicts with the tasks in the Ansible playbooks. The instructions in Vagrantfile that would enable vagrant-cachier are currently commented out.

## Mac OS X

First, install the requirements:

1. [Vagrant](http://www.vagrantup.com/downloads.html)
2. [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
3. [Ansible](http://docs.ansible.com/intro_installation.html)
    * There are several ways to install Ansible on a Mac. We recommend using
      pip instead of homebrew so you will get the latest stable version. To
      install Ansible via pip,

      ```sh
      sudo easy_install pip
      sudo pip install ansible
      ```

Now you're ready to use vagrant to provision SecureDrop VMs!


# Overview

There are predefined VM configurations in the vagrantfile: development, staging, app and mon (production).

* **development**: for working on the application code
    * Source Interface: localhost:8080
    * Document Interface: localhost:8081
* **app-staging**: for working on the environment and hardening
    * Source Interface: localhost:8082
    * Document Interface: localhost:8083
    * The interfaces and SSH are also available over Tor and direct access.
    * A copy of the the onion URLs for source, document and SSH access are written to the Vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
* **mon-staging**: for working on the environment and hardening
    * OSSEC alert configuration is in install_files/ansible-base/staging-specific.yml
* **app-prod**: This is like a production installation with all of the hardening applied but virtualized
    * A copy of the the onion URLs for source, document and SSH access are written to the Vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
    * Putting the AppArmor profiles in complain mode (default) or enforce mode can be done with the Ansible tags apparmor-complain or apparmor-enforce.
* **mon-prod**: This is like a production installation with all of the hardening applied but virtualized


## Development

```
vagrant up
vagrant ssh development
cd /vagrant/securedrop
./manage.py test        # run the unit and functional tests
./manage.py start       # starts the application servers
./manage.py stop        # stops the application servers
./manage.py restart     # restarts the application servers (to test code changes)
./manage.py reset       # resets the state of the development instance
./manage.py add_admin   # create a user to use when logging in to the Document Interface
```

## Staging

The staging environment is a virtual production server that still allows direct access. (you can SSH and hit the web interfaces directly without Tor)

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

You will need to fill out the configuration file `securedrop/install_files/ansible_base/prod-specific.yml`.

To just spawn a specific server run:

```
vagrant up /prod$/
vagrant ssh app-prod
sudo su
cd /var/www/securedrop/
./manage.py add_admin
```

NOTE: The demo instance runs the production playbooks (only difference being the production installs are not virtualized).
Part of the production playbook validates that staging values are not used in production. One of the values it verifies is that the user Ansible runs as is not `vagrant` To be able to run this playbook in a Vagrant/VirtualBox environment you will need to disable the 'validate' role.

```
vagrant up /demo$/ --no-provision
ansible-playbook -i .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory --private-key ~/.vagrant.d/insecure_private_key -u vagrant install_files/ansible-base/site.yml
```

In order to access the servers after the install is completed you will need to install and configure a proxy tool to proxy your SSH connection over Tor. Torify and connect-proxy are two tools that can be used to proxy SSH connections over Tor. You can find out the SSH addresses for each server by examining the contents of `app-ssh-aths` and `mon-ssh-aths` in `/install_files/ansible-base`. Also you must add the HidServAuth values to your `/etc/tor/torrc` file and reload Tor.

### connect-proxy (Ubuntu only)

Ubuntu: `sudo apt-get install connect-proxy`
*Note: you used to be able to install connect-proxy on Mac OS X with Homebrew, but it was not available last we checked (Wed Oct 15 21:15:17 PDT 2014).*

After installing connect-proxy via apt-get, you can use something along the lines of the following example to access the server. Again you need Tor running in the background.

```
ssh admin1@examplenxu7x5ifm.onion -o ProxyCommand="/usr/bin/connect-proxy -5 -S localhost:9050 %h %p"
```

You can also configure your SSH client to make the settings for proxying over Tor persistent, and then connect using the regular SSH command syntax. Add the following lines to your `~/.ssh/config`:

```
Hosts *.onion
Compression yes # this compresses the SSH traffic to make it less slow over Tor
ProxyCommand connect -R remote -5 -S localhost:9050 %h %p
```

This proxies all requests to *.onion addresses through connect-proxy, which will connect to the standard Tor SOCKS port on `localhost:9050`. You can now connect to the SSH hidden service with:

```
ssh <username>@examplenxu7x5ifm.onion
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
Vagrant 1.7.2
```

```
vagrant-hostmanager (1.5.0)
vagrant-login (1.0.1, system)
vagrant-share (1.1.3, system)
```

```
ansible --version
ansible 1.8.4
```
