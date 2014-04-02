# SecureDrop Tails Files

The recommended way for journalists to connect to the SecureDrop document interface is by using Tails. But to access it you need to edit your torrc file and restart tor each time you boot Tails. We've provided a program that makes this much simpler to do.

## Installation

Boot to your internet-connected Tails USB, making sure to mount the persistent volume. Also make sure to choose More Options at the Tails greeter and set a password (so you can use sudo).

Copy the `tails_files` folder to a USB stick and mount it in Tails. To make the instructions simpler, copy the `tails_files` to your home directory, `/home/amnesia/`.

Open a terminal and run:

    cd tails_files
    sudo ./install.sh

It will then ask for the password you set before. Type it and press enter.

A text editor window will pop up, editing the file `.torrc.additions`. Add your HidServAuth line to the end of this file. When you're done, the file should look something like this, except with your owninformation: 

    # add HidServAuth lines here
    HidServAuth b6ferdazsj2v6agu.onion AHgaX9YrO/zanQmSJnILvB # client: journalist1

When you're done, save the document and close the text editor. Reboot Tails, and this time mount your persistent volume but don't set a password. 

## Usage

After you login to Tails, connect to the internet and wait until you connect to the Tor network. Then open your Persistence folder and double-click on `update-torrc`. After that you can connect to your SecureDrop document interface. You have to do this once each time you login to Tails. 

## Background

In SecureDrop, the document interface is an authenticated Tor hidden service, which means users need to edit their /etc/tor/torrc file and add a HidServAuth line, and reload torrc before they'll be able to connect. But since Tails is non-persistent they'll need to do this every single time they boot Tails, and they'll also need to set a password so they can do things as root. Clearly this isn't very user friendly.

This is a simple C program that aims to fix this problem. It looks at /home/amnesia/Persistent/.torrc.additions and appends it to the end of /etc/tor/torrc and reloads torrc. For this to work as the amnesia user, you need to make update_torrc owned by root and executable by all with the setuid flag. Now any user that runs this will be effectively running as the root user (without needing to be a sudoer or have a user password set). The reason I wrote this in C instead of something way simpler, like bash, is the setuid flag only works compiled programs, not scripts. 

## Compiling Yourself

If you'd prefer to compile update_torrc from source, after you have copied the `tails_files` folder to your home directory, open a terminal and run this:

    sudo apt-get install build-essential
    cd tails_files
    sudo ./build.sh

After you've compiled your own update_torrc binary, re-run the installation instructions from above.
