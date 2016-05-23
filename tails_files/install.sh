#!/bin/bash
# SecureDrop persistent setup script for Tails.
#
# Configures access to SecureDrop over Authenticated Tor Hidden Services (ATHS)
# for both the Admin and Journalist Workstations, via a NetworkManager hook.
# Creates convenient desktop icons for easy access. Adds SSH access for Admins.

set -e

# Declare constants. These values will be used by various
# functions throughout the script.
amnesia_home="/home/amnesia"
amnesia_desktop="${amnesia_home}/Desktop"
amnesia_persistent="${amnesia_home}/Persistent"
network_manager_dispatcher="/etc/NetworkManager/dispatcher.d"
securedrop_dotfiles="${amnesia_persistent}/.securedrop"
securedrop_ansible_base="${amnesia_persistent}/securedrop/install_files/ansible-base"
securedrop_init_script="${securedrop_dotfiles}/securedrop_init.py"
tails_live_persistence="/live/persistence/TailsData_unlocked"
tails_live_dotfiles="${tails_live_persistence}/dotfiles"
torrc_additions="${securedrop_dotfiles}/torrc_additions"

# Declare globals. During initial provisioning, we may need to prompt
# for ATHS info for the Document Interface, particularly on the
# Journalist Workstation. In order to avoid reprompting, we'll store
# the value in a reusable global var.
document_aths_info_global=''
source_ths_url_global=''

function validate_tails_environment()
{
  # Ensure that initial expectations about the SecureDrop environment
  # are met. Error messages below explain each condition.
  if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root" 1>&2
    exit 1
  fi
  source /etc/os-release
  if [[ $TAILS_VERSION_ID =~ ^1\..* ]]; then
    echo "This script must be used on Tails version 2.x or greater." 1>&2
    exit 1
  fi
  if [ ! -d "$tails_live_persistence" ]; then
    echo "This script must be run on Tails with a persistent volume." 1>&2
    exit 1
  fi
  if [ ! -d "$securedrop_ansible_base" ]; then
    echo "This script must be run with SecureDrop's git repository cloned to 'securedrop' in your Persistent folder." 1>&2
    exit 1
  fi
}

function is_admin_workstation()
{
  # Detect whether the script is being run on Admin or Journalist Workstation.
  # Under no circumstances should the Journalist Workstation have SSH info,
  # so we'll assume that if the ATHS file for SSH info on the Application Server
  # is present, we're running on the Admin Workstation, otherwise Journalist.
  if [ -f $securedrop_ansible_base/app-ssh-aths ]; then
    # In Bash, 0 equates to Boolean true and 1 to Boolean false.
    return 0
  else
    return 1
fi
}

function cleanup_legacy_artifacts()
{
  # Catch-all function for handling backwards-compatibility. If tasks change
  # between versions of SecureDrop and require this script to be rerun, place
  # "cleanup" tasks here.

  # Remove xsessionrc from 0.3.2 if present
  persistent_xsessionrc_file="${tails_live_persistence}/dotfiles/.xsessionrc"
  if [ -f $persistent_xsessionrc_file ]; then
    rm -f $persistent_xsessionrc_file > /dev/null 2>&1
    # Repair the torrc backup, which was probably busted due to the
    # race condition between .xsessionrc and
    # /etc/NetworkManager/dispatch.d/10-tor.sh This avoids breaking
    # Tor after this script is run.
    #
    # If the Sandbox directive is on in the torrc (now that the dust
    # has settled from any race condition shenanigans), *and* there is
    # no Sandbox directive already present in the backup of the
    # original, "unmodified-by-SecureDrop" copy of the torrc used by
    # securedrop_init, then port that Sandbox directive over to avoid
    # breaking Tor by changing the Sandbox directive while it's
    # running.
    if grep -q 'Sandbox 1' /etc/tor/torrc && ! grep -q 'Sandbox 1' /etc/tor/torrc.bak; then
      echo "Sandbox 1" >> /etc/tor/torrc.bak
    fi
  fi

  # Remove previous NetworkManager hook if present. In 0.3.6 the prefix
  # was "99-", which caused it to run too late. In 0.3.5 the prefix was "70-"
  # and should also be removed for backwards-compatibility.
  for d in $tails_live_persistence $securedrop_dotfiles $network_manager_dispatcher; do
    for f in 70-tor-reload.sh 99-tor-reload.sh ; do
      rm -f "${d}/${f}" > /dev/null 2>&1
    done
  done

  # Remove binary setuid wrapper from previous tails_files installation, if it exists.
  rm -f "${securedrop_dotfiles}/securedrop_init" 2>&1
}


function copy_securedrop_dotfiles()
{
  mkdir -p "$securedrop_dotfiles"

  # copy icon, launchers and scripts
  cp -f securedrop_icon.png $securedrop_dotfiles
  cp -f document.desktop $securedrop_dotfiles
  cp -f source.desktop $securedrop_dotfiles
  cp -f securedrop_init.py $securedrop_init_script

  # set permissions
  chmod 755 $securedrop_dotfiles

}

function set_permissions_on_securedrop_dotfiles()
{
  # Follow up function to enforce correct permissions and ownership
  # on SecureDrop dotfiles in the staging directly. Separated
  # into function to aid readability.
  chown root:root $securedrop_init_script
  chmod 700 $securedrop_init_script
  chown root:root $torrc_additions
  chmod 400 $torrc_additions

  chown amnesia:amnesia "${securedrop_dotfiles}/securedrop_icon.png"
  chmod 600 "${securedrop_dotfiles}/securedrop_icon.png"
}

function prompt_for_document_aths_info()
{
  # Ad-hoc memoization via a global variable. If we've already prompted for
  # the ATHS info here, the global will be populated. Otherwise, we'll store it.
  if [ -z $document_aths_info_global ] ; then
    # During initial provisioning of the Journalist Workstation, the ATHS file
    # for the Document Interface may not be present. If not, prompt for the info.
    aths_regex="^(HidServAuth [a-z2-7]{16}\.onion [A-Za-z0-9+/.]{22})"
    # Loop while reading the input from a dialog box.
    while [[ ! "$document_aths_info" =~ $aths_regex ]]; do
      document_aths_info="$(zenity --entry \
        --title='Hidden service authentication setup' \
        --width=600 \
        --window-icon=${securedrop_dotfiles}/securedrop_icon.png \
        --text='Enter the HidServAuth value to be added to /etc/tor/torrc:')"
    done
  # The global var is populated, so use it for the function var.
  else
    document_aths_info="$document_aths_info_global"
  fi
  echo "$document_aths_info"
}

function prompt_for_source_ths_url()
{
  # Interactively prompt for the Source Interface Onion URL.
  # During initial provisioning of the Journalist Workstation, the THS file
  # for the Source Interface may not be present. If not, prompt for the info.

  # Ad-hoc memoization via a global variable. If we've already prompted for
  # the ATHS info here, the global will be populated. Otherwise, we'll store it.
  if [ -z $source_ths_url_global ] ; then
    ths_regex="^[a-z2-7]{16}\.onion"
    # Loop while reading the input from a dialog box.
    while [[ ! "$document_aths_info" =~ $ths_regex ]]; do
      ths_url="$(zenity --entry \
        --title='Hidden service authentication setup' \
        --width=600 \
        --window-icon=${securedrop_dotfiles}/securedrop_icon.png \
        --text='Enter the Source Interface Onion URL:')"
    done
  # The global var is populated, so use it for the function var.
  else
    ths_url="$source_ths_url_global"
  fi
  echo "$ths_url"
}

function lookup_app_ssh_aths_url()
{
  app_ssh_aths="$(awk '{ print $2 }' ${securedrop_ansible_base}/app-ssh-aths)"
  echo "$app_ssh_aths"
}

function lookup_mon_ssh_aths_url()
{
  mon_ssh_aths="$(awk '{ print $2 }' ${securedrop_ansible_base}/mon-ssh-aths)"
  echo "$mon_ssh_aths"
}

function lookup_document_aths_url()
{
  # First look for the flat file containing the exact value we want.
  # The Admin Workstation will certainly have this file, and the Journalist
  # Workstation probably, but not definitely.
  if [ -f "${securedrop_ansible_base}/app-document-aths" ] ; then
    app_document_aths="$(awk '{ print $2 }' ${securedrop_ansible_base}/app-document-aths)"
  # Failing that, check for ATHS info in the existing Tor config. A previously
  # configured Journalist Workstation will already have the value in torrc.
  # Since we know we're in a Journalist Workstation, assume there's only one
  # ATHS value in the torrc, and use the first.
  elif grep -q -P '^HidServAuth [a-z2-7]{16}\.onion [A-Za-z0-9+/.]{22}' /etc/tor/torrc ; then
    app_document_aths="$(grep ^HidServAuth /etc/tor/torrc | head -n 1 | awk '{ print $2 }')"
  # Last shot before prompting: check for an existing desktop icon specifically
  # for the Document Interface. If found, we can extract the URL from there.
  elif [ -e "${amnesia_desktop}/document.desktop" ] ; then
    app_document_aths="$(grep ^Exec=/usr/local/bin/tor-browser | awk '{ print $2 }')"
  # Couldn't find it anywhere. We'll have to prompt!
  else
    app_document_aths="$(prompt_for_document_aths_info | awk '{ print $2 }')"
  fi
  echo "$app_document_aths"
}

function lookup_source_ths_url()
{
  # Find the Onion URL to the Source Interface. First look for the flat file
  # containing the exact value we want. The Admin Workstation will certainly
  # have this file, and the Journalist Workstation probably, but not definitely.
  if [ -f "${securedrop_ansible_base}/app-source-ths" ] ; then
    app_source_ths="$(awk '{ print $2 }' ${securedrop_ansible_base}/app-source-ths)"
  # Failing that, check for the public THS URL in an existing Desktop icon.
  elif [ -e "${amnesia_desktop}/source.desktop" ] ; then
    app_source_ths="$(grep ^Exec=/usr/local/bin/tor-browser | awk '{ print $2 }')"
  # Couldn't find it anywhere. We'll have to prompt!
  else
    app_source_ths="$(prompt_for_source_ths_url)"
  fi
  echo "$app_source_ths"
}

function configure_ssh_aliases()
{
  # Create SSH aliases for Admin Workstation so `ssh app` and `ssh mon` work
  # as expected. Quite useful for interactive debugging, or harvesting logs.
  # Don't clobber an existing SSH config file; only run if none exists.
  if [[ -d "${amnesia_home}/.ssh" && ! -f "${amnesia_home}/.ssh/config" ]]; then
    # Rather than try to parse the YAML vars file in Bash, let's prompt for username.
    admin_ssh_username="$(zenity --entry \
        --title='Admin SSH user' \
        --window-icon=${securedrop_dotfiles}/securedrop_icon.png \
        --text='Enter your username on the App and Monitor server:')"
    cat > "${securedrop_dotfiles}/ssh_config" <<EOL
Host app
  Hostname $(lookup_app_ssh_aths_url)
  User $admin_ssh_username
Host mon
  Hostname $(lookup_mon_ssh_aths_url)
  User $admin_ssh_username
EOL
    chown amnesia:amnesia "${securedrop_dotfiles}/ssh_config"
    chmod 600 "${securedrop_dotfiles}/ssh_config"
    cp -pf "${securedrop_dotfiles}/ssh_config" "${amnesia_home}/.ssh/config"
  fi
}

function configure_ansible_apt_persistence()
{
  # set ansible to auto-install
  if ! grep -q 'ansible' "${tails_live_persistence}/live-additional-software.conf"; then
    echo "ansible" >> "${tails_live_persistence}/live-additional-software.conf"
  fi
}

function update_ansible_inventory()
{
  # The local IPv4 addresses for the Application and Monitor servers are only
  # used during initial provisioning. Thereafter the SSH connections must be
  # made over Tor. Update the static inventory file so the Admin doesn't
  # have to copy/paste the values.
  if ! grep -v "^#.*onion" "${securedrop_ansible_base}/inventory" | grep -q onion; then
    sed -i "s/app ansible_ssh_host=.* /app ansible_ssh_host=${lookup_app_ssh_aths_url}/" "${securedrop_ansible_base}/inventory"
    sed -i "s/mon ansible_ssh_host=.* /mon ansible_ssh_host=${lookup_mon_ssh_aths_url}/" "${securedrop_ansible_base}/inventory"
  fi
}

function configure_torrc_additions()
{
  if is_admin_workstation; then
    # Store all THS URLs in the torrc_additions file. The securedrop_init.py script
    # will add these values to /etc/tor/torrc on boot via a NetworkManager hook.
    cat - <<< "# HidServAuth lines for SecureDrop's authenticated hidden services" \
      "${securedrop_ansible_base}/app-ssh-aths" \
      "${securedrop_ansible_base}/mon-ssh-aths" \
      "${securedrop_ansible_base}/app-document-aths" > $torrc_additions
  else
    # Using a different approach for grabbing the Document ATHS info on the
    # Journalist Workstation, to avoid prompting Journalists unnecessarily on
    # subsequent runs of this script (to clean up legacy changes).
    cat - <<< "# HidServAuth lines for SecureDrop's authenticated hidden services" \
      <(prompt_for_document_aths_info) > "$torrc_additions"
  fi

}

function create_desktop_shortcuts()
{
  # Create user-friendly desktop icons, with the SecureDrop logo, for the
  # Source and Document Interfaces. Double-clicking on the icons will
  # open Tor Browser and navigate directly to the page. For the Document Interface,
  # the ATHS value must be present in /etc/tor/torrc for the connection to resolve.
  echo "Exec=/usr/local/bin/tor-browser $(lookup_document_aths_url)" >> "${securedrop_dotfiles}/document.desktop"
  echo "Exec=/usr/local/bin/tor-browser $(lookup_source_ths_url)" >> "${securedrop_dotfiles}/source.desktop"

  # Copy launchers to Desktop.
  cp -f "${securedrop_dotfiles}/document.desktop" "${amnesia_desktop}"
  cp -f "${securedrop_dotfiles}/source.desktop" "${amnesia_desktop}"

  # Copy icons to Applications menu.
  cp -f "${securedrop_dotfiles}/document.desktop" "${amnesia_home}/.local/share/applications"
  cp -f "${securedrop_dotfiles}/source.desktop" "${amnesia_home}/.local/share/applications"

  # make it all persistent
  sudo -u amnesia mkdir -p "${tails_live_dotfiles}/Desktop"
  sudo -u amnesia mkdir -p "${tails_live_dotfiles}/.local/share/applications"
  cp -f "${securedrop_dotfiles}/document.desktop" "${tails_live_dotfiles}/Desktop"
  cp -f "${securedrop_dotfiles}/source.desktop" "${tails_live_dotfiles}/Desktop"
  cp -f "${securedrop_dotfiles}/document.desktop" "${tails_live_dotfiles}/.local/share/applications"
  cp -f "${securedrop_dotfiles}/source.desktop" "${tails_live_dotfiles}/.local/share/applications"
}

function set_permissions_on_desktop_shortcuts()
{
  # Follow up function to enforce correct permissions and ownership
  # on desktop shortcuts for Document and Source Interfaces. Separated
  # into function to aid readability.
  chown amnesia:amnesia \
    "${amnesia_desktop}/document.desktop" \
    "${amnesia_desktop}/source.desktop" \
    "${amnesia_home}/.local/share/applications/document.desktop" \
    "${amnesia_home}/.local/share/applications/source.desktop" \
    "${tails_live_dotfiles}/.local/share/applications/document.desktop" \
    "${tails_live_dotfiles}/.local/share/applications/source.desktop" \
    "${tails_live_dotfiles}/Desktop/document.desktop" \
    "${tails_live_dotfiles}/Desktop/source.desktop"

  chmod 700 \
    "${amnesia_desktop}/document.desktop" \
    "${amnesia_desktop}/source.desktop" \
    "${amnesia_home}/.local/share/applications/document.desktop" \
    "${amnesia_home}/.local/share/applications/source.desktop" \
    "${tails_live_dotfiles}/.local/share/applications/document.desktop" \
    "${tails_live_dotfiles}/.local/share/applications/source.desktop" \
    "${tails_live_dotfiles}/Desktop/document.desktop" \
    "${tails_live_dotfiles}/Desktop/source.desktop"
}

function configure_network_manager_hook()
{
  # Install a persistent NetworkManager hook to write ATHS values to the
  # system /etc/tor/torrc, so the Document Interface can be accessed via
  # Tor Browser. On the Admin Workstation, the SSH ATHS values will also
  # be added. The hook will run on "up" for any interface other than loopback,
  # and is carefully ordered to run AFTER the Tails Tor hook and BEFORE the
  # Tails Apt update hook.
  if ! grep -q 'custom-nm-hooks' "${tails_live_persistence}/persistence.conf"; then
    echo "/etc/NetworkManager/dispatcher.d	source=custom-nm-hooks,link" >> "${tails_live_persistence}/persistence.conf"
  fi
  mkdir -p "${tails_live_persistence}/custom-nm-hooks"

  cp -f 65-configure-tor-for-securedrop.sh "${tails_live_persistence}/custom-nm-hooks"
  cp -f 65-configure-tor-for-securedrop.sh "$network_manager_dispatcher"
  chown root:root \
    "${tails_live_persistence}/custom-nm-hooks/65-configure-tor-for-securedrop.sh" \
    "${network_manager_dispatcher}/65-configure-tor-for-securedrop.sh"
  chmod 755 \
    "${tails_live_persistence}/custom-nm-hooks/65-configure-tor-for-securedrop.sh" \
    "${network_manager_dispatcher}/65-configure-tor-for-securedrop.sh"

  # Run the SecureDrop init script. Among other things, implements the torrc
  # additions configured by this script. See `securedrop_init.py` for details.
  /usr/bin/python "${securedrop_dotfiles}/securedrop_init.py"
}

function print_success_message()
{
  cat <<SD_COMPLETE_MSG1
Successfully configured Tor and set up desktop bookmarks for SecureDrop!
You will see a notification appear on your screen when Tor is ready.

The Document Interface's Tor onion URL is: http://$(lookup_document_aths_url)
The Source Interfaces's Tor onion URL is: http://$(lookup_source_ths_url)
SD_COMPLETE_MSG1

  # We're assuming the SSH aliases have been set up as long as ~/.ssh/config exists.
  if is_admin_workstation; then
    cat <<SD_COMPLETE_MSG2
The App Server's SSH hidden service address is: $(lookup_app_ssh_aths_url)
The Monitor Server's SSH hidden service address is: $(lookup_mon_ssh_aths_url)
SSH aliases are set up. You can use them with 'ssh app' and 'ssh mon'.
SD_COMPLETE_MSG2
  fi
}

function main()
{
  # Wrapper function for ordering all the helpers.
  validate_tails_environment
  cleanup_legacy_artifacts

  copy_securedrop_dotfiles
  set_permissions_on_securedrop_dotfiles

  if is_admin_workstation; then
    configure_ansible_apt_persistence
    configure_ssh_aliases
    update_ansible_inventory
  fi

  configure_torrc_additions
  create_desktop_shortcuts
  set_permissions_on_desktop_shortcuts
  configure_network_manager_hook

  print_success_message
}

main
exit 0
