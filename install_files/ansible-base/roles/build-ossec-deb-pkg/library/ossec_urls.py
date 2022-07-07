#!/usr/bin/env python
DOCUMENTATION = """
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
    default: "3.6.0"
    required: no
notes:
  - The OSSEC version to download is hardcoded to avoid surprises.
    If you want a newer version than the current default, you should
    pass the version in via I(ossec_version).
"""
EXAMPLES = """
- ossec_urls:
    ossec_version: "3.6.0"
"""


HAS_REQUESTS = True
try:
    import requests  # lgtm [py/unused-import] # noqa: F401
except ImportError:
    HAS_REQUESTS = False


class OSSECURLs:
    def __init__(self, ossec_version):
        self.REPO_URL = "https://github.com/ossec/ossec-hids"
        self.ossec_version = ossec_version
        self.ansible_facts = dict(
            ossec_version=self.ossec_version,
            ossec_tarball_filename=self.ossec_tarball_filename,
            ossec_tarball_url=self.ossec_tarball_url,
            ossec_signature_filename=self.ossec_signature_filename,
            ossec_signature_url=self.ossec_signature_url,
        )

    @property
    def ossec_tarball_filename(self):
        return "ossec-hids-{}.tar.gz".format(self.ossec_version)

    @property
    def ossec_tarball_url(self):
        return self.REPO_URL + "/archive/{}.tar.gz".format(self.ossec_version)

    @property
    def ossec_signature_url(self):
        return self.REPO_URL + "/releases/download/{}/{}".format(
            self.ossec_version, self.ossec_signature_filename
        )

    @property
    def ossec_signature_filename(self):
        return "ossec-hids-{}.tar.gz.asc".format(self.ossec_version)


def main():
    module = AnsibleModule(  # noqa: F405
        argument_spec=dict(
            ossec_version=dict(default="3.6.0"),
        ),
        supports_check_mode=False,
    )
    if not HAS_REQUESTS:
        module.fail_json(msg="requests required for this module")

    ossec_version = module.params["ossec_version"]
    try:
        ossec_config = OSSECURLs(ossec_version=ossec_version)
    except Exception:
        msg = (
            "Failed to find checksum information for OSSEC v{}."
            "Ensure you have the proper release specified, "
            "and check the download page to confirm: "
            "http://www.ossec.net/?page_id=19".format(ossec_version)
        )
        module.fail_json(msg=msg)

    results = ossec_config.ansible_facts

    if results:
        module.exit_json(changed=False, ansible_facts=results)
    else:
        msg = "Failed to fetch OSSEC URL facts."
        module.fail_json(msg=msg)


from ansible.module_utils.basic import *  # noqa E402,F403

main()
