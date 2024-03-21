#!/usr/bin/python3

import json
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path
from smtplib import SMTP_SSL

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
paxtest = subprocess.run(["paxtest", "blackhat"], capture_output=True, check=False)

fetch = subprocess.check_output(["curl", "-L", "https://meltdown.ovh"])
Path("/tmp/spectre-meltdown-checker.sh").write_bytes(fetch)  # noqa: S108
checker = subprocess.run(
    ["bash", "/tmp/spectre-meltdown-checker.sh", "--no-color"],  # noqa: S108
    capture_output=True, check=False
)

template = f"""\
Hello SecureDrop team,
Today I tested {current} on {hardware}.
If you're getting this email it means it successfully booted!
I ran:
* paxtest, exit code: {paxtest.returncode}
* spectre-meltdown-checker.sh, exit code: {checker.returncode}
Logs for both are attached.
Cheers,
Your friendly kernel testing robot
"""

message = EmailMessage()
message['Subject'] = f"kernel testing {current} on {hardware}"
message['To'] = "securedrop@freedom.press"
message['From'] = "kernel-test-farm@securedrop.org"
message.set_content(template)

# Add attachments
message.add_attachment(paxtest.stdout, maintype="text", subtype="plain",
    filename="paxtest.stdout.log")
message.add_attachment(paxtest.stderr, maintype="text", subtype="plain",
    filename="paxtest.stderr.log")
message.add_attachment(checker.stdout, maintype="text", subtype="plain",
    filename="checker.stdout.log")
message.add_attachment(paxtest.stderr, maintype="text", subtype="plain",
    filename="checker.stderr.log")
print(message.as_string())

credentials = json.loads(Path("/etc/mailstuff.json").read_text())

with SMTP_SSL(credentials["host"]) as server:
    server.login(credentials["username"], credentials["password"])
    server.send_message(message)

print("Sent!")
state.write_text(json.dumps({"version": current}))
