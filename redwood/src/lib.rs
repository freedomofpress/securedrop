#![deny(clippy::all)]

use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use sequoia_openpgp::cert::{CertBuilder, CipherSuite};
use sequoia_openpgp::crypto::Password;
use sequoia_openpgp::parse::{stream::DecryptorBuilder, Parse};
use sequoia_openpgp::policy::StandardPolicy;
use sequoia_openpgp::serialize::{
    stream::{Armorer, Encryptor2 as Encryptor, LiteralWriter, Message},
    SerializeInto,
};
use sequoia_openpgp::Cert;
use std::borrow::Cow;
use std::fs::File;
use std::io::{self, BufWriter, Read, Write};
use std::path::{Path, PathBuf};
use std::str::FromStr;
use std::string::FromUtf8Error;
use std::time::{Duration, SystemTime};

mod decryption;
mod keys;
mod stream;

const STANDARD_POLICY: &StandardPolicy = &StandardPolicy::new();

#[derive(thiserror::Error, Debug)]
pub enum Error {
    #[error("OpenPGP error: {0}")]
    OpenPgp(#[from] anyhow::Error),
    #[error("IO error: {0}")]
    Io(#[from] io::Error),
    #[error("Unexpected non-UTF-8 text: {0}")]
    NotUnicode(#[from] FromUtf8Error),
    #[error("No supported keys for certificate {0}")]
    NoSupportedKeys(String),
    #[error("Contains secret key material")]
    HasSecretKeyMaterial,
}

create_exception!(redwood, RedwoodError, PyException);

impl From<Error> for PyErr {
    fn from(original: Error) -> Self {
        // Use Debug representation to include context/backtrace
        // if possible: <https://docs.rs/anyhow/latest/anyhow/struct.Error.html#display-representations>
        // For the Io/NotUnicode errors it might look weird but should still be
        // comprehensible.
        RedwoodError::new_err(format!("{:?}", original))
    }
}

type Result<T> = std::result::Result<T, Error>;

// All reply keypairs will be "created" on the same day SecureDrop (then
// Strongbox) was publicly released for the first time, 2013-05-14
// https://www.newyorker.com/news/news-desk/strongbox-and-aaron-swartz
const KEY_CREATION_SECONDS_FROM_EPOCH: u64 = 1368507600;

/// A Python module implemented in Rust.
#[pymodule]
fn redwood(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(generate_source_key_pair, m)?)?;
    m.add_function(wrap_pyfunction!(is_valid_public_key, m)?)?;
    m.add_function(wrap_pyfunction!(is_valid_secret_key, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_message, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_stream, m)?)?;
    m.add_function(wrap_pyfunction!(decrypt, m)?)?;
    m.add("RedwoodError", py.get_type::<RedwoodError>())?;
    Ok(())
}

/// Generate a new PGP key pair using the given email (user ID) and protected
/// with the specified passphrase.
/// Returns the public key, private key, and 40-character fingerprint
#[pyfunction]
pub fn generate_source_key_pair(
    passphrase: &str,
    email: &str,
) -> Result<(String, String, String)> {
    let (cert, _revocation) = CertBuilder::new()
        .set_cipher_suite(CipherSuite::RSA4k)
        .add_userid(format!("Source Key <{}>", email))
        .set_creation_time(
            // All reply keypairs will be "created" on the same day, 2013-05-14
            SystemTime::UNIX_EPOCH
                .checked_add(Duration::from_secs(
                    KEY_CREATION_SECONDS_FROM_EPOCH,
                ))
                // unwrap: Safe because the value is fixed and we know it won't overflow
                .unwrap(),
        )
        .add_storage_encryption_subkey()
        .set_password(Some(passphrase.into()))
        .generate()?;
    let public_key = String::from_utf8(cert.armored().to_vec()?)?;
    let secret_key = String::from_utf8(cert.as_tsk().armored().to_vec()?)?;
    Ok((public_key, secret_key, format!("{}", cert.fingerprint())))
}

#[pyfunction]
pub fn is_valid_public_key(input: &str) -> Result<String> {
    let cert = Cert::from_str(input)?;
    // We don't need the keys, just need to check there's at least one and no error
    keys::keys_from_cert(STANDARD_POLICY, &cert)?;
    // And there is no secret key material
    if cert.is_tsk() {
        return Err(Error::HasSecretKeyMaterial);
    }
    Ok(cert.fingerprint().to_string())
}

#[pyfunction]
pub fn is_valid_secret_key(input: &str, passphrase: String) -> Result<String> {
    let passphrase: Password = passphrase.into();
    let cert = Cert::from_str(input)?;
    let secret_key = keys::secret_key_from_cert(&cert)?;
    secret_key.decrypt_secret(&passphrase)?;
    Ok(cert.fingerprint().to_string())
}

/// Encrypt a message (text) for the specified recipients. The list of
/// recipients is a set of PGP public keys. The encrypted message will
/// be written to `destination`.
#[pyfunction]
pub fn encrypt_message(
    recipients: Vec<String>,
    plaintext: String,
    destination: PathBuf,
    armor: Option<bool>,
) -> Result<()> {
    let plaintext = plaintext.as_bytes();
    encrypt(&recipients, plaintext, &destination, armor)
}

/// Encrypt a Python stream (`typing.BinaryIO`) for the specified recipients.
/// The list of recipients is a set of PGP public keys. The encrypted file
/// will be written to `destination`.
#[pyfunction]
pub fn encrypt_stream(
    recipients: Vec<String>,
    plaintext: &PyAny,
    destination: PathBuf,
) -> Result<()> {
    let stream = stream::Stream { reader: plaintext };
    encrypt(&recipients, stream, &destination, None)
}

/// Helper function to encrypt readable things.
///
/// This is largely based on <https://gitlab.com/sequoia-pgp/sequoia/-/blob/main/guide/src/chapter_02.md>.
fn encrypt(
    recipients: &[String],
    mut plaintext: impl Read,
    destination: &Path,
    armor: Option<bool>,
) -> Result<()> {
    let mut certs = vec![];
    let mut recipient_keys = vec![];
    for recipient in recipients {
        certs.push(Cert::from_str(recipient)?);
    }

    for cert in certs.iter() {
        recipient_keys.extend(keys::keys_from_cert(STANDARD_POLICY, cert)?);
    }

    // In reverse order, we set up a writer that will write an encrypted and
    // armored message to a newly-created file at `destination`.
    // TODO: Use `File::create_new()` once it's stabilized: https://github.com/rust-lang/rust/issues/105135
    let sink = File::options()
        .read(true)
        .write(true)
        .create_new(true)
        .open(destination)?;
    let mut writer = BufWriter::new(sink);
    let message = Message::new(&mut writer);
    let message = if armor.unwrap_or(false) {
        Armorer::new(message).build()?
    } else {
        message
    };
    let message = Encryptor::for_recipients(message, recipient_keys).build()?;
    let mut message = LiteralWriter::new(message).build()?;

    // Feed the plaintext into the writer for encryption and writing to disk
    io::copy(&mut plaintext, &mut message)?;

    // Flush any remaining buffers
    message.finalize()?;
    writer.flush()?;

    Ok(())
}

/// Given a ciphertext, private key, and passphrase, unlock the private key with
/// the passphrase, and use it to decrypt the ciphertext. Arbitrary bytes are
/// returned, which may or may not be valid UTF-8.
#[pyfunction]
pub fn decrypt(
    ciphertext: Vec<u8>,
    secret_key: String,
    passphrase: String,
) -> Result<Cow<'static, [u8]>> {
    let recipient = Cert::from_str(&secret_key)?;
    let passphrase: Password = passphrase.into();
    let helper = decryption::Helper {
        secret: &recipient,
        passphrase: &passphrase,
    };

    // Now, create a decryptor with a helper using the given Certs.
    let mut decryptor = DecryptorBuilder::from_bytes(&ciphertext)?
        .with_policy(STANDARD_POLICY, None, helper)?;

    // Decrypt the data.
    let mut buffer: Vec<u8> = vec![];
    io::copy(&mut decryptor, &mut buffer)?;
    // pyo3 maps Cow<[u8]> to Python's bytes
    Ok(Cow::from(buffer))
}

#[cfg(test)]
mod tests {
    use super::*;
    use sequoia_openpgp::Cert;
    use tempfile::TempDir;

    const PASSPHRASE: &str = "correcthorsebatterystaple";
    const SECRET_MESSAGE: &str = "Rust is great 🦀";
    // Purposefully weak key that should be rejected; this is 1024-bit RSA
    // and uses a SHA-1 self signature scheme
    const BAD_KEY: &str = include_str!("../res/weak_sample_key.asc");
    const BAD_KEY_FINGERPRINT: &str =
        include_str!("../res/weak_sample_key_fingerprint.txt");

    #[test]
    fn test_generate_source_key_pair() {
        let (public_key, secret_key, fingerprint) =
            generate_source_key_pair(PASSPHRASE, "foo@example.org").unwrap();
        assert_eq!(fingerprint.len(), 40);
        println!("{}", public_key);
        assert!(public_key.starts_with("-----BEGIN PGP PUBLIC KEY BLOCK-----"));
        assert!(public_key.contains("Comment: Source Key <foo@example.org>"));
        let cert = Cert::from_str(&public_key).unwrap();
        assert_eq!(format!("{}", cert.fingerprint()), fingerprint);
        println!("{}", secret_key);
        assert!(secret_key.starts_with("-----BEGIN PGP PRIVATE KEY BLOCK-----"));
        assert!(secret_key.contains("Comment: Source Key <foo@example.org>"));
        let cert = Cert::from_str(&secret_key).unwrap();
        assert_eq!(format!("{}", cert.fingerprint()), fingerprint);
    }

    #[test]
    fn test_is_valid_public_key() {
        let (good_key, secret_key, fingerprint) =
            generate_source_key_pair(PASSPHRASE, "foo@example.org").unwrap();
        assert_eq!(is_valid_public_key(&good_key).unwrap(), fingerprint);
        assert_eq!(
            is_valid_public_key(BAD_KEY).unwrap_err().to_string(),
            format!(
                "No supported keys for certificate {}",
                BAD_KEY_FINGERPRINT
            )
        );
        assert_eq!(
            is_valid_public_key(&secret_key).unwrap_err().to_string(),
            "Contains secret key material"
        );
    }

    #[test]
    fn test_is_valid_secret_key() {
        let (public_key, secret_key, fingerprint) =
            generate_source_key_pair(PASSPHRASE, "foo@example.org").unwrap();
        assert_eq!(
            is_valid_secret_key(&secret_key, PASSPHRASE.to_string()).unwrap(),
            fingerprint
        );
        assert_eq!(
            is_valid_secret_key(
                &secret_key,
                "not the correct passphrase".to_string()
            )
            .unwrap_err()
            .to_string(),
            "OpenPGP error: unexpected EOF"
        );
        assert_eq!(
            is_valid_secret_key(&public_key, PASSPHRASE.to_string())
                .unwrap_err()
                .to_string(),
            format!("No supported keys for certificate {fingerprint}")
        );
    }

    #[test]
    fn test_source_cert_has_accepted_key() {
        // Certificate with valid key
        let (good_key, _secret_key, _fingerprint) =
            generate_source_key_pair(PASSPHRASE, "foo@example.org").unwrap();

        // Certificate with the weak key
        let bad_cert = Cert::from_bytes(BAD_KEY.as_bytes()).unwrap();
        assert_eq!(BAD_KEY_FINGERPRINT, bad_cert.fingerprint().to_string());

        // Attempting to encrypt to multiple recipients should fail if any one of them
        // has no supported keys
        let tmp_dir = TempDir::new().unwrap();
        let expected_err_msg = format!(
            "No supported keys for certificate {}",
            BAD_KEY_FINGERPRINT
        );

        let err = encrypt_message(
            vec![good_key, BAD_KEY.to_string()],
            SECRET_MESSAGE.to_string(),
            tmp_dir.path().join("message.asc"),
            None,
        )
        .unwrap_err();
        assert_eq!(err.to_string(), expected_err_msg);
    }

    #[test]
    fn test_source_key_creation_expiry() {
        let (public_key, _secret_key, _fingerprint) =
            generate_source_key_pair(PASSPHRASE, "foo@example.org").unwrap();
        let cert = Cert::from_str(&public_key).unwrap();
        let standard_creation_time = SystemTime::UNIX_EPOCH
            // Equivalent to 2013-05-14
            .checked_add(Duration::from_secs(KEY_CREATION_SECONDS_FROM_EPOCH))
            // unwrap: Safe because the value is fixed and we know it won't overflow
            .unwrap();
        let signature = cert.primary_key().self_signatures().next().unwrap();

        assert_eq!(
            signature.signature_creation_time(),
            Some(standard_creation_time)
        );

        // From the documentation:
        // This function is called signature_validity_period and not signature_expiration_time
        // [because] the time is actually relative to the signature's creation time, which
        // is stored in the signature's Signature Creation Time subpacket.
        assert_eq!(signature.signature_validity_period(), None);
    }

    #[test]
    fn test_multiple_recipients() {
        // Generate 3 keys
        let (public_key1, secret_key1, _) =
            generate_source_key_pair(PASSPHRASE, "foo1@example.org").unwrap();
        let (public_key2, secret_key2, _) =
            generate_source_key_pair(PASSPHRASE, "foo2@example.org").unwrap();
        let (_public_key3, secret_key3, _) =
            generate_source_key_pair(PASSPHRASE, "foo3@example.org").unwrap();

        let tmp_dir = TempDir::new().unwrap();
        let tmp = tmp_dir.path().join("message.asc");
        println!("{}", tmp.to_string_lossy());
        // Encrypt a message to keys 1 and 2 but not 3
        encrypt_message(
            vec![public_key1, public_key2],
            SECRET_MESSAGE.to_string(),
            tmp.clone(),
            None,
        )
        .unwrap();
        let ciphertext = std::fs::read(tmp).unwrap();
        // Decrypt as key 1
        let plaintext =
            decrypt(ciphertext.clone(), secret_key1, PASSPHRASE.to_string())
                .unwrap();
        // Verify message is what we put in originally
        assert_eq!(
            SECRET_MESSAGE,
            String::from_utf8(plaintext.to_vec()).unwrap()
        );
        // Decrypt as key 2
        let plaintext =
            decrypt(ciphertext.clone(), secret_key2, PASSPHRASE.to_string())
                .unwrap();
        // Verify message is what we put in originally
        assert_eq!(
            SECRET_MESSAGE,
            String::from_utf8(plaintext.to_vec()).unwrap()
        );
        // Try to decrypt as key 3, expect an error
        let err = decrypt(ciphertext, secret_key3, PASSPHRASE.to_string())
            .unwrap_err();
        assert_eq!(
            err.to_string(),
            "OpenPGP error: no matching pkesk, wrong secret key provided?"
        );
    }

    #[test]
    fn test_encryption_missing_malformed_recipient_key() {
        // Bad fingerprints can be: empty, empty string, or malformed
        let bad_keys: Vec<(Vec<String>, &str)> = vec![
            (
                vec![],
                "OpenPGP error: Invalid operation: \
                Neither recipients, passwords, nor session key given",
            ),
            (
                vec!["".to_string()],
                "OpenPGP error: Malformed Cert: No data",
            ),
            (
                vec!["DEADBEEF0123456".to_string()],
                "OpenPGP error: unexpected EOF",
            ),
        ];
        let tmp_dir = TempDir::new().unwrap();
        for (key, error) in bad_keys {
            let err = encrypt_message(
                key, // missing or malformed recipient key
                "Look ma, no key".to_string(),
                tmp_dir.path().join("message.asc"),
                None,
            )
            .unwrap_err();
            assert_eq!(err.to_string(), error);
        }
    }
}
