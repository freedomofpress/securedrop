#!/bin/bash
# Migration script from git-based to debian-package-based SecureDrop installer
# This script performs a one-time migration for existing users
set -e
set -o pipefail

# Error handler - outputs to terminal only (wrapper handles zenity dialogs)
error_exit() {
    local message="$1"
    echo "ERROR: $message" >&2
    exit 1
}

# Check if old config directory exists
OLD_CONFIG_DIR="$HOME/Persistent/securedrop/install_files/ansible-base"
if [[ ! -d "$OLD_CONFIG_DIR" ]]; then
    error_exit "Old configuration directory not found.\n\nExpected: $OLD_CONFIG_DIR\n\nThis script is for migrating existing installations only."
fi
echo "- Old config directory found: $OLD_CONFIG_DIR"

NEW_CONFIG_DIR="$HOME/.config/securedrop-admin"

SITE_SPECIFIC_FILE="$OLD_CONFIG_DIR/group_vars/all/site-specific"

get_site_specific_value() {
    local config_key="$1"
    { grep "^${config_key}:" "${SITE_SPECIFIC_FILE}" || true; } | awk '{print $2}' | tr -d "'\""
}

copy_or_continue() {
    local config_key="$1"
    file_name=$(get_site_specific_value "${config_key}")
    if [[ -n "${file_name}" && "${file_name}" != "''" ]]; then
        if [[ -f "${OLD_CONFIG_DIR}/${file_name}" ]]; then
            cp "${OLD_CONFIG_DIR}/${file_name}" "${NEW_CONFIG_DIR}/"
            echo "- Migrated item ${config_key}: ${file_name}"
        else
            error_exit "Missing file ${file_name} for config item: ${config_key}."
        fi
    fi
}

copy_or_fail() {
    local config_key="$1"
    file_name=$(get_site_specific_value "${config_key}")
    if [[ -n "$file_name" && "$file_name" != "''" ]]; then
        if [[ -f "$OLD_CONFIG_DIR/$file_name" ]]; then
            cp "$OLD_CONFIG_DIR/$file_name" "$NEW_CONFIG_DIR/"
            echo "- Migrated item ${config_key}: ${file_name}"
        else
            error_exit "Missing file ${file_name} for config item: ${config_key}."
        fi
    else
        error_exit "Required config item missing: ${config_key}."
    fi
}

# Check if running on Tails
if [[ ! -f /etc/os-release ]] || ! grep -q 'NAME="Tails"' /etc/os-release; then
    error_exit "This script must be run on Tails.\n\nCurrent system is not Tails."
fi
echo "- Running on Tails"

# Check Tails version >= 7
tails_version=$(grep '^VERSION=' /etc/os-release | cut -d= -f2 | tr -d '"')
tails_major_version=$(echo "$tails_version" | cut -d. -f1)
if (( tails_major_version < 7 )); then
    error_exit "This migration requires Tails 7 or later.\n\nCurrent version: $tails_version\n\nPlease upgrade Tails before migrating."
fi
echo "- Tails version: $tails_version"

# Verify root script exist
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_SCRIPT="$SCRIPT_DIR/configure-tails-persistence.sh"
if [[ ! -f "$ROOT_SCRIPT" ]]; then
    error_exit "Helper script not found.\n\nExpected: $ROOT_SCRIPT"
fi

# Run the root script
echo "Configuring Tails persistence (requires password)..."
if ! pkexec bash "$ROOT_SCRIPT"; then
    error_exit "Failed to configure Tails persistence."
fi

# Verify installation
if ! command -v /usr/bin/securedrop-admin >/dev/null 2>&1; then
    error_exit "Package installed but securedrop-admin command not found.\n\nInstallation may have failed."
fi
echo "- securedrop-admin command is available"

# Copy admin-specific config, starting with the site-specific config file
if [[ -f "$SITE_SPECIFIC_FILE" ]]; then
    cp "$SITE_SPECIFIC_FILE" "$NEW_CONFIG_DIR/"
    echo "- Migrated file: site-specific"

    # Parse site-specific for GPG public key filenames and copy them -
    # the Submission Public Key and OSSEC Key should always be present
    copy_or_fail "securedrop_app_gpg_public_key"
    copy_or_fail "ossec_alert_gpg_public_key"

    # The journalist alert key is optional
    copy_or_continue "journalist_alert_gpg_public_key"

    # If HTTPS support for the source interface is enabled, copy the files needed
    https_enabled=$(get_site_specific_value securedrop_app_https_on_source_interface)
    if [[ -n "$https_enabled" && "$https_enabled" = "true" ]]; then
        echo "- HTTPS enabled for the Source Interface, copying files:"
        copy_or_fail "securedrop_app_https_certificate_cert_src"
        copy_or_fail "securedrop_app_https_certificate_key_src"
        copy_or_fail "securedrop_app_https_certificate_chain_src"
    fi

    # if SSH-over-Tor is enabled, copy the needed auth files
    ssh_tor_enabled=$(get_site_specific_value enable_ssh_over_tor)
    if [[ -n "$ssh_tor_enabled" && "$ssh_tor_enabled" = "true" ]]; then
        for auth_file in app-ssh.auth_private mon-ssh.auth_private; do
            if [[ -f "$OLD_CONFIG_DIR/$auth_file" ]]; then
                cp "$OLD_CONFIG_DIR/$auth_file" "$NEW_CONFIG_DIR/"
                echo "- Migrated file: $auth_file"
            else
                error_exit "Missing required Tor connection file: $auth_file"
            fi
        done
    fi

    # Copy the tor v3 auth keys - if site-specific is present then they should be too
    if [[ -f "$OLD_CONFIG_DIR/tor_v3_keys.json" ]]; then
        cp "$OLD_CONFIG_DIR/tor_v3_keys.json" "$NEW_CONFIG_DIR/"
        echo "- Migrated file: tor_v3_keys.json"
    else
        error_exit "Missing file ${OLD_CONFIG_DIR}/tor_v3_keys.json."
    fi
else
    echo "! Not found (skipping): site-specific - copying journalist-specific files only"
fi

# Copy SI and JI config files - these should be present for both admins and journalists

for file_name in app-journalist.auth_private app-sourcev3-ths; do
    if [[ -f "$OLD_CONFIG_DIR/$file_name" ]]; then
        cp "$OLD_CONFIG_DIR/$file_name" "$NEW_CONFIG_DIR/"
        echo "- Migrated file: $file_name"
    else
        error_exit "Missing required Tor connection file: $file_name"
    fi
done

# Set correct permissions
chmod 700 "$NEW_CONFIG_DIR"
if compgen -G "$NEW_CONFIG_DIR/*" > /dev/null; then
    chmod 600 "$NEW_CONFIG_DIR"/*
    echo "- Set permissions on config directory and files"
else
    echo "! No files in config directory to set permissions on"
fi

# Delete update flag so GUI updater doesn't try to run again
UPDATE_FLAG="$HOME/Persistent/.securedrop/securedrop_update.flag"
if [[ -f "$UPDATE_FLAG" ]]; then
    rm "$UPDATE_FLAG"
    echo "- Deleted GUI updater flag: $UPDATE_FLAG"
else
    echo "! GUI updater flag not found (already deleted?): $UPDATE_FLAG"
fi
