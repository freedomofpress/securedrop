#!/bin/bash
# Reads user provided input from:
#securedrop/CONFIG_OPTIONS
#
# Usage: ./ossec_install.sh
# --no-updates will not download ossec binary
#
# Installs OSSEC server on the monitor server,
# then waits for the App Server's agent to connect
# The script then verifies that the App Server's agent is active
#
CWD="$(dirname $0)"
cd $CWD

source ../CONFIG_OPTIONS
OSSECBINARYURL="https://pressfreedomfoundation.org/securedrop-files/ossec-binary.tgz"
OSSECBINARYURLSIG="https://pressfreedomfoundation.org/securedrop-files/ossec-binary.tgz.sig"
SIGNINGKEY="https://pressfreedomfoundation.org/securedrop-files/signing_key.asc"
OSSECZIP="ossec-binary.tgz"
OSSECVERSION="ossec-hids-2.7"
TEMPDIR="/tmp/ossec"


# Check for root
root_check() {
  if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
  fi
}


#Catch error
catch_error() {
  if [ $1 -ne "0" ]; then
    echo "ERROR encountered $2"
    exit 1
  fi
}

if [ $ROLE = 'app' -o $ROLE = 'monitor' ]; then
  echo "Starting the interface installation..."
else
  echo "Role not defined in securedrop/install_scripts/CONFIG_OPTIONS"
  exit 1
fi

download_ossec() {
  if [ ! -d /tmp/ossec/$OSSECVERSION ]; then
    echo "Downloading $OSSECBINARYURL..."
    mkdir -p $TEMPDIR
    catch_error $? "making $TEMPDIR"
    ( cd $TEMPDIR ; curl $OSSECBINARYURL > $OSSECZIP ; )
    catch_error $? "downloading $OSSECBINARYURL"

#     (cd $TEMPDIR ; curl $SIGNINGKEY > $SIGNINGKEY ; )
#     catch_error $? "downloading $SIGNINGKEY"
#     gpg --import $TEMPDIR/$SIGNINGKEY
#     catch_error $? "importing $SIGNINGKEY
#     gpg --verify $OSSECVERSION.sig
#     catch_error $? "verifying $OSSECVERSION.sig"

    echo "Extracting $OSSECZIP..."
    ( cd $TEMPDIR ; tar -xzf $OSSECZIP ; )
    catch_error $? "extracting $TEMPDIR"
  fi
}


install_ossec() {
  #Copy the monitor preloaded vars config for ossec
  echo "coping preloaded-vars.conf..."
  sed -i "s/OSSEC_TYPE/$OSSEC_ROLE/g" preloaded-vars.conf
  cp preloaded-vars.conf $TEMPDIR/$OSSECVERSION/etc/preloaded-vars.conf
  catch_error $? "copying preloaded-vars.conf"

  #Run OSSEC install script
  echo "Installing OSSEC server..."
  $TEMPDIR/$OSSECVERSION/install.sh
  catch_error $? "installing OSSEC server"
}


config_files() {
  if [ $ROLE = "app" ]; then

    sed -i "s/MONITOR_IP/$MONITOR_IP/g" $ROLE.client.ossec.conf

    echo "Adding global config to /var/ossec/etc/ossec.conf..."
    BEGIN_MARK='<client'
    END_MARK='<\/client>'
    sed -i -ne "/$BEGIN_MARK/ {p; r $ROLE.client.ossec.conf" -e ":a; n; /$END_MARK/ {p; b}; ba}; p" /var/ossec/etc/ossec.conf

  elif [ $ROLE = "monitor" ]; then

    sed -i "s/SMTP_SERVER/$SMTP_SERVER/g" $ROLE.global.ossec.conf

    sed -i "s/EMAIL_DISTRO/$EMAIL_DISTRO/g" $ROLE.global.ossec.conf
    sed -i "s/EMAIL_DISTRO/$EMAIL_DISTRO/g" $ROLE.logs.ossec.conf

    sed -i "s/EMAIL_FROM/$EMAIL_FROM/g" $ROLE.global.ossec.conf

    echo "Adding global config to /var/ossec/etc/ossec.conf..."
    BEGIN_MARK='<global>'
    END_MARK='<\/global>'
    sed -i -ne "/$BEGIN_MARK/ {p; r $ROLE.global.ossec.conf" -e ":a; n; /$END_MARK/ {p; b}; ba}; p" /var/ossec/etc/ossec.conf
  fi

  #configuring the common sections
  echo "Adding syscheck config to /var/ossec/etc/ossec.conf..."
  BEGIN_MARK='<syscheck>'
  END_MARK='<!-- Files\/directories to ignore -->'
  sed -i -ne "/$BEGIN_MARK/ {p; r $ROLE.syscheck.ossec.conf" -e ":a; n; /$END_MARK/ {p; b}; ba}; p" /var/ossec/etc/ossec.conf

  echo "Adding log files and reports to /var/ossec/etc/ossec.conf..."
  BEGIN_MARK='<!-- Files to monitor (localfiles) -->'
  END_MARK='<localfile>'
  sed -i -ne "/$BEGIN_MARK/ {p; r $ROLE.logs.ossec.conf" -e ":a; n; /$END_MARK/ {p; b}; ba}; p" /var/ossec/etc/ossec.conf
}


restart_ossec() {
  #Restart OSSEC after copying config
  echo "Restarting ossec..."
  /var/ossec/bin/ossec-control restart
  catch_error $? "restarting ossec"
  echo "Restarted ossec"
}


gen_authd_keys() {
  #Generate OSSEC ssl key for authd
  echo "Generating keys for authd"

  openssl req \
    -new -newkey rsa:4096 -x509 -nodes -days 365 \
    -subj '/C=US/ST=NewYork/L=NewYork/CN=monitor' \
    -keyout /var/ossec/etc/sslmanager.key -out /var/ossec/etc/sslmanager.cert
}


start_authd() {
  #Enable Authd for client to App Server to connect
  #Ensure this is not always running
  /var/ossec/bin/ossec-authd -p 1515 -i $APP_IP >/dev/null 2>&1 &
  catch_error $? "Starting authd for $APP_IP"
  echo "authd is running ensure that after the source connects to disable authd"
}


start_agent_auth() {
  echo "Starting ossec agent auth with a manger IP $MONITOR_IP"
  /var/ossec/bin/agent-auth -m $MONITOR_IP -p 1515 -A app
  catch_error $? "starting ossec agent auth"
}

kill_authd() {
  echo "Leaving authd running is a security risk."
  echo "Start the installation on app server."
  echo "After installation on the app server is complete"
  read -p "enter 'Y' to continue: (Y|N): " -e -i Y CONNECT_ANS
  if [ $CONNECT_ANS = "Y" -o $CONNECT_ANS = "y" ]; then
    echo "Stoping authd..."
    pkill ossec-authd
    catch_error $? "killing ossec-authd"
    echo "ossec-authd killed"
  else
    echo "invalid entry try again. <CTRL> C to exit."
    echo "!!!OSSEC-authd does not authenticate. Leaving it running is a security risk not acceptable for production environments!!!"
    kill_authd
  fi
}

check_status() {
  echo "Verifying that the agent is active."
  echo "Sleep 15 seconds for agent to connect..."
  sleep 15
  if ! /var/ossec/bin/list_agents -c | grep "^source-$APP_IP"; then
    echo "The source host is not active."
    echo "It needs to be active to monitor the source server"
    echo "https://www.ossec.net/doc"
    echo "Exiting with errors. The App Server's ossec agent is not connected"
    exit 0
  fi
}

main() {
  root_check

  if [ "$ROLE" = 'monitor' ]; then
    OSSEC_ROLE="server"
    if [ ! "$1" = "--no-updates" ]; then 
      download_ossec
    fi
      install_ossec
      config_files
      restart_ossec
      gen_authd_keys
      start_authd
      kill_authd
      restart_ossec
      check_status
  elif [ "$ROLE" = 'app' ]; then
    OSSEC_ROLE="agent"
    if [ ! "$1" = "--no-updates" ]; then 
      download_ossec
    fi
      install_ossec
      config_files
      start_agent_auth
      restart_ossec
  else
    echo "not a valid role"
    main 
  fi

  echo "OSSEC installation complete"  
}


main

exit 0
