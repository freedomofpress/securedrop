#!/usr/bin/python3
"""
Build a Python wheel containing the Rust redwood code

Ideally we'd use maturin for this, but it has a big dependency tree
that's not really worth reviewing, so this is mostly a stop-gap until
we can use a Debian-packaged version. This is only intended to run in
the SecureDrop dev and packaging environments.

At a high level, this script:
* Compiles the Rust code into a shared library (libredwood.so)
* Copy and rename that into the Python package structure
* Build a Python wheel using setuptools
"""

import argparse
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

parser = argparse.ArgumentParser(description="Build a wheel")
parser.add_argument("--release", action="store_true", help="Build in release mode")
parser.add_argument("--redwood", type=Path, help="Path to redwood folder")
parser.add_argument("--target", type=Path, help="Path to target folder")
args = parser.parse_args()

os.chdir(args.redwood)

if args.release:
    flavor = "release"
    cargo_flags = ["--release"]
else:
    flavor = "debug"
    cargo_flags = []

env = {"CARGO_TARGET_DIR": str(args.target), **os.environ}

print("Starting to build Rust code")
subprocess.check_call(["cargo", "build", "--lib", "--locked"] + cargo_flags, env=env)
print("Copying libredwood.so into package")
libredwood = args.target / flavor / "libredwood.so"
if not libredwood.exists():
    print(f"Error: Can't find libredwood.so (looked for {libredwood})")
    sys.exit(1)

so_destination = args.redwood / "redwood" / ("redwood" + sysconfig.get_config_var("EXT_SUFFIX"))
shutil.copy2(libredwood, so_destination)

print("Building wheel")
subprocess.check_call([sys.executable, "-m", "pip", "wheel", "."])
# Yes the wheel name is wrong (this is not a pure-Python wheel),
# but it doesn't matter, this is only an intermediate step as it will
# be immediately unpacked and installed into the virtualenv.
whl = Path("redwood-0.1.0-py3-none-any.whl")
if not whl.exists():
    print("Error: Can't find the wheel")
    sys.exit(1)
print(f"Built at: {whl.absolute()}")
