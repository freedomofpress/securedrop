#!/usr/bin/python

import os
import json
import re
from operator import itemgetter
from ansible.module_utils.basic import AnsibleModule

try:
    import googleapiclient.discovery
    from google.oauth2.service_account import Credentials
except ImportError:
    HAS_GOOGLE_LIBRARIES = False
else:
    HAS_GOOGLE_LIBRARIES = True

ANSIBLE_METADATA = {
    'metadata_version': '0.1',
    'supported_by': 'fpf',
    'status': ['preview']
}

DOCUMENTATION = '''
module: gce_image_facts
short_description: Gather image details from GCE
description:
    - Gather image facts from Google Compute Engine
author: 'Michael Sheinberg (github.com/msheiny)'
options:
  regex:
    description:
        - A regular expression to pass over the image names that are returned
    required: false
  sort_by_time:
    description:
        - Sort the images returned by creation date.
    required: false
  filter:
    description:
        - GCE image filter to apply. Must match spec as defined on
          https://cloud.google.com/compute/docs/reference/rest/v1/images/list
    required: false
requirements: []
    default: {}
'''

EXAMPLES = '''
- gce_image_facts:
    sort_by_time: yes
    filter: "(family = \"fpf-securedrop\")"
'''

RETURN = '''
gce_images:
    returned: on success
    description: >
        List of GCE images found with the provided parameters.
    type: list
    sample: "[
        {
            "archiveSizeBytes": "3198326784",
            "creationTimestamp": "2018-10-18T14:22:15.702-07:00",
            "description": "Created by Packer",
            "diskSizeGb": "30",
            "family": "fpf-securedrop",
            "guestOsFeatures": [
                {
                    "type": "VIRTIO_SCSI_MULTIQUEUE"
                }
            ],
            "id": "234243243",
            "kind": "compute#image",
            "labelFingerprint": "42WmSpB8rSM=",
            "licenseCodes": [
                "1002001",
                "1000201"
            ],
            "licenses": [],
            "name": "ci-nested-virt-xenial-342424245",
            "selfLink": "",
            "sourceDisk": "",
            "sourceDiskId": "342432423424",
            "sourceType": "RAW",
            "status": "READY"

        }
    ]"
'''


class GoogleComputeImages(object):

    def __init__(self,
                 acct_dict=os.environ['GOOGLE_CREDENTIALS'],
                 scope=["https://www.googleapis.com/auth/compute.readonly"],
                 project="securedrop-ci",
                 zone="us-west1-c",
                 region="us-west1",
                 filter="",
                 email="ci-tester@securedrop-ci.iam.gserviceaccount.com"):

        gce_json_dict = json.loads(acct_dict)
        creds = Credentials.from_service_account_info(gce_json_dict)

        self.compute = googleapiclient.discovery.build('compute', 'v1',
                                                       credentials=creds)
        self.region = region
        self.zone = zone
        self.project = project
        self.filter = filter

    def list_images(self):
        image_result = self.compute.images().list(project=self.project,
                                                  filter=self.filter
                                                  ).execute()
        return image_result['items']


def main():
    argument_spec = dict(
        regex=dict(default="^ci-nested-virt-\w+", type='str', required=False),
        sort_by_time=dict(default=True, type='bool', required=False),
        filter=dict(default="""(family = "fpf-securedrop")""", type='str',
                    required=False)
        )

    module = AnsibleModule(argument_spec=argument_spec)

    image_search_results = []
    google = GoogleComputeImages(filter=module.params['filter'])
    images = google.list_images()

    try:
        for i in images:
            # Filter images through regex
            if re.match(module.params['regex'],
                        i['name']):
                image_search_results.append(i)
    except IndexError:
        # No images found
        image_search_results = []
    else:
        # Sort list items by timestamp
        if module.params['sort_by_time']:
            image_search_results = sorted(image_search_results,
                                          key=itemgetter('creationTimestamp'),
                                          reverse=True)

    if not HAS_GOOGLE_LIBRARIES:
        module.fail_json(msg='google-auth, google-auth-httplib2, '
                             'and google-api-python-client pip dependencies'
                             ' required')

    try:
        module.exit_json(gce_images=image_search_results)
    except googleapiclient.errors.Error as e:
        module.fail_json(msg="Error encountered",
                         Exception=e)


if __name__ == '__main__':
    main()
