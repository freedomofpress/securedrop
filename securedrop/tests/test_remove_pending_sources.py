import argparse

import manage
import pytest
from models import Source, db
from passphrases import PassphraseGenerator
from source_user import create_source_user


@pytest.mark.parametrize("n,m", [(10, 5), (7, 0)])
def test_remove_pending_sources_none_pending(n, m, source_app, config, app_storage):
    """remove_pending_sources() is a no-op on active sources."""

    # Override the configuration to point at the per-test database.
    data_root = config.SECUREDROP_DATA_ROOT

    with source_app.app_context():
        sources = []
        for i in range(0, n):
            source_user = create_source_user(
                db_session=db.session,
                source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
                source_app_storage=app_storage,
            )
            source = source_user.get_db_record()
            source.pending = False
            sources.append(source.id)
        db.session.commit()

        # Make sure we have n sources.
        assert db.session.query(Source).count() == n

        # If we're keeping the n most-recent sources, then remove_pending_sources()
        # shouldn't remove any.
        args = argparse.Namespace(data_root=data_root, verbose=True, keep_most_recent=n)
        manage.setup_verbosity(args)
        manage.remove_pending_sources(args)
        assert db.session.query(Source).count() == n

        # If we're keeping the m most-recent sources, then remove_pending_sources()
        # still shouldn't do anything, because none are pending.
        args = argparse.Namespace(data_root=data_root, verbose=True, keep_most_recent=m)
        manage.setup_verbosity(args)
        manage.remove_pending_sources(args)
        assert db.session.query(Source).count() == n


@pytest.mark.parametrize("n,m", [(10, 5), (7, 0)])
def test_remove_pending_sources_all_pending(n, m, source_app, config, app_storage):
    """remove_pending_sources() removes all but the most-recent m of n pending sources."""
    # Override the configuration to point at the per-test database.
    data_root = config.SECUREDROP_DATA_ROOT

    with source_app.app_context():
        sources = []
        for i in range(0, n):
            source_user = create_source_user(
                db_session=db.session,
                source_passphrase=PassphraseGenerator.get_default().generate_passphrase(),
                source_app_storage=app_storage,
            )
            source = source_user.get_db_record()
            sources.append(source.id)
        db.session.commit()

        # Make sure we have n sources.
        assert db.session.query(Source).count() == n

        # If we're keeping the n most-recent sources, then remove_pending_sources()
        # shouldn't remove any.
        args = argparse.Namespace(data_root=data_root, verbose=True, keep_most_recent=n)
        manage.setup_verbosity(args)
        manage.remove_pending_sources(args)
        assert db.session.query(Source).count() == n

        # If we're keeping the m most-recent sources, then remove_pending_sources()
        # should remove n - m.
        args = argparse.Namespace(data_root=data_root, verbose=True, keep_most_recent=m)
        manage.setup_verbosity(args)
        manage.remove_pending_sources(args)
        assert db.session.query(Source).count() == m

        # Specifically, the first n - m sources should be gone...
        for source in sources[0 : n - m]:
            assert db.session.query(Source).get(source) is None

        # ...and only the last m should remain.
        for source in sources[n - m : n]:
            assert db.session.query(Source).get(source) is not None
