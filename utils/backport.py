#!/usr/bin/env python3
"""
Automatically backport a PR to a release branch

./utils/backport.py PR_ID 2.x.x

The `gh` CLI must be set up and already authenticated.
"""
import argparse
import json
import subprocess
import sys

parser = argparse.ArgumentParser(description="Backport a PR")
parser.add_argument("pr", type=int)
parser.add_argument("version")
args = parser.parse_args()

title = json.loads(
    subprocess.check_output(["gh", "pr", "view", str(args.pr), "--json", "title"], text=True)
)["title"]
commits = json.loads(
    subprocess.check_output(
        ["gh", "api", f"repos/{{owner}}/{{repo}}/pulls/{args.pr}/commits"], text=True
    )
)
print(f'Backporting {len(commits)} commits from "{title}"')
branch = f"backport-{args.pr}"
base = f"release/{args.version}"
subprocess.check_call(["git", "fetch", "origin"])
subprocess.check_call(["git", "checkout", "-b", branch, f"origin/{base}"])
subprocess.check_call(["git", "cherry-pick", "-x"] + [commit["sha"] for commit in commits])
if input("OK to push and create PR? [y/N]").lower() != "y":
    sys.exit()
subprocess.check_call(["git", "push", "-u", "origin", branch])
body = f"""\
## Status

Ready for review

## Description of Changes

Backport of #{args.pr}.

## Testing

* [ ] CI is passing
* [ ] base is `{base}`
* [ ] Only contains changes from #{args.pr}.
"""
print(body)

subprocess.check_call(
    [
        "gh",
        "pr",
        "create",
        "--base",
        base,
        "--body",
        body,
        "--title",
        f'[{args.version}] Backport "{title}"',
    ]
)
