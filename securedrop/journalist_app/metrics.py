# -*- coding: utf-8 -*-

from flask import Blueprint, Response
from models import Journalist, JournalistLoginAttempt, Reply, Source, Submission
from journalist_app.decorators import admin_required
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

SECUREDROP_USERS = Gauge(
    "securedrop_users",
    "Number of journalists who can access SecureDrop and their details",
    labelnames=["username", "user_id", "created", "last"],
)

SECUREDROP_SUBMISSIONS = Gauge(
    "securedrop_submissions",
    "Number of submissions, from which source, their size in bytes, whether they've been read",
    labelnames=["size_bytes", "downloaded", "author"],
)

SECUREDROP_REPLIES = Gauge(
    "securedrop_replies", "Number of replies from journalists to sources"
)

SECUREDROP_SOURCES = Gauge(
    "securedrop_sources",
    "Number of sources who have made submissions, whether they're flagged, number of interactions and when they last logged in",
    labelnames=["designation", "flagged", "last", "interactions"],
)

SECUREDROP_LOGINS = Gauge(
    "securedrop_logins",
    "Number of login attempts (both failed and successful) to the journalist interface, with timestamp and username+id",
    labelnames=["when", "user_id", "username"],
)


def make_blueprint(config):
    view = Blueprint("metrics", __name__)

    @view.route("/", methods=["GET"])
    @admin_required
    def index():
        users = Journalist.query.all()
        submissions = Submission.query.all()
        replies = Reply.query.all()
        sources = Source.query.all()
        logins = JournalistLoginAttempt.query.all()
        for user in users:
            SECUREDROP_USERS.labels(
                username=user.username,
                user_id=user.id,
                created=user.created_on,
                last=user.last_access,
            ).set(len(users))
        for submission in submissions:
            source = Source.query.filter_by(id=submission.source_id).one()
            SECUREDROP_SUBMISSIONS.labels(
                size_bytes=submission.size,
                downloaded=bool(submission.downloaded),
                author=source.journalist_designation,
            ).set(len(submissions))
        SECUREDROP_REPLIES.set(len(replies))
        for source in sources:
            SECUREDROP_SOURCES.labels(
                designation=source.journalist_designation,
                flagged=bool(source.flagged),
                last=source.last_updated,
                interactions=source.interaction_count,
            ).set(len(sources))
        for login in logins:
            journalist = Journalist.query.filter_by(id=login.id).one_or_none()
            SECUREDROP_LOGINS.labels(
                when=login.timestamp, user_id=login.id, username=journalist.username
            ).set(len(logins))

        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    return view
