## Install the grsec-Patched Ubuntu Kernel

The grsec patch increases the security of the Source, Document, and Monitor servers. For now, you have to patch the kernel yourself and make sure that it will boot alright.

        cd ..  
        dpkg -i *.deb  

### Before You Get Started

(Todo: Explain that the patched kernel has only been tested on specific hardware, and list that hardware.)
        
### Obtaining the Patch

(Todo: Explain how to obtain the patch, somewhere in the install script?)

### Configuring and Installing the Patch

(Todo: More detail about what you need to do before you can reboot.)

Review boot menu and boot into the new kernel. Verify that `/boot/grub/menu.lst` has the correct values. Make adjustments as necessary.

        sudo reboot 

After the reboot check that you booted into the correct kernel.   

        uname -r  

It should end in '-grsec'  

After finishing installing the patch, ensure the grsec sysctl configs are applied and locked.

        sysctl -p  
        sysctl -w kernel.grsecurity.grsec_lock = 1  
        sysctl -p 
        
Visit the official [Grsecurity documentation](http://en.wikibooks.org/wiki/Grsecurity) for more information about [obtaining](http://en.wikibooks.org/wiki/Grsecurity/Obtaining_grsecurity) and [configuring and installing](http://en.wikibooks.org/wiki/Grsecurity/Configuring_and_Installing_grsecurity) the kernel patch.
