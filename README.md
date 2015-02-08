# OSSEC for Ubuntu
OSSEC server and agent packages for Ubuntu

This repository contains all of the code and documentation related to the generic OSSEC packages maintained by the Freedom of the Press Foundation for all SecureDrop instances.

## Building the packages

1. Ensure that the correct version, sha and md5 values are defined in the playbook
`ansible/build-deb-pkgs.yml`

2. First time, run `vagrant up`. To rebuild packages you can just run `vagrant provision`.

The `ossec-server-VERSION-amd64.deb` and `ossec-agent-VERSION-amd64.deb` packages will be in the ./build directory.
