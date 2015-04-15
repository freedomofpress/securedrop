#!/bin/bash
# SecureDrop 0.3pre upgrade helper script
# ./upgrade.sh <non default git branch to use>
# parse_yaml() courtesy of a StackOverflow user:
# http://stackoverflow.com/a/21189044
set -x
set -e

function parse_yaml {
   local prefix=$2
   local s='[[:space:]]*' w='[a-zA-Z0-9_]*' fs=$(echo @|tr @ '\034')
   sed -ne "s|^\($s\):|\1|" \
        -e "s|^\($s\)\($w\)$s:$s[\"']\(.*\)[\"']$s\$|\1$fs\2$fs\3|p" \
        -e "s|^\($s\)\($w\)$s:$s\(.*\)$s\$|\1$fs\2$fs\3|p"  $1 |
   awk -F$fs '{
      indent = length($1)/2;
      vname[indent] = $2;
      for (i in vname) {if (i > indent) {delete vname[i]}}
      if (length($3) > 0) {
         vn=""; for (i=0; i<indent; i++) {vn=(vn)(vname[i])("_")}
         printf("%s%s%s=\"%s\"\n", "'$prefix'",vn, $2, $3);
      }
   }'
}

# set paths and variables
HOMEDIR=/home/amnesia
PERSISTENT=$HOMEDIR/Persistent
TAILSCFG=/live/persistence/TailsData_unlocked
ANSIBLE=$PERSISTENT/securedrop/install_files/ansible-base
# This will need to be changed to default to the expected current version 0.3.3
GIT_TAG_NAME=${1:-0.3.3}

# check for root
if [[ $EUID -ne 0 ]]; then
  echo "Error: This script must be run as root." 1>&2
  exit 1
fi

# check for persistence
if [ ! -d "$TAILSCFG" ]; then
  echo "Error: This script must be run on Tails with a persistent volume." 1>&2
  exit 1
fi

# check if git is installed
if ! dpkg --get-selections | grep -q "^git[[:space:]]*install$" >/dev/null; then
	apt-get install git
fi

# check if ansible is installed
if ! dpkg --get-selections | grep -q "^ansible[[:space:]]*install$" >/dev/null; then
	apt-get install ansible
fi

# TODO: should check that there is a key present in the ssh agent
# check for SSH identity
if [ ! -f $HOMEDIR/.ssh/id_rsa ]; then
	echo "Error: There is no SSH key file present." 1>&2
	exit 1
fi

# check for SecureDrop git repo has correct branch checked out.
if ! git tag --points-at HEAD | grep -q "^$GIT_TAG_NAME$" > /dev/null; then
  echo "Error: This script must be run with SecureDrop's current tagged release" 1>&2
  exit 1
fi

# check that the signature is valid
VERIFIED=$(git tag -v $GIT_TAG_NAME 2>&1 | tail -1 | grep gpg)
if [[ ! $VERIFIED =~ .*Good\ signature.* ]]; then
  echo "Error: the signed git tag could not be verified." 1>&2
  exit 1
fi

# check for authenticated Tor hidden services
if ! grep -q 'HidServAuth' /etc/tor/torrc; then
	echo "Error: There are no HidServAuth values in your torrc file." 1>&2
	exit 1
fi

# parse prod-specific.yml YAML into Bash variables
eval $(parse_yaml $ANSIBLE/prod-specific.yml)

# check that prod-specific.yml contains IP addresses
if ! echo $monitor_ip | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}"; then
	echo "Error: monitor_ip in prod-specific.yml is not an IP address." 1>&2
	exit 1
fi

if ! echo $app_ip | grep -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}"; then
	echo "Error: app_ip in prod-specific.yml is not an IP address." 1>&2
	exit 1
fi

# check that an SSH user is defined
if [ -z $ssh_users ]; then
	echo "Error: ssh_users is not defined in prod-specific.yml." 1>&2
	exit 1
fi

# grab .onion hostnames from the Ansible inventory and check that they're not IPs
APPSSHHOST=`awk '/app ansible_ssh_host=.* /{ print $2 }' $ANSIBLE/inventory`
MONSSHHOST=`awk '/mon ansible_ssh_host=.* /{ print $2 }' $ANSIBLE/inventory`
APP_SSH_HOST="${APPSSHHOST#ansible_ssh_host=}"
MON_SSH_HOST="${MONSSHHOST#ansible_ssh_host=}"

if [[ ! $APP_SSH_HOST =~ .*onion ]]; then
	echo "Error: the app ansible_ssh_host in Ansible's inventory file is not an .onion address." 1>&2
	exit 1
fi

if [[ ! $MON_SSH_HOST =~ .*onion ]]; then
	echo "Error: the mon ansible_ssh_host in Ansible's inventory file is not an .onion address." 1>&2
	exit 1
fi

# check that we can connect to each server via SSH
APP_STATUS=$(sudo -u amnesia ssh -i /home/amnesia/.ssh/id_rsa -l $ssh_users -o BatchMode=yes -o "ConnectTimeout=45" -o "ProxyCommand connect -R remote -5 -S localhost:9050 %h %p" $APP_SSH_HOST echo OK 2>&1)
MON_STATUS=$(sudo -u amnesia ssh -i /home/amnesia/.ssh/id_rsa -l $ssh_users -o BatchMode=yes -o "ConnectTimeout=45" -o "ProxyCommand connect -R remote -5 -S localhost:9050 %h %p" $MON_SSH_HOST echo OK 2>&1)

if [[ $APP_STATUS != "OK" ]]; then
	echo "Error: can't connect to the Application Server via SSH." 1>&2
	exit 1
fi

if [[ $MON_STATUS != "OK" ]]; then
	echo "Error: can't connect to the Monitor Server via SSH." 1>&2
	exit 1
fi

# remove old kernels
sudo -u amnesia ssh -i /home/amnesia/.ssh/id_rsa -l $ssh_users -o BatchMode=yes -o "ConnectTimeout=45" -o "ProxyCommand connect -R remote -5 -S localhost:9050 %h %p" $APP_SSH_HOST sudo apt-get autoremove 2>&1
sudo -u amnesia ssh -i /home/amnesia/.ssh/id_rsa -l $ssh_users -o BatchMode=yes -o "ConnectTimeout=45" -o "ProxyCommand connect -R remote -5 -S localhost:9050 %h %p" $MON_SSH_HOST sudo apt-get autoremove 2>&1

# run the upgrade playbook
sudo -u amnesia ansible-playbook -i install_files/ansible-base/inventory -u $ssh-users --sudo install_files/ansible-base/upgrade.yml

# run the production playbook
sudo -u amnesia ansible-playbook -i install_files/ansible-base/inventory -u $ssh_users --sudo install_files/ansible-base/securedrop-prod.yml
