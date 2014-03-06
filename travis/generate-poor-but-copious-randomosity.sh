#!/bin/bash 
set -e -u

ls -l /dev*

# generate a bunch of disk-based entropy?
cat /proc/sys/kernel/random/entropy_avail
echo 'here comes some entropy!!!!'

wget --quiet -O /dev/null http://softwarestudies.com/projects/manga.viz/ma
nga.first_10_titles.Xstdev.Yentropy.10000w.jpeg_medium.jpg

echo 'did you see all that entropy right there?!'
cat /proc/sys/kernel/random/entropy_avail
