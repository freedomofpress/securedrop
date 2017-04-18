#!/bin/bash
set -e

/usr/bin/expect<<EOF
spawn dpkg-reconfigure -f readline resolvconf
expect "updates?" { send "Yes\r" }
expect "dynamic files?" { send "Yes\r" }
EOF

exit 0
