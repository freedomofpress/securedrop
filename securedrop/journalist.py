import sys

from encryption import EncryptionManager, GpgKeyNotFoundError
from execution import asynchronous
from journalist_app import create_app
from models import Source
from sdconfig import SecureDropConfig

import redwood

config = SecureDropConfig.get_current()
# app is imported by journalist.wsgi
app = create_app(config)


@asynchronous
def prime_keycache() -> None:
    """Pre-load the source public keys into Redis."""
    with app.app_context():
        encryption_mgr = EncryptionManager.get_default()
        for source in Source.query.filter_by(pending=False, deleted_at=None).all():
            try:
                encryption_mgr.get_source_public_key(source.filesystem_id)
            except GpgKeyNotFoundError:
                pass


def validate_journalist_key() -> None:
    """Verify the journalist PGP key is valid"""
    encryption_mgr = EncryptionManager.get_default()
    # First check that we can read it
    try:
        journalist_key = encryption_mgr.get_journalist_public_key()
    except Exception as e:
        print(f"ERROR: Unable to read journalist public key: {e}", file=sys.stderr)
        app.logger.error(f"ERROR: Unable to read journalist public key: {e}")
        sys.exit(1)
    # And then what we read is valid
    try:
        redwood.is_valid_public_key(journalist_key)
    except redwood.RedwoodError as e:
        print(f"ERROR: Journalist public key is not valid: {e}", file=sys.stderr)
        app.logger.error(f"ERROR: Journalist public key is not valid: {e}")
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    validate_journalist_key()
    prime_keycache()
    debug = getattr(config, "env", "prod") != "prod"
    # nosemgrep: python.flask.security.audit.app-run-param-config.avoid_app_run_with_bad_host
    app.run(debug=debug, host="0.0.0.0", port=8081)
