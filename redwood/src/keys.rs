use crate::{Error, Result};
use sequoia_openpgp::cert::prelude::ValidErasedKeyAmalgamation;
use sequoia_openpgp::packet::key::{PublicParts, SecretParts, UnspecifiedRole};
use sequoia_openpgp::packet::Key;
use sequoia_openpgp::policy::Policy;
use sequoia_openpgp::Cert;

/// We want to use the same iterators on public and secret keys but it's not
/// really possible to do it in a function because of type differences so we
/// use a macro instead.
macro_rules! filter_keys {
    ( $keys:expr, $policy: ident ) => {
        $keys
            .with_policy($policy, None)
            .supported()
            .alive()
            .revoked(false)
            .for_storage_encryption()
    };
}

/// Get public encryption keys from the specified cert, returning an error if
/// no valid keys are found.
pub(crate) fn keys_from_cert<'a>(
    policy: &'a dyn Policy,
    cert: &'a Cert,
) -> Result<Vec<ValidErasedKeyAmalgamation<'a, PublicParts>>> {
    // Pull the encryption keys that are compatible with by the standard policy
    // (e.g. not SHA-1) supported by Sequoia, and not revoked.
    let keys: Vec<_> = filter_keys!(cert.keys(), policy).collect();

    // Each certificate must have at least one supported encryption key
    if keys.is_empty() {
        Err(Error::NoSupportedKeys(cert.fingerprint().to_string()))
    } else {
        Ok(keys)
    }
}

/// Get the secret encryption key, which is the first and only subkey, from the cert.
pub(crate) fn secret_key_from_cert<'a>(
    policy: &'a dyn Policy,
    cert: &'a Cert,
) -> Result<Key<SecretParts, UnspecifiedRole>> {
    // Pull the encryption keys that are compatible with by the standard policy
    // (e.g. not SHA-1) supported by Sequoia, and not revoked.
    // These filter options should be kept in sync with `Helper::decrypt()`.
    let keys: Vec<_> = filter_keys!(cert.keys().secret(), policy).collect();

    // Just return the first encryption key
    match keys.get(0) {
        Some(key) => Ok(key.key().clone()),
        None => Err(Error::NoSupportedKeys(cert.fingerprint().to_string())),
    }
}
