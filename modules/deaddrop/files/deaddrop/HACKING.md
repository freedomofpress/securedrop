development setup for deaddrop
==============================

This document assumes your development environment is a Debian, Ubuntu
or Fedora derivative.

If you're familiar with homebrew and pip on OSX you should be able to follow along. Secure RM
may already installed as srm.

install gnupg2:

    $ sudo yum install gnupg2
    $ sudo apt-get install gnupg2
    $ brew install gnupg2

install srm (secure remove utility):

    $ sudo yum install srm
    $ sudo apt-get install secure-delete

install virtualenv:

    $ sudo yum install python-virtualenv
    $ sudo apt-get install python-virtualenv
    $ pip install virtualenv

create and activate a new virtualenv:

    $ virtualenv ~/envs/deaddrop
    $ . ~/envs/deaddrop/bin/activate

install dependencies:

    $ sudo yum install python-devel
    $ sudo apt-get install python-dev
    $ pip install web.py python-gnupg python-bcrypt pycrypto beautifulsoup4 paste
    # or...
    $ pip install -r requirements.txt

cp the config template and fill in empty values:

    $ cp example_config.py config.py

**NOTE**: the `STORE_DIR` and `GPG_KEY_DIR` must be absolute paths.
Create them if necessary:

    $ mkdir -p /tmp/deaddrop/{store,keys}

**NOTE**: you will need to create a journalist key for development.

    $ gpg2 --homedir /tmp/deaddrop/keys --gen-key

Make sure you *only* use this key for development. We recommend using a userid
like "Deaddrop Dev (DO NOT USE IN PRODUCTION) <dev@deaddrop.example.com>" so
you don't forget!

Once you've generated the dev key, copy the userid to the `JOURNALIST_KEY`
field of `config.py`.

running
-------

At this point you should be able to directly invoke source or
journalist:

    $ python journalist.py
    $ python source.py

And browse to http://localhost:8080/ in your browser.
