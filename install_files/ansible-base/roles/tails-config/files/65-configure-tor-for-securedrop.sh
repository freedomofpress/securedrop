#!/bin/sh

# notifies the user that SecureDrop is configured, and triggers the updater

# Run only when the interace is not "lo":
if [ "$1" = "lo" ]; then
  exit 0
fi

# Run whenever an interface gets "up", not otherwise:
if [ "$2" != "up" ]; then
  exit 0
fi

/usr/bin/python3 /home/amnesia/Persistent/.securedrop/securedrop_init_post.py
