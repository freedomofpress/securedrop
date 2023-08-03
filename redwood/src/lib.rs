#![deny(clippy::all)]

use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use sequoia_openpgp::cert::{CertBuilder, CipherSuite};
use sequoia_openpgp::crypto::Password;
use sequoia_openpgp::parse::{stream::DecryptorBuilder, Parse};
use sequoia_openpgp::policy::StandardPolicy;
use sequoia_openpgp::serialize::{
    stream::{Armorer, Encryptor, LiteralWriter, Message},
    SerializeInto,
};
use sequoia_openpgp::Cert;
use std::fs::File;
use std::io::{self, Read};
use std::path::{Path, PathBuf};
use std::str::FromStr;
use std::string::FromUtf8Error;
use std::time::{Duration, SystemTime};

/// Alias to make it easier for Python readers
type Bytes = Vec<u8>;

mod decryption;

#[derive(thiserror::Error, Debug)]
pub enum Error {
    #[error("OpenPGP error: {0}")]
    OpenPgp(#[from] anyhow::Error),
    #[error("IO error: {0}")]
    Io(#[from] io::Error),
    #[error("Unexpected non-UTF-8 text: {0}")]
    NotUnicode(#[from] FromUtf8Error),
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

/// A Python module implemented in Rust.
#[pymodule]
fn redwood(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(generate_source_key_pair, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_message, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_file, m)?)?;
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
            // All reply keypairs will be "created" on the same day SecureDrop (then
            // Strongbox) was publicly released for the first time.
            // https://www.newyorker.com/news/news-desk/strongbox-and-aaron-swartz
            SystemTime::UNIX_EPOCH
                // Equivalent to 2013-05-14
                .checked_add(Duration::from_secs(1368507600))
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

/// Encrypt a message (text) for the specified recipients. The list of
/// recipients is a set of PGP public keys. The encrypted message will
/// be written to `destination`.
#[pyfunction]
pub fn encrypt_message(
    recipients: Vec<String>,
    plaintext: String,
    destination: PathBuf,
) -> Result<()> {
    let plaintext = plaintext.as_bytes();
    encrypt(&recipients, plaintext, &destination)
}

/// Encrypt a file that's already on disk for the specified recipients.
/// The list of recipients is a set of PGP public keys. The encrypted file
/// will be written to `destination`.
#[pyfunction]
pub fn encrypt_file(
    recipients: Vec<String>,
    plaintext: PathBuf,
    destination: PathBuf,
) -> Result<()> {
    let plaintext = File::open(plaintext)?;
    encrypt(&recipients, plaintext, &destination)
}

/// Helper function to encrypt readable things.
///
/// This is largely based on <https://gitlab.com/sequoia-pgp/sequoia/-/blob/main/guide/src/chapter_02.md>.
fn encrypt(
    recipients: &[String],
    mut plaintext: impl Read,
    destination: &Path,
) -> Result<()> {
    let p = &StandardPolicy::new();
    let mut certs = vec![];
    let mut recipient_keys = vec![];
    for recipient in recipients {
        certs.push(Cert::from_str(recipient)?);
    }

    // For each of the recipient certificates, pull the encryption keys that
    // are compatible with by the standard policy (e.g. not SHA-1) supported by
    // Sequoia (duh), and not revoked.
    for cert in certs.iter() {
        for key in cert
            .keys()
            .with_policy(p, None)
            .supported()
            .alive()
            .revoked(false)
        {
            recipient_keys.push(key);
        }
    }

    // In reverse order, we set up a writer that will write an encrypted and
    // armored message to a newly-created file at `destination`.
    let mut sink = File::create(destination)?;
    let message = Message::new(&mut sink);
    let message = Armorer::new(message).build()?;
    let message = Encryptor::for_recipients(message, recipient_keys).build()?;
    let mut message = LiteralWriter::new(message).build()?;

    // Feed the plaintext into the writer for encryption and writing to disk
    io::copy(&mut plaintext, &mut message)?;

    // Flush any remaining buffers
    message.finalize()?;

    Ok(())
}

/// Given a ciphertext, private key, and passphrase, unlock the private key with
/// the passphrase, and use it to decrypt the ciphertext.  It is assumed that the
/// plaintext is UTF-8.
#[pyfunction]
pub fn decrypt(
    ciphertext: Bytes,
    secret_key: String,
    passphrase: String,
) -> Result<String> {
    let recipient = Cert::from_str(&secret_key)?;
    let policy = &StandardPolicy::new();
    let passphrase: Password = passphrase.into();
    let helper = decryption::Helper {
        policy,
        secret: &recipient,
        passphrase: &passphrase,
    };

    // Now, create a decryptor with a helper using the given Certs.
    let mut decryptor = DecryptorBuilder::from_bytes(&ciphertext)?
        .with_policy(policy, None, helper)?;

    // Decrypt the data.
    let mut buffer: Bytes = vec![];
    io::copy(&mut decryptor, &mut buffer)?;
    let plaintext = String::from_utf8(buffer)?;
    Ok(plaintext)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::NamedTempFile;

    #[test]
    fn test_generate_source_key_pair() {
        let (public_key, secret_key, fingerprint) = generate_source_key_pair(
            "correcthorsebatterystaple",
            "foo@example.org",
        )
        .unwrap();
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
    fn test_encryption_decryption() {
        // Generate a new key
        let (public_key, secret_key, _fingerprint) = generate_source_key_pair(
            "correcthorsebatterystaple",
            "foo@example.org",
        )
        .unwrap();
        let tmp = NamedTempFile::new().unwrap();
        // Encrypt a message
        encrypt_message(
            vec![public_key],
            "Rust is great 🦀".to_string(),
            tmp.path().to_path_buf(),
        )
        .unwrap();
        let ciphertext = std::fs::read_to_string(tmp.path()).unwrap();
        // Verify ciphertext looks like an encrypted message
        assert!(ciphertext.starts_with("-----BEGIN PGP MESSAGE-----\n"));
        // Try to decrypt the message
        let plaintext = decrypt(
            ciphertext.into_bytes(),
            secret_key,
            "correcthorsebatterystaple".to_string(),
        )
        .unwrap();
        // Verify message is what we put in originally
        assert_eq!("Rust is great 🦀", &plaintext);
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
        let tmp: NamedTempFile = NamedTempFile::new().unwrap();
        for (key, error) in bad_keys {
            let err = encrypt_message(
                key, // missing or malformed recipient key
                "Look ma, no key".to_string(),
                tmp.path().to_path_buf(),
            )
            .unwrap_err();
            assert_eq!(err.to_string(), error);
        }
    }
}
