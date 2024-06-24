# Mimic CI, set up the all the required environment variables to match the
# nested virtualization tests. This file should be sourced by the GCE CI
# tooling in order to prepare the env.

# If these scripts are run on developer workstations, the CI env
# vars populated by CircleCI won't be present; make a sane default.
if [ -z "${CIRCLE_BUILD_NUM:-}" ]; then
    export CIRCLE_BUILD_NUM="${USER}"
fi

# Set common vars we'll need throughout the CI scripts.
TOPLEVEL="$(git rev-parse --show-toplevel)"
export TOPLEVEL
GCE_CREDS_FILE="${TOPLEVEL}/.gce.creds"
export GCE_CREDS_FILE
export BUILD_NUM="${CIRCLE_BUILD_NUM}"
export PROJECT_ID="securedrop-ci"
export JOB_NAME="sd-ci-nested"
export GCLOUD_MACHINE_TYPE="c2-standard-8"
GCLOUD_CONTAINER_VER="$(cat "${TOPLEVEL}/devops/gce-nested/gcloud-container.ver")"
export GCLOUD_CONTAINER_VER
export CLOUDSDK_COMPUTE_ZONE="us-west1-c"
export EPHEMERAL_DIRECTORY="/tmp/gce-nested"
export FULL_JOB_ID="${JOB_NAME}-${BUILD_NUM}"
export SSH_USER_NAME=sdci
export SSH_PRIVKEY="${EPHEMERAL_DIRECTORY}/gce"
export SSH_PUBKEY="${SSH_PRIVKEY}.pub"

# The GCE credentials are stored as an env var on the CI platform,
# retrievable via GOOGLE_CREDENTIALS. Let's read that value, decode it,
# and write it to disk in the CI environment so the gcloud tooling
# can authenticate.
function generate_gce_creds_file() {
    # First check if there is an existing cred file
    if [ ! -f "${GCE_CREDS_FILE}" ]; then

        # Oh there isnt one!? Well do we have a google cred env var?
        if [ -z "${GOOGLE_CREDENTIALS:-}" ]; then
            echo "ERROR: Make sure you set env var GOOGLE_CREDENTIALS"
        # Oh we do!? Well then lets process it
        else
            # Does the env var have a google string it in.. assume we are a json
            if [[ "$GOOGLE_CREDENTIALS" =~ google ]]; then
                echo "$GOOGLE_CREDENTIALS" > "$GCE_CREDS_FILE"
            # otherwise assume we are a base64 string. Thats needed for CircleCI
            else
                echo "$GOOGLE_CREDENTIALS" | base64 --decode > "$GCE_CREDS_FILE"
            fi
        fi
    fi
}

# Wrapper function to communicate with the gcloud API. Ensure gcloud-sdk
# container is running, and if so, pass all args to it.
function gcloud_call() {
    if ! (docker ps | grep -q gcloud_tool); then
        docker run --rm \
                --env="CLOUDSDK_COMPUTE_ZONE=${CLOUDSDK_COMPUTE_ZONE}" \
                --volume "${EPHEMERAL_DIRECTORY}/gce.pub:/gce.pub" \
                --volume "${GCE_CREDS_FILE}:/gce-svc-acct.json" \
                --name gcloud_tool -d \
                "quay.io/freedomofpress/gcloud-sdk:${GCLOUD_CONTAINER_VER}" \
                background >/dev/null 2>&1
        # Give container a moment for gcloud tooling to authenticate
        # Kept falling over on first calls without this
        sleep 3
    fi

    docker exec -i gcloud_tool \
        /usr/bin/gcloud --project "${PROJECT_ID}" "$@"
}


generate_gce_creds_file
