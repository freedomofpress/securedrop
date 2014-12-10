# The SecureDrop Development Community

You can subscribe to our mailing list here: [securedrop-dev](https://lists.riseup.net/www/subscribe/securedrop-dev). Or join is in #securedrop-dev on [irc.oftc.net](http://www.oftc.net/).

# Hacking on the Code

The SecureDrop production environment runs Ubuntu trusty. In order to make it so all developers have as similar an environment as possible, we have made it easy to write and test code changes in trusty, even if that's not the operating system you're running.

The two ways to do this are using Vagrant or using a chroot jail. Vagrant works by creating Ubuntu VMs using VirtualBox and installing a development environment inside of them. Vagrant and VirtualBox are cross-platform, which means this method works in GNU/Linux, OS X, and Windows. However, it won't work if your development environment is already a VM, like if you run Qubes. It also might not work if you're using old hardware that doesn't support 64-bit virtualization. If you can't use Vagrant, you can use a chroot jail instead. Using a chroot jail only works if you're already running GNU/Linux.

## Vagrant and VirtualBox

Install [Vagrant](http://vagrantup.com), [VirtualBox](http://www.virtualbox.org), and [Ansible](http://docs.ansible.com/intro_installation.html). In GNU/Linux, you can probably install vagrant and ansible from your package manager, and add the VirtualBox repository to install virtualbox from your package manager.

Once Vagrant is installed, you also need to install the vagrant-hostmanager plugin.

```sh
vagrant plugin install vagrant-hostmanager
```

Now clone the repository and run `vagrant up` to start the Vagrant VMs.

```
git clone https://github.com/freedomofpress/securedrop.git
cd securedrop
vagrant up
```

This creates VMs with the SecureDrop codebase in /vagrant. You can edit files on your host machine in your favorite editor, and restart the web servers in the VM to test your changes.

You can ssh into the VM by typing `vagrant ssh`.

SecureDrop consists of two related web applications, one for sources and one for journalists. You can start the web servers from within the VM with:

```sh
cd /vagrant/securedrop
./manage.py start
```

Now you can visit SecureDrop by loading [http://localhost:8080] for the source interface and [http://localhost:8081] for the journalist interface in your web browser.

To run tests:

```sh
cd /vagrant/securedrop
./manage.py test
```sh

For more instructions on how to interact with your VM, refer to the [Vagrant website](http://vagrantup.com).



### Caching Vagrant

Sometimes you will find yourself destroying and provisioning your Vagrant VM frequently (usually to debug issues in `setup_dev.sh`). The installation process takes a while, and can quickly become an annoying time waster. To avoid this, install the vagrant-cachier plugin:

```sh
vagrant plugin install vagrant-cachier
```

This will cache packages from your next provision and use them in the future, making re-provisioning much, much faster. Installing the plugin is all you need to do, our Vagrantfile is set up to take advantage of it when it is available.

## Chroot Jail

First install the appropriate dependencies for your VM's OS:

```sh
sudo apt-get install debootstrap schroot
sudo yum install debootstrap schroot
```

You can use the script chroot-dev to setup and use your development environment.

```sh
git clone https://github.com/freedomofpress/securedrop.git
cd securedrop
./chroot-dev
```

This will show you a list of commands:

```
Usage: ./chroot-dev [command]

    up      # create chroot if needed, mount filesystems, start servers
    down    # stop servers, unmount filesystems from chroot
    start   # start securedrop web app servers
    stop    # stop securedrop web app servers
    restart # restart securedrop web app servers
    test    # run tests
    destroy # destroy chroot jail
```

All you need to do is run `./chroot-dev up`. The first time you do this it will take some time to install and configure your chroot development environment. In the future, all you have to do is run `./chroot-dev up` and you'll be ready to start working.

You can run tests with `./chroot-dev test`.

# Using manage.py

The `securedrop/manage.py` script is provied to help automate common tasks. At
the moment, the following commands are available:

* `start` - start the source and journalist servers
* `test` - run the test suite
* `reset` - reset the state of the development instance

    This is useful if you've changed the database schema and are getting
    errors, but don't want to bother with doing a migration.
