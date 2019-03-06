#!/bin/bash
# Wrapper script to create Vagrant boxes for use with the "upgrade"
# scenario.

molecule test -s vagrant-packager && \
# Unfortunately since we need to prompt the user for sudo creds..
# I had to break the actual vagrant package logic outside of molecule
molecule/vagrant-packager/package.py && \
molecule destroy -s vagrant-packager


