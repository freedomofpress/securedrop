#!/bin/bash
set -e
set -u


# By default let's assume we're testing against the development VM.
target_host=${1:-development}

# Set env var so that `testinfra/conftest.py` can read in a YAML vars file
# specific to the host being tested.
export SECUREDROP_TESTINFRA_TARGET_HOST="${target_host}"

# Assemble list of role tests to run. Hard-coded per host.
case $target_host in
development*)
  target_roles=(testinfra/app-code testinfra/development)
  ;;
app-staging*)
  target_roles=(testinfra/app
                testinfra/app-code
                testinfra/app-test
                testinfra/common
                testinfra/development/test_xvfb.py
                )
  ;;
mon-staging*)
  target_roles=(testinfra/mon testinfra/common)
  ;;
mon-prod*)
  target_roles=(testinfra/mon)
  ;;
*)
  echo "Unknown host '${target_host}'! Exiting."
  exit 1
  ;;
esac

# Print informative output prior to test run.
echo "Running Testinfra suite against '${target_host}'..."
echo "Target roles: "
for role in ${target_roles[@]:0} ; do
    echo "    - ${role}"
done

# Execute config tests.
testinfra \
    -vv \
    -n auto \
    --connection ansible \
    --ansible-inventory .vagrant/provisioners/ansible/inventory/vagrant_ansible_inventory \
    --hosts "${target_host}" \
    $target_roles
