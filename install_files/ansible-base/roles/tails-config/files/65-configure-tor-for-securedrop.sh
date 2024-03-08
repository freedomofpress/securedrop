#!/bin/sh

# appends HidServAuth values needed for SecureDrop
# authenticated onion services to /etc/tor/torrc
# and reloads Tor

# Run only when the interface is not "lo":
if [ "$1" = "lo" ]; then
  exit 0
fi

# Run whenever an interface gets "up", not otherwise:
if [ "$2" != "up" ]; then
  exit 0
fi

QT_QPA_PLATFORM="wayland;xcb" /usr/bin/python3 /home/amnesia/Persistent/.securedrop/securedrop_init.py
