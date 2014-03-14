#!/bin/bash
# Usage: ./display_tor_urls.sh
# Description: Depending which securedrop package is installed
#  display the respective tor url and auth values
set -e
#set -x
bold=$(tput bold)
blue=$(tput setaf 4)
red=$(tput setaf 1)
normalcolor=$(tput sgr 0)

    if [ "$(dpkg -l securedrop-app)" ]; then
        # Display the urls for the source and document interfaces
        if [ -f /var/chroot/source/var/lib/tor/hidden_service/hostname ]; then
            source_int="$(cat /var/chroot/source/var/lib/tor/hidden_service/hostname)"
            echo "$bold$blue################################################################################$normalcolor"
            echo "$blue The Source Interfaces url is: $normalcolor"
            echo "$red http://$source_int"
        fi

        if [ -f /var/chroot/document/var/lib/tor/hidden_service/hostname ]; then
            echo "$blue The Document Interface listens on port 8080"
            echo " you will need to$bold append :8080$normalcolor$blue to the url as shown below"
            echo " The Document Interfaces' url and auth values for each journalist: $normalcolor"
            while read line; do
                ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
                ATHS_USER="$(echo "$line" | awk '{print $5}')"
                echo "$red $ATHS_USER$blue's url is$red http://$ONION_ADDRESS:8080$normalcolor"
                echo "$red $ATHS_USER$blue's TBB torrc config line is:"
                echo "$red HidServAuth $line $normalcolor"
            done < /var/chroot/document/var/lib/tor/hidden_service/hostname
            echo "$blue To add more journalists run $red'/opt/securedrop/scripts/add-journalist.sh NAME'$blue script$normalcolor"
            echo "$bold$blue################################################################################$normalcolor"
        fi

        if [ -f /var/lib/tor/hidden_service/hostname ]; then
            echo "$bold$blue#################################################################################$normalcolor"
            echo "$blue The App Server is only accessible through a Tor Authenticated Hidden Service"
            echo " you will need to use connect-proxy, torify or something similar to"
            echo " proxy ssh through tor$normalcolor"
            while read line; do
                ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
                ATHS_USER="$(echo "$line" | awk '{print $5}')"
                echo "$red $ATHS_USER$blue's ssh address is$red ssh $ATHS_USER@$ONION_ADDRESS$normalcolor"
                echo "$red $ATHS_USER$blue's system torrc config line is:"
                echo "$red HidServAuth $line $normalcolor"
            done < /var/lib/tor/hidden_service/hostname
            echo "$blue You will need to run the$red '/opt/securedrop/scripts/add-admin.sh USERNAME'$blue"
            echo " to add more admins.$normalcolor"
            echo "$bold$blue#################################################################################$normalcolor"
       fi
    elif [ "$(dpkg -l securedrop-document)" ]; then
        if [ -f /var/lib/tor/hidden_service/hostname ]; then
            echo "$blue The Document Interface listens on port 8080"
            echo " you will need to$bold append :8080$normalcolor$blue to the url as shown below"
            echo " The Document Interfaces' url and auth values for each journalist: $normalcolor"
            while read line; do
                ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
                ATHS_USER="$(echo "$line" | awk '{print $5}')"
                echo "$red $ATHS_USER$blue's url is$red http://$ONION_ADDRESS:8080$normalcolor"
                echo "$red $ATHS_USER$blue's torrc config line is:"
                echo "$red HidServAuth $line $normalcolor"
            done < /var/lib/tor/hidden_service/hostname
            echo "$bold$blue################################################################################$normalcolor"
        fi
    elif [ "$(dpkg -l securedrop-source)" ]; then
        if [ -f /var/lib/tor/hidden_service/hostname ]; then
            source_int="$(cat /var/lib/tor/hidden_service/hostname)"
            echo "$bold$blue################################################################################$normalcolor"
            echo "$blue The Source Interfaces url is: $normalcolor"
            echo "$red http://$source_int"
        fi
    elif [ "$(dpkg -l securedrop-monitor)" ]; then
        if [ -f /var/lib/tor/hidden_service/hostname ]; then
            echo "$bold$blue#################################################################################$normalcolor"
            echo "$blue The Monitor Server is only accessible through a Tor Authenticated Hidden Service"
            echo " you will need to use connect-proxy, torify or something similar to"
            echo " proxy ssh through tor$normalcolor"
            while read line; do
                ONION_ADDRESS="$(echo "$line" | awk '{print $1}')"
                ATHS_USER="$(echo "$line" | awk '{print $5}')"
                echo "$red $ATHS_USER$blue's ssh address is$red ssh $ATHS_USER@$ONION_ADDRESS$normalcolor"
                echo "$red $ATHS_USER$blue's system torrc config line is:"
                echo "$red HidServAuth $line $normalcolor"
            done < /var/lib/tor/hidden_service/hostname
            echo "$blue You will need to run the$red '/opt/securedrop/scripts/add-admin.sh USERNAME'$blue"
            echo " to add more admins.$normalcolor"
            echo "$bold$blue#################################################################################$normalcolor"
 
        fi
     fi
