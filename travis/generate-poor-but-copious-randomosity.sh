#!/bin/bash 
set -e -u

ls -l /dev*

# generate a bunch of disk-based entropy?
cat /proc/sys/kernel/random/entropy_avail
echo 'here comes some entropy!!!!'
cat /dev/sda1 | tail -n 10000 > /dev/null
echo 'did you see all that entropy right there?!'
cat /proc/sys/kernel/random/entropy_avail
