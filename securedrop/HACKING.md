development setup for securedrop
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

    $ virtualenv ~/envs/securedrop
    $ . ~/envs/securedrop/bin/activate

Clone the repository if you haven't already:

    $ git clone https://github.com/freedomofpress/securedrop.git

cd into the repo, then cd into `deaddrop` (we know, we still need to change the names :)

install dependencies:

    $ sudo yum install python-devel
    $ sudo apt-get install python-dev
    $ pip install --upgrade distribute
    $ pip install -r requirements.txt

cp the config template and fill in empty values:

    $ cp example_config.py config.py

**NOTE**: the `STORE_DIR` and `GPG_KEY_DIR` must be absolute paths.
Create them if necessary:

    $ mkdir -p /tmp/securedrop/{store,keys}

**FYI**: most OS's erase `/tmp` on reboot. I'm working on a script to do all of
this crap automatically, and might encourage putting these elsewhere for
development. Otherwise you have to recreate the dirs and re-import the keys
(below) after every reboot. **Alternatively**, you can just import the GPG key
that is included for the tests to use in development:

    $ gpg2 --homedir /tmp/deaddrop/keys --import test_journalist_key.*

**NOTE**: you will need to create a journalist key for development.

    $ gpg2 --homedir /tmp/securedrop/keys --gen-key

Make sure you *only* use this key for development. We recommend using a userid
like "securedrop Dev (DO NOT USE IN PRODUCTION) <dev@securedrop.example.com>" so
you don't forget!

Once you have the dev keypair, copy the key fingerprint to the `JOURNALIST_KEY`
field of `config.py`. You can find the key fingerprint by running:

    $ gpg2 --homedir /tmp/securedrop/keys --fingerprint

You might have to manually remove the spaces.

running
-------

At this point you should be able to directly invoke source or
journalist:

    $ python journalist.py
    $ python source.py

And browse to http://localhost:8080/ in your browser.
