#!/bin/sh
sudo rm update_torrc
gcc -o update_torrc update_torrc.c
sudo chown root:root update_torrc
sudo chmod 755 update_torrc
sudo chmod +s update_torrc 
