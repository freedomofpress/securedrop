from contextlib import contextmanager
from typing import Generator

from db import db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.session import Session


@contextmanager
def _get_fake_db_module(
    database_uri: str,
) -> Generator[SQLAlchemy, None, None]:
    # flask-sqlalchemy's API only allows DB access via a Flask app
    # So we create a fake Flask app just so we can get a connection to the DB
    app_for_db_connection = Flask("FakeAppForDbConnection")
    app_for_db_connection.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app_for_db_connection.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    db.init_app(app_for_db_connection)

    with app_for_db_connection.app_context():
        yield db


@contextmanager
def get_database_session(database_uri: str) -> Generator[Session, None, None]:
    """Easily get a session to the DB without having to deal with Flask apps.

    Can be used for tests and utility scripts that need to add data to the DB outside of the
    context of the source & journalist Flask applications.
    """
    with _get_fake_db_module(database_uri) as initialized_db_module:
        db_session = initialized_db_module.session
        try:
            yield db_session
        finally:
            db_session.close()
