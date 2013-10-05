#!/bin/bash
MyUID=`id -u $NAME`
cd /etc
for NAME in `cut -d: -f1 /etc/passwd`; do
  MyUID=`id -u $NAME`  
  if [ $MyUID -lt 500 -a $NAME != 'root' ]; then
  `usermod -L -s /dev/null $NAME`
  fi
done
