#!/opt/venvs/securedrop-app-code/bin/python

import os
import sys

os.environ["CRYPTOGRAPHY_ALLOW_OPENSSL_102"] = "True"
sys.path.insert(0, "/var/www/securedrop")

# import logging
# logging.basicConfig(stream=sys.stderr)

from source import app as application
