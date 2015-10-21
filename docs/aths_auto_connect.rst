Set up access to the authenticated hidden services
==================================================

To complete setup of the Admin Workstation, we recommend using the
scripts in ``tails_files`` to easily and persistently configure Tor to
access these hidden services.

Navigate to the directory with these scripts and type these commands
into the terminal:

::

    cd ~/Persistent/securedrop/tails_files/
    sudo ./install.sh

Type the administration password that you selected when starting Tails
and hit enter. The installation process will download additional
software and then open a text editor with a file called
*torrc\_additions*.

Edit this file, inserting the *HidServAuth* information for the three
authenticated hidden services that you just received. You can
double-click or use the 'cat' command to read the values from
``app-document-aths``, ``app-ssh-aths`` and ``mon-ssh-aths``. This
information includes the address of the Document Interface, each
server's SSH daemon and your personal authentication strings, like in
the example below:

::

    # add HidServAuth lines here
    HidServAuth gu6yn2ml6ns5qupv.onion Us3xMTN85VIj5NOnkNWzW # client: user
    HidServAuth fsrrszf5qw7z2kjh.onion xW538OvHlDUo5n4LGpQTNh # client: admin
    HidServAuth yt4j52ajfvbmvtc7.onion vNN33wepGtGCFd5HHPiY1h # client: admin

An easy way to do this is to run ``cat *-aths`` from the
``install_files/ansible-base`` folder in a terminal window, and
copy/paste the output into the opened text editor.

When you are done, click *Save* and **close** the text editor. Once the
editor is closed, the install script will automatically resume.

Running ``install.sh`` sets up an initialization script that
automatically updates Tor's configuration to work with the authenticated
hidden services every time you login to Tails. As long as Tails is
booted with the persistent volume enabled then you can open the Tor
Browser and reach the Document Interface as normal, as well as connect
to both servers via secure shell. Tor's `hidden service
authentication <https://www.torproject.org/docs/tor-manual.html.en#HiddenServiceAuthorizeClient>`__
restricts access to only those who have the 'HidServAuth' values.

Set up SSH host aliases
-----------------------

This step is optional but makes it much easier to connect to and
administer the servers. Create the file ``/home/amnesia/.ssh/config``
and add a configuration following the scheme below, but replace
``Hostname`` and ``User`` with the values specific to your setup:

::

    Host app
      Hostname fsrrszf5qw7z2kjh.onion
      User <ssh_user>
    Host mon
      Hostname yt4j52ajfvbmvtc7.onion
      User <ssh_user>

Now you can simply use ``ssh app`` and ``ssh mon`` to connect to each
server, and it will be stored in the Tails Dotfiles persistence.

Set up two-factor authentication for the Admin
----------------------------------------------

As part of the SecureDrop installation process, you will need to set up
two-factor authentication on the App Server and Monitor Server using the
Google Authenticator mobile app.

After your torrc has been updated with the HidServAuth values, connect
to the App Server using ``ssh`` and run ``google-authenticator``. Follow
the instructions in `our Google Authenticator
guide </docs/google_authenticator.md>`__ to set up the app on your
Android or iOS device.

To disconnect enter the command ``exit``. Now do the same thing on the
Monitor Server. You'll end up with an account for each server in the
Google Authenticator app that generates two-factor codes needed for
logging in.
