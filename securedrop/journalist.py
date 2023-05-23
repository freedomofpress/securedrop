from actions.sources_actions import SearchSourcesAction
from db import db
from encryption import EncryptionManager, GpgKeyNotFoundError
from execution import asynchronous
from journalist_app import create_app
from sdconfig import SecureDropConfig

config = SecureDropConfig.get_current()
# app is imported by journalist.wsgi
app = create_app(config)


@asynchronous
def prime_keycache() -> None:
    """Pre-load the source public keys into Redis."""
    with app.app_context():
        encryption_mgr = EncryptionManager.get_default()
        all_sources = SearchSourcesAction(db_session=db.session).perform()
        for source in all_sources:
            try:
                encryption_mgr.get_source_public_key(source.filesystem_id)
            except GpgKeyNotFoundError:
                pass


prime_keycache()


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, "env", "prod") != "prod"
    # nosemgrep: python.flask.security.audit.app-run-param-config.avoid_app_run_with_bad_host
    app.run(debug=debug, host="0.0.0.0", port=8081)  # nosec
