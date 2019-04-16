Setting Up the Development Environment
======================================

.. include:: ../includes/docs-branches.txt

Prerequisites
-------------

SecureDrop is a multi-machine design. To make development and testing
easy, we provide a set of virtual environments, each tailored for a
specific type of development task. We use Vagrant, VirtualBox, and
Docker and our Ansible playbooks can provision these environments on
either virtual machines or physical hardware.

.. note:: SecureDrop is written in Python 2. We plan to migrate to Python 3
          in a future release. 

Quick Start
-----------

The Docker based environment is suitable for developing the web application
and updating the documentation.


Ubuntu or Debian GNU/Linux
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: sh

   sudo apt-get update
   sudo apt-get install -y make git

We recommend using the stable version of Docker CE (Community Edition) which can
be installed via the official documentation links:

* `Docker CE for Ubuntu`_
* `Docker CE for Debian`_

Make sure to follow the `Post-installation steps for Linux`_, as well.

.. _`Docker CE for Ubuntu`: https://docs.docker.com/install/linux/docker-ce/ubuntu/
.. _`Docker CE for Debian`: https://docs.docker.com/install/linux/docker-ce/debian/
.. _`Post-installation steps for Linux`: https://docs.docker.com/install/linux/linux-postinstall/

macOS
~~~~~

Install Docker_.

.. _Docker: https://store.docker.com/editions/community/docker-ce-desktop-mac


Qubes
~~~~~

Create a StandaloneVM based on Debian 9, called ``sd-dev``.
You can use the **Q** menu to configure a new VM, or run
the following in ``dom0``:

.. code:: sh

   qvm-clone --class StandaloneVM debian-9 sd-dev
   qvm-start sd-dev
   qvm-sync-appmenus sd-dev

The commands above will created a new StandaloneVM, boot it, then update
the Qubes menus with applications within that VM. Open a terminal in
``sd-dev``, and proceed with installing `Docker CE for Debian`_.

Fork & Clone the Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now you are ready to get your own copy of the source code.
Visit our repository_ fork it and clone it on you local machine:


.. code:: sh

   git clone git@github.com:<your_github_username>/securedrop.git

Using the Docker Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Docker based helpers are intended for rapid development on the
SecureDrop web application and documentation. They use Docker images
that contain all the dependencies required to run the tests, a demo
server etc.

.. tip:: When run for the first time, building Docker images will take
         a few minutes, even one hour when your Internet connection is
         not fast. If you are unsure about what happens, you can get a
         more verbose output by setting the environment
         variable ``export DOCKER_BUILD_VERBOSE=true``.

The SecureDrop repository is bind mounted into the
container and files modified in the container are also modified in the
repository. This container has no security hardening or monitoring.

To get started, you can try the following:

.. code:: sh

   cd securedrop/securedrop
   make dev                                    # run development servers
   make test                                   # run tests
   bin/dev-shell bin/run-test tests/functional # functional tests only
   bin/dev-shell bash                          # shell inside the container

To specify the version of Python you want to use, set the ``PYTHON_VERSION``
environmental variable, like so:

.. code:: sh

    PYTHON_VERSION=3 make test    # Run tests on Python 3
    PYTHON_VERSION=2 make test    # Run tests on Python 2
    PYTHON_VERSION=3 make dev     # Run dev container on Python 3
    PYTHON_VERSION=2 make dev     # Run dev container on Python 2

.. tip:: The interactive shell in the container does not run
         ``redis``, ``Xvfb`` etc.  However you can import shell helper
         functions with ``source bin/dev-deps`` and call ``run_xvfb``,
         ``maybe_create_config_py`` etc.

SecureDrop consists of two separate web applications (the Source Interface and
the *Journalist Interface*) that run concurrently. In the development environment
they are configured to detect code changes and automatically reload whenever a
file is saved. They are made available on your host machine by forwarding the
following ports:

* Source Interface: `localhost:8080 <http://localhost:8080>`__
* *Journalist Interface*: `localhost:8081 <http://localhost:8081>`__

A test administrator (``journalist``) and non-admin user (``dellsberg``) are
created by default when running ``make dev``. In addition, sources and
submissions are present. The test users have the following credentials. Note that
the password and TOTP secret are the same for both accounts for convenience during
development.

* **Username:** ``journalist`` or ``dellsberg``
* **Password:** ``correct horse battery staple profanity oil chewy``
* **TOTP secret:** ``JHCO GO7V CER3 EJ4L``

If you need to generate the six digit token, use the TOTP secret in
combination with an authenticator application that implements
`RFC 6238 <https://tools.ietf.org/html/rfc6238>`__, such as
`FreeOTP <https://freeotp.github.io/>`__ (Android and iOS) or
`oathtool <http://www.nongnu.org/oath-toolkit/oathtool.1.html>`__
(command line tool, multiple platforms). Instead of typing the TOTP code, you
can simply scan the following QR code:

.. image:: ../images/devenv/test-users-totp-qrcode.png

You can also generate the 2FA code using the Python interpreter:

.. code:: python

  >>> import pyotp
  >>> pyotp.TOTP('JHCOGO7VCER3EJ4L').now()
  u'422038'

.. _multi_machine_environment:

Setting Up a Multi-Machine Environment
--------------------------------------

.. note:: You do not need this step if you only plan to work on the
   web application or the documentation.

To get started, you will need to install Vagrant, VirtualBox, Docker, and
Ansible on your development workstation.


Ubuntu or Debian GNU/Linux
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note:: Tested on: Ubuntu 16.04 and Debian GNU/Linux stretch

.. code:: sh

   sudo apt-get update
   sudo apt-get install -y build-essential libssl-dev libffi-dev python-dev \
       dpkg-dev git linux-headers-$(uname -r) virtualbox

We recommend using the latest stable version of Vagrant, ``1.8.5`` at the time
of this writing, which might be newer than what is in your distro's package
repositories. Older versions of Vagrant has been known to cause problems
(`GitHub #932`_, `GitHub #1381`_). If ``apt-cache policy vagrant`` says your
candidate version is not at least 1.8.5, you should download the current version
from the `Vagrant Downloads page`_ and then install it.

.. code:: sh

    # If your OS vagrant is recent enough
    sudo apt-get install vagrant
    # OR this, if you downloaded the deb package.
    sudo dpkg -i vagrant.deb

.. _`Vagrant Downloads page`: https://www.vagrantup.com/downloads.html
.. _`GitHub #932`: https://github.com/freedomofpress/securedrop/pull/932
.. _`GitHub #1381`: https://github.com/freedomofpress/securedrop/issues/1381

.. warning:: We do not recommend installing vagrant-cachier. It destroys apt’s
            state unless the VMs are always shut down/rebooted with Vagrant,
            which conflicts with the tasks in the Ansible playbooks. The
            instructions in Vagrantfile that would enable vagrant-cachier are
            currently commented out.

VirtualBox should be at least version 5.x. See `GitHub #1381`_ for documentation
of incompatibility with the older VirtualBox 4.x release series.

Finally, install Ansible so it can be used with Vagrant to automatically
provision VMs. We recommend installing Ansible from PyPi with ``pip`` to ensure
you have the latest stable version.

.. code:: sh

    sudo apt-get install python-pip

The version of Ansible recommended to provision SecureDrop VMs may not be the
same as the version in your distro's repos, or may at some point flux out of
sync. For this reason, and also just as a good general development practice, we
recommend using a Python virtual environment to install Ansible and other
development-related tooling. Using `virtualenvwrapper
<http://virtualenvwrapper.readthedocs.io/en/stable/>`_:

.. code:: sh

    sudo apt-get install virtualenvwrapper
    source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
    mkvirtualenv -p /usr/bin/python2 securedrop

.. note:: You'll want to add the command to source ``virtualenvwrapper.sh``
          to your ``~/.bashrc`` (or whatever your default shell configuration
          file is) so that the command-line utilities ``virtualenvwrapper``
          provides are automatically available in the future.

macOS
~~~~~

Install the dependencies for the development environment:

#. Vagrant_
#. VirtualBox_
#. Ansible_
#. rsync >= 3.1.0

If you use homebrew-cask_ to manage macOS apps, you can install Vagrant and
VirtualBox that way. As for Ansible, we strongly recommend installing it
in a virtual environment using ``virtualenvwrapper`` and ``pip``, so as not to
install the older version we use system-wide. The following commands assume your
default Python is the Python 2 that ships with macOS. If you are using a
different version, the path to ``virtualenvwrapper.sh`` will differ. Running
``pip show virtualenvwrapper`` should help you find it.

.. code:: sh

    sudo easy_install pip # if you don't already have pip
    sudo -H pip install -U virtualenvwrapper --ignore-installed six
    source /usr/local/bin/virtualenvwrapper.sh
    mkvirtualenv -p python securedrop

.. note:: You'll want to add the command to source ``virtualenvwrapper.sh``
          to your ``~/.bashrc`` (or whatever your default shell configuration
          file is) so that the command-line utilities ``virtualenvwrapper``
          provides are automatically available in the future.
          
The version of rsync installed by default on macOS is extremely out-of-date, as is Apple's custom. We recommend using Homebrew_ to install a modern version (3.1.0 or greater): ``brew install rsync``.

.. _Vagrant: http://www.vagrantup.com/downloads.html
.. _VirtualBox: https://www.virtualbox.org/wiki/Downloads
.. _Ansible: http://docs.ansible.com/intro_installation.html
.. _Homebrew: https://brew.sh/
.. _homebrew-cask: http://sourabhbajaj.com/mac-setup/Vagrant/README.html

Fork & Clone the Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now you are ready to get your own copy of the source code.
Visit our repository_ fork it and clone it on you local machine:


.. code:: sh

   git clone git@github.com:<your_github_username>/securedrop.git

.. _repository: https://github.com/freedomofpress/securedrop

Install Python Requirements
~~~~~~~~~~~~~~~~~~~~~~~~~~~

SecureDrop uses many third-party open source packages from the python community.
Ensure your virtualenv is activated and install the packages.

.. code:: sh

    pip install -r securedrop/requirements/develop-requirements.txt

.. note:: You will need to run this everytime new packages are added.
