#!/bin/bash
# Create the GCE instance that will host the Staging VMs. All this script
# does is provision the instances; the actual config and tests are
# handled by the adjacent gce-runner script.
set -u
set -e

TOPLEVEL="$(git rev-parse --show-toplevel)"
# shellcheck source=devops/gce-nested/ci-env.sh
. "${TOPLEVEL}/devops/gce-nested/ci-env.sh"


function create_gce_ssh_key() {
    # Ensure SSH key in-place
    if [[ ! -f "$SSH_PUBKEY" ]]; then
        mkdir -p "$EPHEMERAL_DIRECTORY"
        ssh-keygen -f "$SSH_PRIVKEY" -q -P ""
    fi
}

# Lookup the latest GCE image available for use with SD CI.
# Value will be used in the create call.
function find_latest_ci_image() {
    #gcloud_call compute images list \
    #    --filter="family:fpf-securedrop AND name ~ ^ci-nested-virt" \
    #    --sort-by=~Name --limit=1 --format="value(Name)"
    # Return hardcoded image id to prevent newer builds from breaking CI
    echo "ci-nested-virt-buster-1633365108"
}

# Call out to GCE API and start a new instance, designating
# the SD CI network settings.
function create_sd_ci_gce_instance() {
  # First check that a suitable instance isn't already running.
  if ! gcloud_call compute instances describe "${FULL_JOB_ID}" >/dev/null 2>&1; then
      # Fetch latest image id, for use in create call
      local ci_image
      ci_image="$(find_latest_ci_image)"
      # Fire-up remote instance
      gcloud_call compute instances create "${FULL_JOB_ID}" \
          --image="$ci_image" \
          --network securedropci \
          --subnet ci-subnet \
          --boot-disk-type=pd-ssd \
          --machine-type="${GCLOUD_MACHINE_TYPE}" \
          --metadata "ssh-keys=${SSH_USER_NAME}:$(cat $SSH_PUBKEY)"

      # Give box a few more seconds for SSH to become available
      sleep 20
  fi
}

# Main logic
create_gce_ssh_key
create_sd_ci_gce_instance
