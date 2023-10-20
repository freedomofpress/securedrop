#!/opt/venvs/securedrop-app-code/bin/python
"""
Benchmark operations of redwood/Sequoia vs pretty-bad-protocol/GPG

SecureDrop theoretically accepts submissions up to 500MB, so we
benchmark how long encrypting each size takes
"""

import os
import sys
import tempfile
import timeit
from io import BytesIO
from pathlib import Path

import pretty_bad_protocol as gnupg

import redwood

os.environ["USERNAME"] = "www-data"

PASSPHRASE = "correcthorsebatterystaple"
COUNTER = 0
FAST = "--fast" in sys.argv


def format_time(dt):
    """Copied out of timeit.main()"""
    units = {"nsec": 1e-9, "usec": 1e-6, "msec": 1e-3, "sec": 1.0}
    precision = 3
    scales = [(scale, unit) for unit, scale in units.items()]
    scales.sort(reverse=True)
    for scale, unit in scales:
        if dt >= scale:
            break

    return "%.*g %s" % (precision, dt / scale, unit)


sizes = [
    (5_000, "5KB"),
    (50_000, "50KB"),
    (500_000, "500KB"),
    (5_000_000, "5MB"),
]
if not FAST:
    sizes.extend(
        [
            (50_000_000, "50MB"),
            (500_000_000, "500MB"),
        ]
    )

r_public_key, r_secret_key, r_fingerprint = redwood.generate_source_key_pair(PASSPHRASE, "foobar")
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    gpg = gnupg.GPG(
        binary="gpg2",
        homedir=str(tmpdir),
        options=["--pinentry-mode loopback", "--trust-model direct"],
    )
    g_fingerprint = gpg.gen_key(
        gpg.gen_key_input(
            passphrase=PASSPHRASE,
            name_email="foobar",
            key_type="RSA",
            key_length=4096,
            name_real="Source Key",
            creation_date="2013-05-14",
            expire_date="0",
        )
    ).fingerprint
    g_public_key = gpg.export_keys(g_fingerprint)
    if not g_public_key:
        raise RuntimeError("failed exporting public key")

    for (input_bytes, human_bytes) in sizes:
        slow = input_bytes >= 50_000_000
        loops = 10 if slow else 100
        decrypt = not slow
        plaintext = tmpdir / "message.txt"
        plaintext.write_text("A" * input_bytes)
        if decrypt:
            ciphertext = tmpdir / "message.asc"
            if ciphertext.exists():
                # Delete before we overwrite it.
                ciphertext.unlink()
            redwood.encrypt_stream([r_public_key, g_public_key], plaintext.open(mode="rb"), ciphertext)
            ciphertext_bytes = ciphertext.read_bytes()

        def redwood_encrypt(clean=False):
            global COUNTER
            COUNTER += 1
            ciphertext = tmpdir / f"message-{COUNTER}.asc"

            redwood.encrypt_stream([r_public_key], plaintext.open(mode="rb"), ciphertext)
            if clean:
                ciphertext.unlink()

        def redwood_decrypt():
            redwood.decrypt(ciphertext_bytes, r_secret_key, PASSPHRASE)

        def gpg_encrypt(clean=False):
            global COUNTER
            COUNTER += 1
            ciphertext = tmpdir / f"message-{COUNTER}.asc"
            res = gpg.encrypt(
                plaintext.open(mode="rb"),
                g_fingerprint,
                output=str(ciphertext),
                always_trust=True,
                armor=False,
            )
            if not res.ok:
                raise RuntimeError("gpg encryption failed")
            if clean:
                ciphertext.unlink()

        def gpg_decrypt():
            res = gpg.decrypt_file(BytesIO(ciphertext_bytes), passphrase=PASSPHRASE)
            if not res.ok:
                raise RuntimeError(res.stderr)

        print(f"== {human_bytes} ({loops} & 10 loops) ==")
        r_duration = timeit.repeat(lambda: redwood_encrypt(clean=slow), number=loops)
        print(f"redwood encrypt: {[format_time(dt) for dt in r_duration]}")
        g_duration = timeit.repeat(lambda: gpg_encrypt(clean=slow), number=loops)
        print(f"gpg encrypt    : {[format_time(dt) for dt in g_duration]}")
        if decrypt:
            r2_duration = timeit.repeat(redwood_decrypt, number=10)
            print(f"redwood decrypt: {[format_time(dt) for dt in r2_duration]}")
            g2_duration = timeit.repeat(gpg_decrypt, number=10)
            print(f"gpg decrypt    : {[format_time(dt) for dt in g2_duration]}")
