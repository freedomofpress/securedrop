# OSSEC for Ubuntu
OSSEC server and agent packages for Ubuntu

This repository contains all of the code and documentation related to the generic OSSEC packages maintained by the Freedom of the Press Foundation for all SecureDrop instances.

## Build the packages

```
bundle install
bundle exec rake
```

The `ossec-server-VERSION-amd64.deb` and `ossec-agent-VERSION-amd64.deb` packages will be in the ./build directory.

These package will need to be moved to the securedrop repo's ./build directory for testing in that environment.

### Verify:

* The download url did not change. If it did update `download_url`
* The naming convention for the file name in the url did not change. If it did update `download_name`
* The naming convention for the OSSEC archive did not change. If it did update `archive_name`

### Update Changelog when changing versions

* `ossec-server/usr/share/doc/ossec-server/changelog.Debian`
* `ossec-agent/usr/share/doc/ossec-agent/changelog.Debian`

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