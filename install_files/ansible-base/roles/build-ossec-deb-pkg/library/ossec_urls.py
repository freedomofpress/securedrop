#!/usr/bin/env python
DOCUMENTATION = '''
---
module: ossec_urls
short_description: Gather facts for OSSEC download URLs
description:
  - Gather version, checksum, and URL info for OSSEC downloads
author:
    - Conor Schaefer (@conorsch)
    - Freedom of the Press Foundation (@freedomofpress)
requirements:
    - requests
options:
  ossec_version:
    description:
      - version number of release to download
    default: "3.0.0"
    required: no
notes:
  - The OSSEC version to download is hardcoded to avoid surprises.
    If you want a newer version than the current default, you should
    pass the version in via I(ossec_version).
'''
EXAMPLES = '''
- ossec_urls:
    ossec_version: "3.0.0"
'''

import re  # noqa: E402


HAS_REQUESTS = True
try:
    import requests
except ImportError:
    HAS_REQUESTS = False


class OSSECURLs():

    def __init__(self, ossec_version):
        self.ossec_version = ossec_version

        checksums = self.parse_checksums()

        self.ansible_facts = dict(
            ossec_version=self.ossec_version,
            ossec_tarball_filename=self.ossec_tarball_filename,
            ossec_tarball_url=self.ossec_tarball_url,
            ossec_checksum_filename=self.ossec_checksum_filename,
            ossec_checksum_url=self.ossec_checksum_url,
            )

        self.ansible_facts.update(checksums)

    @property
    def ossec_tarball_filename(self):
        return "ossec-hids-{}.tar.gz".format(self.ossec_version)

    @property
    def ossec_tarball_url(self):
        return "https://github.com/ossec/ossec-hids/archive/{}.tar.gz".format(
                self.ossec_version)

    @property
    def ossec_checksum_url(self):
        return "https://github.com/ossec/ossec-hids/releases/download/{}/{}".format(  # noqa: E501
                self.ossec_version, self.ossec_checksum_filename)

    @property
    def ossec_checksum_filename(self):
        return "{}-checksum.txt".format(self.ossec_tarball_filename)

    def parse_checksums(self):
        r = requests.get(self.ossec_checksum_url)
        checksum_regex = re.compile(r'''
                                    ^MD5\(
                                    '''
                                    + re.escape(self.ossec_tarball_filename) +
                                    r'''\)=\s+(?P<ossec_md5_checksum>[0-9a-f]{32})\s+
                                    SHA1\(
                                    '''
                                    + re.escape(self.ossec_tarball_filename) +
                                    r'''\)=\s+(?P<ossec_sha1_checksum>[0-9a-f]{40})$
                                    ''', re.VERBOSE | re.MULTILINE
                                    )
        checksum_list = r.content.rstrip()
        results = re.match(checksum_regex, checksum_list).groupdict()
        return results


def main():
    module = AnsibleModule(  # noqa: F405
        argument_spec=dict(
            ossec_version=dict(default="3.0.0"),
        ),
        supports_check_mode=False
    )
    if not HAS_REQUESTS:
        module.fail_json(msg='requests required for this module')

    ossec_version = module.params['ossec_version']
    try:
        ossec_config = OSSECURLs(ossec_version=ossec_version)
    except:  # noqa: E722
        msg = ("Failed to find checksum information for OSSEC v{}."
               "Ensure you have the proper release specified, "
               "and check the download page to confirm: "
               "http://www.ossec.net/?page_id=19".format(ossec_version))
        module.fail_json(msg=msg)

    results = ossec_config.ansible_facts

    if results:
        module.exit_json(changed=False, ansible_facts=results)
    else:
        msg = "Failed to fetch OSSEC URL facts."
        module.fail_json(msg=msg)


from ansible.module_utils.basic import * # noqa E402,F403
main()
