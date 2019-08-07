#!/bin/sh

# appends HidServAuth values needed for SecureDrop
# authenticated Onion Services to /etc/tor/torrc
# and reloads Tor

# Run only when the interace is not "lo":
if [ "$1" = "lo" ]; then
  exit 0
fi

# Run whenever an interface gets "up", not otherwise:
if [ "$2" != "up" ]; then
  exit 0
fi

/usr/bin/python /home/amnesia/Persistent/.securedrop/securedrop_init.py
