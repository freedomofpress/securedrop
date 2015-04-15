#!/bin/bash
# SecureDrop 0.3pre upgrade helper script

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

# TODO: this should check that the correct branch is checked out and the
# signature is valid.
# check for SecureDrop git repo
if [ ! -d "$ANSIBLE" ]; then
  echo "Error: This script must be run with SecureDrop's git repository cloned to 'securedrop' in your Persistent folder." 1>&2
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

# perform upgrade
su amnesia
cd ~/Persistent/securedrop

git stash save "site specific configs"
git pull
git checkout check-migration-scripts-for-0.3
git stash pop

echo "We're about to open the Ansible inventory file so you can review it. Save it when you're done..."
sleep 5
editor install_files/ansible-base/inventory

echo "We're about to open the prod-specific.yml settings so you can review them. Save the file when youre done..."
sleep 5
editor install_files/ansible-base/prod-specific.yml

# run the upgrade playbook
ansible-playbook -i install_files/ansible-base/inventory -u $ssh-users --sudo install_files/ansible-base/upgrade.yml

git stash save "site specific configs"
git checkout tags/0.3.2

VERIFIED=$(git tag -v 0.3.2 2>&1 | tail -1 | grep gpg)
if [[ ! $VERIFIED =~ .*Good\ signature.* ]]; then
	echo "Error: the signed git tag could not be verified." 1>&2
	exit 1
fi

git stash pop

echo "We're about to open the Ansible inventory file so you can review it. Save it when you're done..."
sleep 5
editor install_files/ansible-base/inventory

echo "We're about to open the prod-specific.yml settings so you can review them. Save the file when youre done..."
sleep 5
editor install_files/ansible-base/prod-specific.yml

# run the production playbook
ansible-playbook -i install_files/ansible-base/inventory -u $ssh_users --sudo install_files/ansible-base/securedrop-prod.yml
