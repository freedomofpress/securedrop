//! Decryption is much more complicated than encryption,
//! This code is mostly lifted from https://docs.sequoia-pgp.org/sequoia_guide/chapter_02/index.html

use anyhow::anyhow;
use sequoia_openpgp::crypto::{Password, SessionKey};
use sequoia_openpgp::parse::stream::*;
use sequoia_openpgp::policy::Policy;
use sequoia_openpgp::types::SymmetricAlgorithm;

pub(crate) struct Helper<'a> {
    pub(crate) policy: &'a dyn Policy,
    pub(crate) secret: &'a sequoia_openpgp::Cert,
    pub(crate) passphrase: &'a Password,
}

impl<'a> VerificationHelper for Helper<'a> {
    fn get_certs(
        &mut self,
        _ids: &[sequoia_openpgp::KeyHandle],
    ) -> sequoia_openpgp::Result<Vec<sequoia_openpgp::Cert>> {
        // You're supposed to public keys for signature verification here, but
        // we don't care whether messages are signed or not.
        Ok(Vec::new())
    }

    fn check(
        &mut self,
        _structure: MessageStructure,
    ) -> sequoia_openpgp::Result<()> {
        // You're supposed to implement a signature verification policy here,
        // but we don't care whether messages are signed or not.
        Ok(())
    }
}

impl<'a> DecryptionHelper for Helper<'a> {
    fn decrypt<D>(
        &mut self,
        pkesks: &[sequoia_openpgp::packet::PKESK],
        _skesks: &[sequoia_openpgp::packet::SKESK],
        sym_algo: Option<SymmetricAlgorithm>,
        mut decrypt: D,
    ) -> sequoia_openpgp::Result<Option<sequoia_openpgp::Fingerprint>>
    where
        D: FnMut(SymmetricAlgorithm, &SessionKey) -> bool,
    {
        // The encryption key is the first and only subkey.
        let key = self
            .secret
            .keys()
            .secret()
            .with_policy(self.policy, None)
            .next()
            // In practice this error shouldn't be reachable from SecureDrop-generated keys
            .ok_or_else(|| {
                anyhow!("certificate did not have a usable secret key")
            })?
            .key()
            .clone();

        // Decrypt the secret key with the specified passphrase.
        let mut pair = key.decrypt_secret(self.passphrase)?.into_keypair()?;

        pkesks[0]
            .decrypt(&mut pair, sym_algo)
            .map(|(algo, session_key)| decrypt(algo, &session_key));

        // XXX: The documentation says:
        // > If the message is decrypted using a PKESK packet, then the
        // > fingerprint of the certificate containing the encryption subkey
        // > should be returned. This is used in conjunction with the intended
        // > recipient subpacket (see Section 5.2.3.29 of RFC 4880bis) to
        // > prevent Surreptitious Forwarding.
        // Unclear if that's something we need to do.
        Ok(None)
    }
}
