# The SecureDrop Development Community

You can subscribe to our mailing list here: [securedrop-dev](https://lists.riseup.net/www/subscribe/securedrop-dev). Or join is in #securedrop-dev on [irc.oftc.net](http://www.oftc.net/).

# Hacking on the Code

Install [Vagrant](http://vagrantup.com) and [VirtualBox](http://www.virtualbox.org), clone the git repository, and start vagrant:

	git clone https://github.com/freedomofpress/securedrop.git
	cd securedrop
	vagrant up

This creates a virtual machine with the SecureDrop codebase in /vagrant. You can edit files on your host machine in your favorite editor, and restart the web servers in the VM to test your changes.

You can ssh into the VM by typing `vagrant ssh`.

SecureDrop consists of two related web applications, one for sources and one for journalists. You can start the web servers from within the VM with:

    cd /vagrant/securedrop
    python source.py &
    python journalist.py &

Now you can visit SecureDrop by loading [http://localhost:8080] for the source interface and [http://localhost:8081] for the journalist interface in your web browser.

To run tests:

	cd /vagrant/securedrop
	./test.sh

For more instructions on how to interact with your VM, refer to the [Vagrant website](http://vagrantup.com).

