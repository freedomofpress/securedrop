#!/bin/bash
# SecureDrop 0.3pre upgrade helper script
# ./upgrade.sh
# parse_yaml() courtesy of a StackOverflow user:
# http://stackoverflow.com/a/21189044
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
ANSIBLE_BASE=$HOMEDIR/Persistent/securedrop/install_files/ansible-base

# check for elevated privileges. running with `sudo` will
# cause script to fail on SSH connections, since only the normal
# user has access to the ssh-agent keychain for the ATHS connections.
if [[ $UID == 0 ]]; then
  cat <<-EOS
  This script should not be run as root.
  If elevated privileges are required to install
  additional packages, you will be prompted to enter
  your sudo password.
EOS
  exit 1
fi

# check for persistence
if [[ ! -d /live/persistence/TailsData_unlocked ]]; then
  echo "Error: This script must be run on Tails with a persistent volume." 1>&2
  exit 1
fi

# check if git is installed
if ! dpkg --get-selections | grep -q "^git[[:space:]]*install$" >/dev/null; then
    echo "Package 'git' not found, but is required. Installing now."
	sudo apt-get install git
fi

# check if ansible is installed
if ! dpkg --get-selections | grep -q "^ansible[[:space:]]*install$" >/dev/null; then
    echo "Package 'ansible' not found, but is required. Installing now."
	sudo apt-get install ansible
fi

# TODO: should check that there is a key present in the ssh agent
# check for SSH identity
if [[ ! -f $HOMEDIR/.ssh/id_rsa ]]; then
	echo "Error: There is no SSH key file present." 1>&2
	exit 1
fi

# check for authenticated Tor hidden services
if ! grep -q 'HidServAuth' /etc/tor/torrc; then
	echo "Error: There are no HidServAuth values in your torrc file." 1>&2
	exit 1
fi

# parse prod-specific.yml YAML into Bash variables
eval $(parse_yaml $ANSIBLE_BASE/prod-specific.yml)

# check that prod-specific.yml contains IP addresses
if ! echo $monitor_ip | grep -q -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}"; then
	echo "Error: monitor_ip in prod-specific.yml is not an IP address." 1>&2
	exit 1
fi

if ! echo $app_ip | grep -q -E -o "([0-9]{1,3}[\.]){3}[0-9]{1,3}"; then
	echo "Error: app_ip in prod-specific.yml is not an IP address." 1>&2
	exit 1
fi

# check that an SSH user is defined
if [[ -z $ssh_users ]]; then
	echo "Error: ssh_users is not defined in prod-specific.yml." 1>&2
	exit 1
fi

# grab .onion hostnames from the Ansible inventory and check that they're not IPs
app_ssh_host_raw=$(awk '/app ansible_ssh_host=.* /{ print $2 }' $ANSIBLE_BASE/inventory)
mon_ssh_host_raw=$(awk '/mon ansible_ssh_host=.* /{ print $2 }' $ANSIBLE_BASE/inventory)
app_ssh_host="${app_ssh_host_raw#ansible_ssh_host=}"
mon_ssh_host="${mon_ssh_host_raw#ansible_ssh_host=}"

if [[ ! $app_ssh_host =~ .*onion ]]; then
	echo "Error: the app ansible_ssh_host in Ansible's inventory file is not an .onion address." 1>&2
	exit 1
fi

if [[ ! $mon_ssh_host =~ .*onion ]]; then
	echo "Error: the mon ansible_ssh_host in Ansible's inventory file is not an .onion address." 1>&2
	exit 1
fi

# check that we can connect to each server via SSH
app_status=$(ssh -i $HOMEDIR/.ssh/id_rsa -l $ssh_users -o BatchMode=yes -o "ConnectTimeout=45" $app_ssh_host echo OK 2>&1)
mon_status=$(ssh -i $HOMEDIR/.ssh/id_rsa -l $ssh_users -o BatchMode=yes -o "ConnectTimeout=45" $mon_ssh_host echo OK 2>&1)

if [[ $app_status != "OK" ]]; then
	echo "Error: can't connect to the Application Server via SSH." 1>&2
	exit 1
fi

if [[ $mon_status != "OK" ]]; then
	echo "Error: can't connect to the Monitor Server via SSH." 1>&2
	exit 1
fi

# remove old kernels
ssh -i $HOMEDIR/.ssh/id_rsa -l $ssh_users -o BatchMode=yes -o "ConnectTimeout=45" $app_ssh_host sudo apt-get autoremove 2>&1
ssh -i $HOMEDIR/.ssh/id_rsa -l $ssh_users -o BatchMode=yes -o "ConnectTimeout=45" $mon_ssh_host sudo apt-get autoremove 2>&1

# run the upgrade playbook
ansible-playbook -i $ANSIBLE_BASE/inventory -u $ssh_users --sudo $ANSIBLE_BASE/upgrade.yml

# run the production playbook
# NOTE: this run intentionally skips running the 'backup' role.
# Unintentionally running the 'backup' role can cause large file transfers
# over Tor, causing substantial problems during upgrade. If you wish to
# run a backup manually, use this command:
#
# ansible-playbook -i $ANSIBLE_BASE/inventory -u $ssh_users --sudo $ANSIBLE_BASE/securedrop-prod.yml --tags backup
#
ansible-playbook -i $ANSIBLE_BASE/inventory -u $ssh_users --sudo $ANSIBLE_BASE/securedrop-prod.yml --skip-tags backup
