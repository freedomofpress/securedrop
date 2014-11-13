# Installing Tails on USB sticks

Tails is an operating system that boots off of removable media, either a DVD or a USB stick. For SecureDrop you'll need to install Tails onto USB sticks so that you can enable persistent storage.

The [Tails website](https://tails.boum.org/) has detailed and up-to-date instructions on how to download and verify Tails, and how to create a Tails USB stick. Here are some links to help you out:

* [Download, verify, install](https://tails.boum.org/download/index.en.html)
* [Installing onto a USB stick or SD card](https://tails.boum.org/doc/first_steps/installation/index.en.html)
* [Create & configure the persistent volume](https://tails.boum.org/doc/first_steps/persistence/configure/index.en.html)

## Note for Mac OS X users

The tails documentation for "manually installing" Tails onto a USB device for Mac OS X include the following `dd` invocation to copy the .iso to the USB:

```
dd if=[tails.iso] of=/dev/diskX
```

This command is *very slow* (in my testing, it takes about 18 minutes to copy the .iso to a USB 2.0 drive). You can speed it up by adding the following arguments to `dd`:

```
dd if=[tails.iso] of=/dev/rdiskX bs=1m
```

Note the change from `diskX` to `rdiskX`. This reduced the copy time to 3 minutes for me. For an explanation, I defer to the relevant [Server Fault](http://superuser.com/questions/421770/dd-performance-on-mac-os-x-vs-linux) ("I believe it has to do with buffers").
