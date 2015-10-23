# Development Guide

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Prerequisites](#prerequisites)
  - [Ubuntu/Debian](#ubuntudebian)
  - [Mac OS X](#mac-os-x)
- [Clone the repository](#clone-the-repository)
- [Pick a development environment](#pick-a-development-environment)
  - [Development](#development)
  - [Staging](#staging)
  - [Prod](#prod)
    - [connect-proxy (Ubuntu only)](#connect-proxy-ubuntu-only)
    - [torify (Ubuntu and Mac OS X)](#torify-ubuntu-and-mac-os-x)
- [Tips & Tricks](#tips-&-tricks)
  - [Using Tor Browser with the development environment](#using-tor-browser-with-the-development-environment)
- [Version Notes](#version-notes)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Prerequisites

SecureDrop is a multi-machine design. To make development and testing easy, we provide a set of virtual environments, each tailored for a specific type of development task. We use Vagrant and Virtualbox to conveniently develop with a set of virtual environments, and our Ansible playbooks can provison these environments on either virtual machines or physical hardware.

To get started, you will need to install Vagrant, Virtualbox, and Ansible.

## Ubuntu/Debian

*Tested: Ubuntu 14.04*

```sh
sudo apt-get install -y dpkg-dev virtualbox-dkms linux-headers-$(uname -r) build-essential git
```

We recommend using the latest stable version of Vagrant (`1.7.4` at the time of
this writing), which might be newer than what is in the Ubuntu repositories.

If `apt-cache policy vagrant` says your candidate version is not at least
1.7, you should download the current version from
https://www.vagrantup.com/downloads.html and then install it.

```sh
sudo dpkg -i vagrant.deb    # if you downloaded vagrant.deb from vagrantup.com

sudo apt-get install vagrant    # OR this, if your OS vagrant is recent enough
```

We *do not* recommend using an older version of Vagrant older than 1.7 from
Ubuntu's package repositories. For instance, version 1.5.4 in Ubuntu
is significantly out of date and does not work with SecureDrop
([context](https://github.com/freedomofpress/securedrop/pull/932)).

```sh
sudo dpkg-reconfigure virtualbox-dkms
```

Finally, install Ansible so it can be used with Vagrant to automatically
provision VMs. We recommend installing Ansible with pip to ensure you have the
latest stable version.

```sh
sudo apt-get install python-pip
sudo pip install -U ansible
```

If you're using Ubuntu, you can install a sufficiently recent version of Ansible from backports (if you prefer): `sudo apt-get install ansible/trusty-backports`

*Tested: Ansible 1.8.4*

**Warning: for now, we do not recommend installing vagrant-cachier.** It destroys apt's state unless the VMs are always shut down/rebooted with Vagrant, which conflicts with the tasks in the Ansible playbooks. The instructions in Vagrantfile that would enable vagrant-cachier are currently commented out.

## Mac OS X

Install the requirements:

1. [Vagrant](http://www.vagrantup.com/downloads.html)
2. [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
3. [Ansible](http://docs.ansible.com/intro_installation.html). There are several
      ways to install Ansible on a Mac. We recommend using pip so you will get
      the latest stable version. To install Ansible via pip, `sudo easy_install
      pip && sudo pip install -U ansible`.

# Clone the repository

Once you've installed the prerequisites for the development environment, use git to clone the SecureDrop repo: `git clone https://github.com/freedomofpress/securedrop.git`. SecureDrop uses a branching model based on [git-flow](http://nvie.com/posts/a-successful-git-branching-model/). The `master` branch always points to the latest stable release. Use this branch if you are interested in installing or auditing SecureDrop. Development for the upcoming release of SecureDrop takes place on `develop`, which is the default branch. If you want to contribute, you should branch from and submit pull requests to `develop`.

# Pick a development environment

There are several predefined virtual environments in the Vagrantfile: development, staging, and prod (production).

* **development**: for working on the application code
    * Source Interface: localhost:8080
    * Document Interface: localhost:8081
* **app-staging**: for working on the environment and hardening
    * Source Interface: localhost:8082
    * Document Interface: localhost:8083
    * The interfaces and SSH are also available over Tor.
    * A copy of the the onion URLs for source, document and SSH access are written to the Vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
* **mon-staging**: for working on the environment and hardening
    * OSSEC alert configuration is in install_files/ansible-base/staging-specific.yml
* **app-prod**: This is like a production installation with all of the hardening applied but virtualized
    * A copy of the the onion URLs for source, document and SSH access are written to the Vagrant host's ansible-base directory. The files will be named: app-source-ths, app-document-aths, app-ssh-aths
    * Putting the AppArmor profiles in complain mode (default) or enforce mode can be done with the Ansible tags apparmor-complain or apparmor-enforce.
* **mon-prod**: This is like a production installation with all of the hardening applied but virtualized

If you plan to alter the configuration of any of these machines,
make sure to review the [Development Guide for Serverspec Tests](/docs/spec_tests.md).

## Development

This VM is intended for rapid development on the SecureDrop web application. It
syncs the `/vagrant` directory on the VM to the top level of the SecureDrop
repo, which means you can use your favorite editor on your host machine to edit
the code. This machine has no security hardening or monitoring.

This is the "default" VM, so you don't need to specify the `development` machine
name when running commands like `vagrant up` and `vagrant ssh`. Of course, you
can specify the name if you want to.

```
vagrant up
vagrant ssh
cd /vagrant/securedrop
./manage.py run         # run development servers
./manage.py test        # run the unit and functional tests
./manage.py reset       # resets the state of the development instance
./manage.py add_admin   # create a user to use when logging in to the Document Interface
```

SecureDrop consists of two separate web appications (the Source Interface and
the Document Interface) that run concurrently. The development servers will
detect code changes when they are saved and automatically reload.

## Staging

The staging environment is almost identical to the production, but the security
hardening is weakened slightly to allow direct access (without Tor) to SSH and
the web server. This is a convenient environment to test how changes work across
the full stack.

If you want to receive OSSEC alerts or change any other settings, you will need
to fill out your local copy of
`securedrop/install_files/ansible_base/staging-specific.yml`.

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
Part of the production playbook validates that staging values
are not used in production. One of the values it verifies is that the user
Ansible runs as is not `vagrant` To be able to run this playbook in a virtualized
environment for testing, you will need to disable the `validate` role, which you can
do by running `export SECUREDROP_PROD_SKIP_TAGS=validate` before provisioning.

To create only the prod servers, run:

```
vagrant up /prod$/
vagrant ssh app-prod
sudo su
cd /var/www/securedrop/
./manage.py add_admin
```

In order to access the servers after the install is completed you will need to install
and configure a proxy tool to proxy your SSH connection over Tor.
Torify and connect-proxy are two tools that can be used to proxy SSH connections over Tor.

### connect-proxy (Ubuntu only)

Ubuntu: `sudo apt-get install connect-proxy`
*Note: you used to be able to install connect-proxy
on Mac OS X with Homebrew, but it was not available last we checked (Wed Oct 15 21:15:17 PDT 2014).*

After installing connect-proxy via apt-get and appending the tor config options
to your local config, you can export the environment variable `SECUREDROP_SSH_OVER_TOR=1`
in order to use `vagrant ssh` commands to access the prod instances. Here is an example
of how that works:

```
$ vagrant up --provision /prod/     # restricts SSH to Tor after final reboot
$ vagrant ssh-config app-prod       # will show incorrect info due to lack of env var
Host app-prod
  HostName 127.0.0.1
  User vagrant
  Port 2201
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile /home/conor/.vagrant.d/insecure_private_key
  IdentitiesOnly yes
  LogLevel FATAL
$ vagrant ssh app-prod -c 'echo hello'   # will fail due to incorrect ssh-config
ssh_exchange_identification: read: Connection reset by peer
$ export SECUREDROP_SSH_OVER_TOR=1       # instruct Vagrant to use Tor for SSH
$ vagrant ssh-config app-prod            # will show correct info, with ProxyCommand
Host app-prod
  HostName l57xhqhltlu323vi.onion
  User vagrant
  Port 22
  UserKnownHostsFile /dev/null
  StrictHostKeyChecking no
  PasswordAuthentication no
  IdentityFile /home/conor/.vagrant.d/insecure_private_key
  IdentitiesOnly yes
  LogLevel FATAL
  ProxyCommand connect -R remote -5 -S 127.0.0.1:9050 %h %p
$ # ensure ATHS values are active in local Tor config:
$ cat *-aths | sudo tee -a /etc/tor/torrc > /dev/null && sudo service tor reload
$ vagrant ssh app-prod -c 'echo hello'   # works
hello
Connection to l57xhqhltlu323vi.onion closed.
```

If `SECUREDROP_SSH_OVER_TOR` is declared, Vagrant will look up the ATHS URLs
and `HidServAuth` values for each server by examining the contents of `app-ssh-aths`
and `mon-ssh-aths` in `./install_files/ansible-base`. You can manually inspect
these files to append values to your local `torrc`, as in the `cat` example above.
Note that the `cat` example above will also add the ATHS info for the
Document Interface, as well, which is useful for testing.

### torify (Ubuntu and Mac OS X)

Ubuntu: torsocks should be installed by the tor package. If it is not installed, make sure you are using tor from the [Tor Project's repo](https://www.torproject.org/docs/debian.html.en), and not Ubuntu's package.
Mac OS X (Homebrew): `brew install torsocks`

If you have torify on your system (`$ which torify`) and you're Tor running in the background, simply prepend it to the SSH command:

```
torify ssh admin@examplenxu7x5ifm.onion
```

# Tips & Tricks

## Using Tor Browser with the development environment

We strongly encourage sources to use the Tor Browser when they access the Source Interface. Tor Browser is the easiest way for the average person to use Tor without making potentially catastrophic mistakes, makes disable Javascript easy via the handy NoScript icon in the toolbar, and prevents state about the source's browsing habits (including their use of SecureDrop) from being persisted to disk.

Since Tor Browser is based on an older version of Firefox (usually the current ESR release), it does not always render HTML/CSS the same as other browsers (especially more recent versions of browsers). Therefore, we recommend testing all changes to the web application in the Tor Browser instead of whatever browser you normally use for web development. Unfortunately, it is not possible to access the local development servers by default, due to Tor Browser's proxy configuration.

To test the development environment in Tor Browser, you need to add an exception to allow Tor Browser to access localhost:

1. Open the "Tor Browser" menu and click "Preferences..."
2. Choose the "Advanced" section and the "Network" subtab under it
3. In the "Connection" section, click "Settings..."
4. In the text box labeled "No Proxy for:", enter `127.0.0.1`
    * Note: for some reason, `localhost` doesn't work here.
5. Click "Ok" and close the Preferences window

You should now be able to access the development server in the Tor Browser by navigating to `127.0.0.1:8080` and `127.0.0.1:8081`.

# Version Notes

This documentation has been tested and confirmed to work on:

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
