development setup for securedrop
================================

the easy way
------------

If you running Ubuntu/Debian, use the `setup_ubuntu.sh`. Note that this script leads to build errors if you are using Percona instead of standard MySQL.

1. Clone the repo
2. cd into `securedrop`
3. `./setup_ubuntu.sh`

the hard way
------------

This document assumes your development environment is a Debian, Ubuntu or
Fedora derivative.

If you're familiar with homebrew and pip on OSX you should be able to follow
along. Secure RM may already installed as srm.

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

    $ virtualenv ~/envs/securedrop
    $ . ~/envs/securedrop/bin/activate

Clone the repository if you haven't already:

    $ git clone https://github.com/freedomofpress/securedrop.git

cd into the repo, then cd into `securedrop`

install dependencies:

    $ sudo yum install python-devel
    $ sudo apt-get install python-dev libmysqlclient-dev phantomjs
    $ pip install --upgrade distribute
    $ pip install -r source-requirements.txt
    $ pip install -r document-requirements.txt
    $ pip install -r test-requirements.txt

cp the config templates and fill in empty values:

    $ cp config/base.py.example config/base.py
    $ cp config/development.py.example config/development.py
    $ cp config/test.py.example config/test.py

Create the `STORE_DIR` and `GPG_KEY_DIR`:

    $ mkdir -p .securedrop/{store,keys,tmp}

By default, all files storing the state of the application are saved under
`.securedrop/`. This directory is included in `.gitignore` by default.

**NOTE**: you will need to create a journalist key for development.

    $ gpg2 --homedir .securedrop/keys --gen-key

**Alternatively**, you can just import the GPG key that is included for the
tests to use in development:

    $ gpg2 --homedir .securedrop/keys --import test_journalist_key.*

Make sure you *only* use this key for development. If you genereate it, we
recommend choosing a userid like "SecureDrop Development (DO NOT USE IN
PRODUCTION)" so you don't forget!

Once you have the dev keypair, copy the key fingerprint to the `JOURNALIST_KEY`
field of `config/development.py`. You can find the key fingerprint by running:

    $ gpg2 --homedir .securedrop/keys --fingerprint

You might have to manually remove the spaces.

populate the database:

    $ python -c 'import db; db.create_tables()'

running
-------

At this point you should be able to directly invoke source or
journalist:

    $ python journalist.py
    $ python source.py

And browse to http://localhost:8080/ in your browser for the source interface,
or http://localhost:8081/ for the journalist interface.
