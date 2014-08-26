# Tails for the Journalist Workstation

This guide outlines the steps required to set up *Tails* on a *Transfer Device*, such as a USB stick, for use with the *Journalist Workstation*. The workstation will be used to connect to the *Document Interface*, download documents, and move them to the Secure Viewing Station using the Transfer Device.

When running commands or editing configuration files that include filenames, version numbers, admin or journalist names, make sure it all matches your setup.

## Install Tails on a Transfer Device

Instructions on how to download, verify and install the operating system onto a Transfer Device can be found on the [Tails website](https://tails.boum.org/download/index.en.html).

### Create an encrypted persistent volume

Creating an encrypted persistent volume will allow you to securely save information in the free space that is left on the Transfer Device. This information will remain available to you even if you reboot Tails. Instructions on how to create and use this volume can be found on the [Tails website](https://tails.boum.org/doc/first_steps/persistence/index.en.html). You will be asked to select persistence features, such as personal data. We recommend that you enable all features.

## Configure Tails for use with SecureDrop

Before you can set up Tails for use with the Journalist Workstation, make sure you have enabled the persistent volume and that you are connected to the Internet.

### Start Tails and enable the persistent volume

When starting Tails, you should see a *Welcome to Tails*-screen with two options. Select *Yes* to enable the persistent volume and enter your password. Select *Yes* to show more options and click *Forward*. Enter an *Administration password* for use with this current Tails session and click *Login*. Once you're logged in, connect the Tails machine to the Internet.

### Download and run the setup scripts

Open the terminal and run the following command to get the files required to set up Tails for use with the Journalist Workstation.

```
git clone https://github.com/freedomofpress/securedrop.git
```

Navigate to the directory with the setup scripts and begin the installation:

```
cd securedrop/tails_files/
sudo ./install.sh
```

Type the administration password that you selected when starting Tails and hit enter. The installation process will download additional software and then open a text editor with a file called *torrc_additions*. 

Edit the file with the *HidServAuth* information for your SecureDrop instance that you got during the [installation process](https://github.com/freedomofpress/securedrop/blob/develop/docs/install.md#finalize-the-installation-on-the-app-server). This information contains of the address to the Document Interface and your personal authentication string. The information from the installation guide results in the following:

```
# add HidServAuth lines here
HidServ Auth gu6yn2ml6ns5qupv.onion Us3xMTN85VIj5NOnkNWzW # client: bob
```

When you are done, click *Save* and close the text editor.

## Using Tails with the Journalist Workstation

To use Tails with the Journalist Workstation, start Tails and enable the persistent volume. You do not have to set a password. Connect to the Internet, then click on *Places* and select the *Persistent* folder. Double-click on *SecureDrop Init*. Once that's done, open the browser and connect to the Document Interface as normal. Keep in mind that you have to repeat this step every time you start Tails.

### Create bookmarks for Source and Document Interfaces

If you want, you can open the browser and create bookmarks for the Source and Document Interfaces. Navigate to the site you wish to bookmark, select *Bookmarks* and *Bookmark This Page*, give the site a useful name (e.g. *Source Interface*), and click *Done*. Tails will remember the bookmarks even if you reboot.
