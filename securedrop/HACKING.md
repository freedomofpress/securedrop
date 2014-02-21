development setup for securedrop
================================

1. Clone the repo
2. Make sure you have [vagrant](http://vagrantup.com) and [VirtualBox](http://www.virtualbox.org) installed
3. `vagrant up`

This creates a vm with the secure drop repository located in /vagrant.

You can ssh into it with `vagrant ssh`. To start the servers:

    $ cd /vagrant/securedrop
    $ python source.py &
    $ python journalist.py &

Now, you can visit SecureDrop (in your normal browser, Vagrant forwards the
ports from the VM) at [http://localhost:8080] and the journalist site at
[http://localhost:8081].

To run tests:

    $ cd /vagrant/securedrop
    $ ./test.sh

For more instructions on how to interact with your vm, refer to the [vagrant website](http://vagrantup.com).

