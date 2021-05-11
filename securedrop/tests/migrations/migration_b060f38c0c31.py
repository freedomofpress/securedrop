# -*- coding: utf-8 -*-

import random
import uuid
from typing import Any, Dict

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from db import db
from journalist_app import create_app
from .helpers import random_chars, random_datetime, bool_or_none

random.seed("ᕕ( ᐛ )ᕗ")


def add_submission(source_id):
    params = {
        "uuid": str(uuid.uuid4()),
        "source_id": source_id,
        "filename": random_chars(50),
        "size": random.randint(0, 1024 * 1024 * 500),
        "downloaded": bool_or_none(),
        "checksum": random_chars(255, chars="0123456789abcdef")
    }
    sql = """
    INSERT INTO submissions (uuid, source_id, filename, size, downloaded, checksum)
    VALUES (:uuid, :source_id, :filename, :size, :downloaded, :checksum)
    """
    db.engine.execute(text(sql), **params)


class UpgradeTester:
    """
    Verify that the Source.flagged column no longer exists.
    """

    source_count = 10
    original_sources = {}  # type: Dict[str, Any]
    source_submissions = {}  # type: Dict[str, Any]

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def load_data(self):
        with self.app.app_context():
            for i in range(self.source_count):
                self.add_source()

            self.original_sources = {
                s.uuid: s for s in db.engine.execute(text("SELECT * FROM sources")).fetchall()
            }

            for s in self.original_sources.values():
                for i in range(random.randint(0, 3)):
                    add_submission(s.id)

                self.source_submissions[s.id] = db.engine.execute(
                    text("SELECT * FROM submissions WHERE source_id = :source_id"),
                    **{"source_id": s.id}
                ).fetchall()

    def add_source(self):
        params = {
            "uuid": str(uuid.uuid4()),
            "filesystem_id": random_chars(96),
            "journalist_designation": random_chars(50),
            "flagged": bool_or_none(),
            "last_updated": random_datetime(nullable=True),
            "pending": bool_or_none(),
            "interaction_count": random.randint(0, 1000),
        }
        sql = """
        INSERT INTO sources (uuid, filesystem_id,
        journalist_designation, flagged, last_updated, pending,
        interaction_count)
        VALUES (:uuid, :filesystem_id, :journalist_designation,
        :flagged, :last_updated, :pending, :interaction_count)
        """

        db.engine.execute(text(sql), **params)

    def check_upgrade(self):
        with self.app.app_context():

            # check that the flagged column is gone
            with pytest.raises(OperationalError, match=".*sources has no column named flagged.*"):
                self.add_source()

            # check that the sources are otherwise unchanged
            sources = db.engine.execute(text("SELECT * FROM sources")).fetchall()
            assert len(sources) == len(self.original_sources)
            for source in sources:
                assert not hasattr(source, "flagged")
                original_source = self.original_sources[source.uuid]
                assert source.id == original_source.id
                assert source.journalist_designation == original_source.journalist_designation
                assert source.last_updated == original_source.last_updated
                assert source.pending == original_source.pending
                assert source.interaction_count == original_source.interaction_count

                source_submissions = db.engine.execute(
                    text("SELECT * FROM submissions WHERE source_id = :source_id"),
                    **{"source_id": source.id}
                ).fetchall()
                assert source_submissions == self.source_submissions[source.id]


class DowngradeTester:
    """
    Verify that the Source.flagged column has been recreated properly.
    """

    source_count = 10
    original_sources = {}  # type: Dict[str, Any]
    source_submissions = {}  # type: Dict[str, Any]

    def __init__(self, config):
        self.config = config
        self.app = create_app(config)

    def add_source(self):
        params = {
            "uuid": str(uuid.uuid4()),
            "filesystem_id": random_chars(96),
            "journalist_designation": random_chars(50),
            "last_updated": random_datetime(nullable=True),
            "pending": bool_or_none(),
            "interaction_count": random.randint(0, 1000),
            "deleted_at": None,
        }
        sql = """
        INSERT INTO sources (
        uuid, filesystem_id, journalist_designation, last_updated, pending,
        interaction_count
        ) VALUES (
        :uuid, :filesystem_id, :journalist_designation, :last_updated, :pending,
        :interaction_count
        )
        """

        db.engine.execute(text(sql), **params)

    def load_data(self):
        with self.app.app_context():
            for i in range(self.source_count):
                self.add_source()

            self.original_sources = {
                s.uuid: s for s in db.engine.execute(text("SELECT * FROM sources")).fetchall()
            }

            for s in self.original_sources.values():
                for i in range(random.randint(0, 3)):
                    add_submission(s.id)

                self.source_submissions[s.id] = db.engine.execute(
                    text("SELECT * FROM submissions WHERE source_id = :source_id"),
                    **{"source_id": s.id}
                ).fetchall()

    def check_downgrade(self):
        with self.app.app_context():
            # check that the sources are otherwise unchanged
            sources = db.engine.execute(text("SELECT * FROM sources")).fetchall()
            assert len(sources) == len(self.original_sources)
            for source in sources:
                assert hasattr(source, "flagged")
                original_source = self.original_sources[source.uuid]
                assert source.id == original_source.id
                assert source.journalist_designation == original_source.journalist_designation
                assert source.last_updated == original_source.last_updated
                assert source.pending == original_source.pending
                assert source.interaction_count == original_source.interaction_count
                assert not hasattr(original_source, "flagged")
                assert source.flagged is None

                source_submissions = db.engine.execute(
                    text("SELECT * FROM submissions WHERE source_id = :source_id"),
                    **{"source_id": source.id}
                ).fetchall()
                assert source_submissions == self.source_submissions[source.id]
