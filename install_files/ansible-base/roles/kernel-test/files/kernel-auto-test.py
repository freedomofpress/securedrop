#!/usr/bin/python3
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Two tokens are needed because one has account scopes for gists, and the other
# has repository access to create issues.
tokens = json.loads(Path("/etc/github-token.json").read_text())
GITHUB_TOKEN = tokens["issues"]
GIST_TOKEN = tokens["gist"]

state = Path("/etc/kernel-check.json")
if state.exists():
    previous = json.loads(state.read_text())["version"]
else:
    previous = None

current = subprocess.check_output(["uname", "-r"], text=True).strip()
if current == previous:
    print(f"No changes to kernel version (still {previous}), exiting")
    sys.exit(0)

hardware = Path("/sys/devices/virtual/dmi/id/product_name").read_text().strip()

print(f"I am beginning to test {current} on {hardware}")

paxtest = subprocess.run(["paxtest", "blackhat"], stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
    check=False)
fetch = subprocess.check_output(["curl", "-L", "https://meltdown.ovh"])
Path("/tmp/spectre-meltdown-checker.sh").write_bytes(fetch)  # noqa: S108
checker = subprocess.run(
    ["bash", "/tmp/spectre-meltdown-checker.sh", "--no-color"],  # noqa: S108
    stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
    check=False,
)

def create_gist(command, result):
    headers = {
        "Authorization": f"Bearer {GIST_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    data = {
        "description": f"{command} on {hardware} for {current}",
        "public": False,
        "files": {
            f"{command}.log": {"content": result.stdout.decode()},
        },
    }
    req = urllib.request.Request(
        "https://api.github.com/gists",
        data=json.dumps(data).encode(),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())["html_url"]

paxtest_gist = create_gist("paxtest", paxtest)
checker_gist = create_gist("spectre-meltdown-checker.sh", checker)

template = f"""\
Hello SecureDrop team,

Today I tested {current} on {hardware}.

If you're seeing this comment it means it successfully booted!

I ran:
* paxtest, exit code: {paxtest.returncode} ([logs]({paxtest_gist}))
* spectre-meltdown-checker.sh, exit code: {checker.returncode} ([logs]({checker_gist}))

Cheers,
Your friendly kernel testing robot
"""

print(template)

def search_issues(kernel_version):
    headers = {
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    query = urllib.parse.quote(f"repo:freedomofpress/securedrop {kernel_version} in:title state:open")
    url = f"https://api.github.com/search/issues?q={query}"
    print(f"Searching via {url}")
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())["items"]

def create_issue(title, body):
    print("Creating issue")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    url = "https://api.github.com/repos/freedomofpress/securedrop/issues"
    data = json.dumps({"title": title, "body": body}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

def create_comment(issue_number, body):
    print("Leaving comment")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    }
    url = f"https://api.github.com/repos/freedomofpress/securedrop/issues/{issue_number}/comments"
    data = json.dumps({"body": body}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

issue_body = f"""\
Dearest SecureDrop developers,

This issue tracks the testing and release of Linux kernel {current}.

See https://developers.securedrop.org/en/latest/kernel.html for details.

P.S. This issue was automatically created by the [kernel-auto-test.py](https://github.com/freedomofpress/securedrop/blob/kernel-test/install_files/ansible-base/roles/kernel-test/files/kernel-auto-test.py) script.
"""

# Search for existing issue
issues = search_issues(current)

# Create or update issue
if issues:
    existing_issue = issues[0]
    create_comment(existing_issue["number"], template)
else:
    new_issue = create_issue(f"New Linux kernel: {current}", issue_body)
    create_comment(new_issue["number"], template)

print("All done!")
state.write_text(json.dumps({"version": current}))
