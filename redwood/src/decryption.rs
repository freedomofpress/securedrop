//! Decryption is much more complicated than encryption,
//! This code is mostly lifted from https://docs.sequoia-pgp.org/sequoia_guide/chapter_02/index.html

use crate::keys::secret_key_from_cert;
use anyhow::anyhow;
use sequoia_openpgp::crypto::{Password, SessionKey};
use sequoia_openpgp::parse::stream::*;
use sequoia_openpgp::policy::Policy;
use sequoia_openpgp::types::SymmetricAlgorithm;
use sequoia_openpgp::KeyID;

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
        let key = secret_key_from_cert(self.policy, self.secret)?;

        for pkesk in pkesks {
            // Note: this check won't work for messages encrypted with --throw-keyids,
            // but we don't generate any messages that use it.
            if pkesk.recipient() == &KeyID::from(key.fingerprint()) {
                // Decrypt the secret key with the specified passphrase.
                let mut pair = key
                    .clone()
                    .decrypt_secret(self.passphrase)?
                    .into_keypair()?;
                pkesk
                    .decrypt(&mut pair, sym_algo)
                    .map(|(algo, session_key)| decrypt(algo, &session_key));
                // Return the fingerprint of the key we decrypted with, this is used in
                // conjunction with the intended recipient subpacket (see "Intended Recipient Fingerprint"
                // in RFC 4880bis) to prevent Surreptitious Forwarding.
                return Ok(Some(key.fingerprint()));
            }
        }

        Err(anyhow!("no matching pkesk, wrong secret key provided?"))
    }
}
