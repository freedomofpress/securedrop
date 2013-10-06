development setup for deaddrop
==============================

This document assumes your development environment is a Debian, Ubuntu
or Fedora derivative.  If you're familiar with homebrew on OSX you
should be able to follow along (documentation patches welcome).

install gnupg2:
    $ sudo yum install gnupg2
    $ sudo apt-get install gnupg2

install virtualenv:

	$ sudo yum install python-virtualenv
	$ sudo apt-get install python-virtualenv

create and activate a new virtualenv:

	$ virtualenv ~/envs/deaddrop
	$ . ~/envs/deaddrop/bin/activate

install dependencies:

	$ pip install web.py python-gnupg python-bcrypt pycrypto

install srm (secure remove utility):

	$ sudo yum install srm
	$ sudo apt-get install secure-delete

use the example config:

	$ ln -s example_config.py config.py

**NOTE**: the STORE_DIR and GPG_KEY_DIR must be absolute paths.
Ensure they exist:

       $ mkdir -p /tmp/deaddrop/{store,keys}

running
-------

At this point you should be able to directly invoke source or
journalist:

	$ python journalist.py
	$ python source.py

And browse to http://localhost:8080/ in your browser.
