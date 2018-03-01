#!/bin/bash

molecule test -s vagrant_packager && \
# Unfortunately since we need to prompt the user for sudo creds..
# I had to break the actual vagrant package logic outside of molecule
molecule/vagrant_packager/package.py && \
molecule destroy -s vagrant_packager
