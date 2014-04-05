# SecureDrop Tails Files

The recommended way for journalists to connect to the SecureDrop document interface is by using Tails. But to access it you need to edit your torrc file and restart tor each time you boot Tails. We've provided a program that makes this much simpler to do.

## Installation

Boot to your internet-connected Tails USB, making sure to mount the persistent volume. Also make sure to choose More Options at the Tails greeter and set a password (so you can use sudo). Connect to the internet.

Copy the securedrop folder to your home directory, or git clone it directly in tails.

Open a terminal and run:

    cd securedrop/tails_files/
    sudo ./install.sh

It will then ask for the password you set before. Type it and press enter.

A text editor window will pop up, editing the file `torrc_additions`. Add your HidServAuth line to the end of this file. When you're done, the file should look something like this, except with your owninformation: 

    # add HidServAuth lines here
    HidServAuth b6ferdazsj2v6agu.onion AHgaX9YrO/zanQmSJnILvB # client: journalist1

When you're done, save the document and close the text editor. Reboot Tails, and this time mount your persistent volume but don't set a password. 

## Usage

After you login to Tails, connect to the internet and wait until you connect to the Tor network. Then open your Persistence folder and double-click on `securedrop_init`. After that you can connect to your SecureDrop document interface. You have to do this once each time you login to Tails. 
