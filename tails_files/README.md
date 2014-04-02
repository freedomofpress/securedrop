# securedrop-torrc

The recommended way for journalists to connect to their [SecureDrop](https://github.com/freedomofpress/securedrop) document interface is by using Tails. But the document interface is an authenticated Tor hidden service, which means they need to edit their /etc/tor/torrc file, and add a HidServAuth line, and reload torrc before they'll be able to connect. But since Tails is non-persistent they'll need to do this every single time they boot Tails, and they'll also need to set a password so they can do things as root. Clearly this isn't very user friendly.

This is a simple C program that aims to fix this problem. It looks at /home/amnesia/Persistent/torrc.additions and appends it to the end of /etc/tor/torrc and reloads torrc. For this to work as the amnesia user, you need to make update_torrc owned by root and executable by all with the setuid flag. Now any user that runs this will be effectively running as the root user (without needing to be a sudoer or have a user password set). The reason I wrote this in C instead of something way simpler, like bash, is the setuid flag only works compiled programs, not scripts. 

To install this in your own Tails persistent volume:

* Boot to Tails, mount your persistent volume, and choose More Options to set a password the first time
* Create a new `torrc.additions` file in your Persistent folder that contains the HidServAuth line you need

When you're done creating this file, lock down its permissions:

```
cd /home/amnesia/Persistent
sudo chown root:root torrc.additions
sudo chmod 444 torrc.additions
```

If you want to use the binary that I've already compiled:

* Copy the `update_torrc` binary into your Persistent folder
* Then run this to set the correct permissions:

```
cd /home/amnesia/Persistent
sudo chown root:root update_torrc
sudo chmod 755 update_torrc
sudo chmod +s update_torrc
```

If you don't trust me and want to compile it yourself:

* Copy `update_torrc.c` and `build.sh` to your Persistent folder
* Then run this:

```
sudo apt-get install build-essential
cd /home/amnesia/Persistent
sudo ./build.sh
```

Go ahead and reboot Tails. From this point on you can boot Tails and mount your persistent volume but not set a root password. All you have to do is wait to connect to the Tor network, open your Persistent folder, and double-click on `update_torrc`.
