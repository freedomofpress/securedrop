#!/bin/bash
# Usage:
# Description: Add or remove journalist users from the document interface
bold=$(tput bold)
blue=$(tput setaf 4)
red=$(tput setaf 1)
normalcolor=$(tput sgr 0)
basedir="/var/chroot/document"
journalist_user="$1"

# Add journalist to tor hidden service config.
# this will not work unless there is already at least one journalist configured.
# if a journalist is not already configured it does not need leading comma
if [[ ! "$(grep "$journalist_user" $basedir/etc/tor/torrc)" ]]; then
    sed -i "/HiddenServiceAuthorizeClient/s/$/,$journalist_user/" $basedir/etc/tor/torrc
fi

schroot -c document -u root --directory / -- service tor reload
echo "sleep 10 sec to wait for cert to be created"
sleep 10
if [ -f $basedir/var/lib/tor/hidden_service/hostname ]; then
    echo "$bold$blue################################################################################$normalcolor"
    echo "$blue The Document Interface is only accessible through a Tor Authenticated Hidden Service"
    echo " you will need to modify the journalist's torrc file and add a bookmark for them"
    echo "$normalcolor"
    ONION_ADDRESS="$(awk '/'$journalist_user'/ {print $1}' $basedir/var/lib/tor/hidden_service/hostname)"
    AUTH_VALUE="$(awk '/'$journalist_user'/ {print $2}' $basedir/var/lib/tor/hidden_service/hostname)"
    echo ""
    echo "$red $journalist_user$blue's ssh ATHS address is$red $ONION_ADDRESS $normalcolor"
    echo "$red $journalist_user$blue's torrc config line is:"
    echo "$red HidServAuth $ONION_ADDRESS $AUTH_VALUE # $journalist_user$normalcolor"
    echo "$bold$blue################################################################################$normalcolor"
fi
