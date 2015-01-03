# Tails Guide

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**  *generated with [DocToc](http://doctoc.herokuapp.com/)*

- [Installing Tails on USB sticks](#installing-tails-on-usb-sticks)
  - [Note for Mac OS X users](#note-for-mac-os-x-users)
- [Configure Tails for use with SecureDrop](#configure-tails-for-use-with-securedrop)
  - [Persistence](#persistence)
  - [Start Tails and enable the persistent volume](#start-tails-and-enable-the-persistent-volume)
  - [Download the repository](#download-the-repository)
  - [Passphrase Database](#passphrase-database)
  - [Set up easy access to the Document Interface](#set-up-easy-access-to-the-document-interface)
  - [Using Tails with the Workstation](#using-tails-with-the-workstation)
    - [Create bookmarks for Source and Document Interfaces](#create-bookmarks-for-source-and-document-interfaces)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# Installing Tails on USB sticks

Tails is a live operating system that is run from removable media, such as a DVD or a USB stick. For SecureDrop, you'll need to install Tails onto USB sticks and enable persistent storage.

We recommend creating an initial Tails Live USB or DVD, and then using that to create additional Tails Live USBs with the *Tails Installer*, a special program that is only available from inside Tails. *You will only be able to create persistent volumes on USB sticks that had Tails installed via the Tails Installer*.

The [Tails website](https://tails.boum.org/) has detailed and up-to-date instructions on how to download and verify Tails, and how to create a Tails USB stick. Here are some links to help you out:

* [Download and verify the Tails .iso](https://tails.boum.org/download/index.en.html)
* [Install onto a USB stick or SD card](https://tails.boum.org/doc/first_steps/installation/index.en.html)
* [Create & configure the persistent volume](https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html)

## Note for Mac OS X users

The tails documentation for "manually installing" Tails onto a USB device for Mac OS X include the following `dd` invocation to copy the .iso to the USB:

```
dd if=[tails.iso] of=/dev/diskX
```

This command is *very slow* (in our testing, it takes about 18 minutes to copy the .iso to a USB 2.0 drive). You can speed it up by adding the following arguments to `dd`:

```
dd if=[tails.iso] of=/dev/rdiskX bs=1m
```

Note the change from `diskX` to `rdiskX`. This reduced the copy time to 3 minutes for us. For an explanation, defer to the relevant [Server Fault post](http://superuser.com/questions/421770/dd-performance-on-mac-os-x-vs-linux) ("I believe it has to do with buffers"). If you have GNU coreutils installed (such as through Homebrew), you may need to capitalize the M suffixed to the `bs` value.

# Configure Tails for use with SecureDrop

## Persistence

Creating an encrypted persistent volume will allow you to securely save information in the free space that is left on the Transfer Device. This information will remain available to you even if you reboot Tails. Instructions on how to create and use this volume can be found on the [Tails website](https://tails.boum.org/doc/first_steps/persistence/index.en.html). You will be asked to select from a list of persistence features, such as personal data. We recommend that you enable **all** features.

## Start Tails and enable the persistent volume

When starting Tails, you should see a *Welcome to Tails*-screen with two options. Select *Yes* to enable the persistent volume and enter your password. Select *Yes* to show more options and click *Forward*. Enter an *Administration password* for use with this current Tails session and click *Login*.

If you're setting up the Secure Viewing Station, stop here. You're done. Otherwise, once you're logged in, connect the Tails machine to the Internet.

## Download the repository

The rest of the SecureDrop-specific configuration is assisted by files stored in the SecureDrop git repository. To get started, open a terminal and run the following commands to download the git repository. Note that since the repository is fairly large and Tor can be slow, this may take a few minutes.

```sh
cd ~/Persistent
git clone https://github.com/freedomofpress/securedrop.git
```

## Passphrase Database

As mentioned in the installation documentation, we provide a KeePassX password database template to make it easier for admins and journlists to generate strong, unique passphrases and store the securely. Once you have set up Tails with persistence and have cloned the repo, you can set up your personal password database using this template.

You can find the template in `tails_files/securedrop-keepassx.xml` inside the securedrop repository. Note that you will not be able to access your passwords if you forget the master password, or the location of the key file, used to protect the database.

To use the template:

 * Open the KeePassX program
 * Select `File`, `Import from...`, and `KeePassX XML (*.xml)`
 * Navigate to the location of `securedrop-keepassx.xml`, select it, and click `Open`
 * Set a strong master password or choose a key file to protect the password database
 * Click `File` and `Save Database As`
 * Save the database in the Tails Persistent folder

## Set up easy access to the Document Interface

If this is an Admin Workstation or Journalist Workstation, we recommend using the scripts in `tails_files` to easily configure Tor to access the Document Interface.

Navigate to the directory with the setup scripts and begin the installation:

```
cd securedrop/tails_files/
sudo ./install.sh
```

Type the administration password that you selected when starting Tails and hit enter. The installation process will download additional software and then open a text editor with a file called *torrc_additions*.

Edit the file, inserting the *HidServAuth* information for your SecureDrop instance that you received during the installation process. The values can be found in `install_files/ansible-base/app-document-aths`. This information includes the address to the Document Interface and your personal authentication string, as seen in the example below:

```
# add HidServAuth lines here
HidServAuth gu6yn2ml6ns5qupv.onion Us3xMTN85VIj5NOnkNWzW # client: bob
```

If you're working on the Admin Workstation, you should also insert the lines found in `app-ssh-aths` and `mon-ssh-aths`, which will allow you to connect using a secure shell over Tor to the App and Monitor Servers. When you are done, click *Save* and close the text editor.

## Using Tails with the Workstation

To use Tails with the Workstation, start Tails and enable the persistent volume. You do not have to set a password. Connect to the Internet, then click on *Places* and select the *Persistent* folder. Double-click on *SecureDrop Init*. Once that's done, open the browser and connect to the Document Interface as normal. You will need to remember to repeat this step every time you start Tails.

### Create bookmarks for Source and Document Interfaces

If you want, you can open the browser and create bookmarks for the Source and Document Interfaces. Navigate to the site you wish to bookmark, select *Bookmarks* and *Bookmark This Page*, give the site a useful name (e.g. *Source Interface*), and click *Done*. Tails will remember the bookmarks even if you reboot.
