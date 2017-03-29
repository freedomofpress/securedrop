#!/usr/bin/env python

import glob
import os
import shutil
import subprocess
import sys

SECUREDROP_DIR = sys.argv[1]
BUILD_DIR = sys.argv[2]
GLOBS = {'.': ['*.py', 'COPYING', 'wordlist'],
         'dictionaries': ['*.txt'],
         'journalist_templates': ['*.html'],
         'management': ['*.py'],
         'requirements': ['securedrop-requirements.txt'],
         'source_templates': ['*.html'],
         'static/js': ['*.js'],
         'static/js/libs': ['*.js'],
         'tests': ['*.py'],
         'tests/files': ['*.py'],
         'tests/functional': ['*.py'],
         'tests/utils': ['*.py'],
         }
PATHS = ['static/fonts', 'static/i']

os.makedirs(BUILD_DIR)

for rel_path, glob_list in GLOBS.iteritems():
    try:
        os.makedirs(os.path.join(BUILD_DIR, rel_path))
    except OSError:
        pass
    for glob_str in glob_list:
        matching_paths = glob.glob(os.path.join(SECUREDROP_DIR,
                                                rel_path,
                                                glob_str))
        for path in matching_paths:
            subprocess.check_call([
                "cp", "--preserve=mode,timestamps", path,
                os.path.join(BUILD_DIR, rel_path, os.path.basename(path))])

for rel_path in PATHS:
    subprocess.check_call(["cp", "--preserve=mode,timestamps", "-R",
                           os.path.join(SECUREDROP_DIR, rel_path),
                           os.path.join(BUILD_DIR, rel_path)])

sys.exit(0)
