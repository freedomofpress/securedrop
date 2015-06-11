# OSSEC for Ubuntu
OSSEC server and agent packages for Ubuntu

This repository contains all of the code and documentation related to the generic OSSEC packages maintained by the Freedom of the Press Foundation for all SecureDrop instances.

## Verifying the packages

OSSEC doesn't provide a sha256 checksum for their download. They do provide a MD5 and SHA1. OSSEC also doesn't sign their checksum file but the download page is over HTTPS now.

Ansible only has options to check a sha256 or md5 checksum not a sha1 checksum.

### Derive the OSSEC archive sha256 checksum

* Download OSSEC archive and checksum file to your host.
  * The OSSEC download url is: http://www.ossec.net/?page_id=19
  * Follow the stable download link for the `ossec-hids-{{ VERSION }}-tar.gz` and `checksum`:

```
Latest Stable Release (2.8.2)
Server/Agent 2.8.2 – Linux/BSD
```

* Verify sha1 and md5 checksum
* Generate the sha256 checksum of the verified download

## Update vars in the ansible playbook

The vars for building the deb packages are in `ansible/build-deb-pkgs.yml`

### Update

* `version` is correct upstream OSSEC version
* `download_checksum_sha256` is the upstream OSSEC downloads sha256 checksum derived earlier.
* `download_checksum_md5` is the value from the `checksum` file on the OSSEC download page.

### Verify:

* The download url did not change. If it did update `download_url`
* The naming convention for the file name in the url did not change. If it did update `download_name`
* The naming convention for the OSSEC archive did not change. If it did update `archive_name`

### Example
For OSSEC version 2.8.2 updated and verified these values in `ansible/build-deb-pkgs.yml`

```
    version: "2.8.2"
    download_url: "https://github.com/ossec/ossec-hids/archive"
    download_name: "{{ version }}.tar.gz"
    download_checksum_sha256: "61e0892175a79fe119c8bab886cd41fcc3be9b84526600b06c18fa178a59cb34"
    download_checksum_md5: "3036d5babc96216135759338466e1f79"
    archive_name: "ossec-hids-{{ download_name }}"
```

## Use Vagrant to build the deb packages

* First time, run `vagrant up`.

* To rebuild packages you can just run `vagrant provision`.

The `ossec-server-VERSION-amd64.deb` and `ossec-agent-VERSION-amd64.deb` packages will be in the ./build directory.

These package will need to be moved to the securedrop repo's ./build directory for testing in that environment.
