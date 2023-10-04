from pathlib import Path

import pretty_bad_protocol as gnupg

import redwood


def test_gpg_export_keys(tmp_path):
    gpg = gnupg.GPG(
        binary="gpg2",
        homedir=str(tmp_path),
        options=["--pinentry-mode loopback", "--trust-model direct"],
    )
    passphrase = "correcthorsebatterystaple"
    gen_key_input = gpg.gen_key_input(
        passphrase=passphrase,
        name_email="example@example.org",
        key_type="RSA",
        key_length=4096,
        name_real="example",
    )
    fingerprint = gpg.gen_key(gen_key_input)
    print(fingerprint)
    public_key = gpg.export_keys(fingerprint)
    assert redwood.is_valid_public_key(public_key)
    secret_key = gpg.export_keys(fingerprint, secret=True, passphrase=passphrase)
    assert secret_key.startswith("-----BEGIN PGP PRIVATE KEY BLOCK-----")

    # Now verify the exported key pair is usable by Sequoia
    message = "GPG to Sequoia-PGP, yippe!"
    ciphertext = tmp_path / "encrypted.asc"
    redwood.encrypt_message([public_key], message, ciphertext)
    decrypted = redwood.decrypt(ciphertext.read_bytes(), secret_key, passphrase).decode()
    assert decrypted == message

    # Test some failure cases for exporting the secret key:
    # bad passphrase
    assert gpg.export_keys(fingerprint, secret=True, passphrase="wrong") == ""
    # exporting a non-existent secret key (import just the public key and try to export)
    journalist_public_key = (
        Path(__file__).parent / "files" / "test_journalist_key.pub"
    ).read_text()
    journalist_fingerprint = gpg.import_keys(journalist_public_key).fingerprints[0]
    assert gpg.export_keys(journalist_fingerprint, secret=True, passphrase=passphrase) == ""
