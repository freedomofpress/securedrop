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
parser.add_argument("pr", type=int, help="the # of the PR to backport")
parser.add_argument("version", help="the release version to target with the backport")
parser.add_argument("remote", default="origin", help="the git remote to use (defaults to origin)")
parser.add_argument("--skip", default=[], action="append", help="don't cherry-pick these commits")
args = parser.parse_args()

title = json.loads(
    subprocess.check_output(["gh", "pr", "view", str(args.pr), "--json", "title"], text=True)
)["title"]
commits = json.loads(
    subprocess.check_output(
        ["gh", "api", "--paginate", f"repos/{{owner}}/{{repo}}/pulls/{args.pr}/commits"], text=True
    )
)

# NB. It's tempting to do something like `set(commit_hashes) -= set(args.skip)`
# here, but we must preserve the order of commits, and it's not worth pulling
# in an ordered-set implementation just for this.
commit_hashes = [commit["sha"] for commit in commits if commit["sha"] not in args.skip]

print(f'Backporting {len(commit_hashes)}/{len(commits)} commits from "{title}"')
branch = f"backport-{args.pr}"
base = f"release/{args.version}"
remote = args.remote
subprocess.check_call(["git", "fetch", remote])
subprocess.check_call(["git", "checkout", "-b", branch, f"{remote}/{base}"])
subprocess.check_call(["git", "cherry-pick", "-x"] + commit_hashes)
if input("OK to push and create PR? [y/N]").lower() != "y":
    sys.exit()
subprocess.check_call(["git", "push", "-u", remote, branch])
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
