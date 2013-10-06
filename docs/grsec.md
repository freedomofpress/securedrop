## Install the grsec-patched Ubuntu kernel

For now, you have to patch the kernel yourself and make sure that it will boot alright.

The grsec patch increases the security of each of the servers.  

        cd ..  
        dpkg -i *.deb  

Review boot menu and boot into new kernel  
Verify that `/boot/grub/menu.lst` has the correct values. Make adjustments as necessary.  

        sudo reboot 

After the reboot check that you booted into the correct kernel.   

        uname -r  

It should end in '-grsec'  

After finishing installing the ensure the grsec sysctl configs are applied and locked

        sysctl -p  
        sysctl -w kernel.grsecurity.grsec_lock = 1  
        sysctl -p 