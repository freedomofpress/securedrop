use crate::{Error, Result};
use sequoia_openpgp::cert::prelude::ValidErasedKeyAmalgamation;
use sequoia_openpgp::packet::key::{PublicParts, SecretParts, UnspecifiedRole};
use sequoia_openpgp::packet::Key;
use sequoia_openpgp::policy::{NullPolicy, Policy};
use sequoia_openpgp::Cert;

/// Get public encryption keys from the specified cert, returning an error if
/// no valid keys are found.
pub(crate) fn keys_from_cert<'a>(
    policy: &'a dyn Policy,
    cert: &'a Cert,
) -> Result<Vec<ValidErasedKeyAmalgamation<'a, PublicParts>>> {
    // Pull the encryption keys that are compatible with by the standard policy
    // (e.g. not SHA-1) supported by Sequoia, and not revoked.
    let keys: Vec<_> = cert
        .keys()
        .with_policy(policy, None)
        .supported()
        .alive()
        .revoked(false)
        .for_storage_encryption()
        .collect();

    // Each certificate must have at least one supported encryption key
    if keys.is_empty() {
        Err(Error::NoSupportedKeys(cert.fingerprint().to_string()))
    } else {
        Ok(keys)
    }
}

/// Get the secret encryption key from the cert.
pub(crate) fn secret_key_from_cert(
    cert: &Cert,
) -> Result<Key<SecretParts, UnspecifiedRole>> {
    // Get the secret encryption key for decryption. We don't care about
    // whether it is revoked or expired, or even if its not a weak key
    // since we're just decrypting.
    // We first try to find the key using the StandardPolicy and then
    // fall back to a NullPolicy to prevent downgrade attacks.
    let key = cert
        .keys()
        .secret()
        .with_policy(crate::STANDARD_POLICY, None)
        .for_storage_encryption()
        .next();
    if let Some(key) = key {
        return Ok(key.key().clone());
    }

    // No key found, try again with a null policy
    let null = NullPolicy::new();
    let key = cert
        .keys()
        .secret()
        .with_policy(&null, None)
        .for_storage_encryption()
        .next();

    match key {
        Some(key) => Ok(key.key().clone()),
        None => Err(Error::NoSupportedKeys(cert.fingerprint().to_string())),
    }
}
