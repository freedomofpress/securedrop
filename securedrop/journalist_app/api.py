import collections.abc
import json
from datetime import datetime, timezone
from os import path
from typing import Set, Tuple, Union
from uuid import UUID

import flask
import werkzeug
from db import db
from flask import Blueprint, abort, current_app, jsonify, request
from journalist_app import utils
from journalist_app.sessions import session
from models import (
    InvalidUsernameException,
    Journalist,
    LoginThrottledException,
    Reply,
    SeenReply,
    Source,
    Submission,
    WrongPasswordException,
)
from sqlalchemy import Column
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from store import NotEncrypted, Storage
from two_factor import OtpSecretInvalid, OtpTokenInvalid
from werkzeug.exceptions import default_exceptions


def get_or_404(model: db.Model, object_id: str, column: Column) -> db.Model:
    result = model.query.filter(column == object_id).one_or_none()
    if result is None:
        abort(404)
    return result


def make_blueprint() -> Blueprint:
    api = Blueprint("api", __name__)

    @api.route("/")
    def get_endpoints() -> Tuple[flask.Response, int]:
        endpoints = {
            "sources_url": "/api/v1/sources",
            "current_user_url": "/api/v1/user",
            "all_users_url": "/api/v1/users",
            "submissions_url": "/api/v1/submissions",
            "replies_url": "/api/v1/replies",
            "seen_url": "/api/v1/seen",
            "auth_token_url": "/api/v1/token",
        }
        return jsonify(endpoints), 200

    # Before every post, we validate the payload before processing the request
    @api.before_request
    def validate_data() -> None:
        if request.method == "POST":
            # flag, star, and logout can have empty payloads
            if not request.data:
                dataless_endpoints = [
                    "add_star",
                    "remove_star",
                    "flag",
                    "logout",
                ]
                for endpoint in dataless_endpoints:
                    if request.endpoint == "api." + endpoint:
                        return
                abort(400, "malformed request")
            # other requests must have valid JSON payload
            else:
                try:
                    json.loads(request.data.decode("utf-8"))
                except ValueError:
                    abort(400, "malformed request")

    @api.route("/token", methods=["POST"])
    def get_token() -> Tuple[flask.Response, int]:
        creds = json.loads(request.data.decode("utf-8"))

        username = creds.get("username", None)
        passphrase = creds.get("passphrase", None)
        one_time_code = creds.get("one_time_code", None)

        if username is None:
            abort(400, "username field is missing")
        if passphrase is None:
            abort(400, "passphrase field is missing")
        if one_time_code is None:
            abort(400, "one_time_code field is missing")

        try:
            journalist = Journalist.login(username, passphrase, one_time_code)

            response = jsonify(
                {
                    "token": session.get_token(),
                    "expiration": session.get_lifetime(),
                    "journalist_uuid": journalist.uuid,
                    "journalist_first_name": journalist.first_name,
                    "journalist_last_name": journalist.last_name,
                }
            )

            # Update access metadata
            journalist.last_access = datetime.now(timezone.utc)
            db.session.add(journalist)
            db.session.commit()

            session["uid"] = journalist.id

            return response, 200
        except (
            LoginThrottledException,
            InvalidUsernameException,
            OtpSecretInvalid,
            OtpTokenInvalid,
            WrongPasswordException,
        ):
            return abort(403, "Token authentication failed.")

    @api.route("/sources", methods=["GET"])
    def get_all_sources() -> Tuple[flask.Response, int]:
        sources = Source.query.filter_by(pending=False, deleted_at=None).all()
        return jsonify({"sources": [source.to_json() for source in sources]}), 200

    @api.route("/sources", methods=["DELETE"])
    def delete_sources() -> Tuple[flask.Response, int]:
        """
        Given a list of `Source` UUIDs, iterate over the list and try to delete
        each `Source`.  Return HTTP 200 "Success" if all `Source`s were deleted
        or HTTP 207 "Multi-Status" if some failed.  (There's an argument for
        HTTP 202 "Accepted", since filesystem-level deletion is still deferred
        to the shredder; but that's an implementation detail that we can hide
        from the client.)

        NB. According to RFC 9110 §9.3.5, a client may not assume that a DELETE
        endpoint will accept a request body, but a DELETE endpoint may do so,
        and in our case we can rule out middleboxes that might mangle it in
        transit.
        """
        if not isinstance(request.json, list):
            abort(400, "no sources specified")

        succeeded = []
        failed = []
        for source_uuid in request.json:
            try:
                # Don't use `get_or_404()`: we'll handle the `NoResultFound`
                # case ourselves, rather than abort with HTTP 404.
                source = Source.query.filter(Source.uuid == source_uuid).one()
                utils.delete_collection(source.filesystem_id)
                succeeded.append(source_uuid)

            # Deletion is idempotent, so count nonexistent `Source`s as
            # successes.
            except NoResultFound:
                succeeded.append(source_uuid)

            except Exception as exc:
                current_app.logger.error(f"Failed to delete source {source_uuid}: {exc}")
                failed.append(source_uuid)

        # Return the lists of both failed and succeeded deletion operations no
        # matter what, so that the client can act directly on the results.
        return (
            jsonify(
                {
                    "failed": failed,
                    "succeeded": succeeded,
                }
            ),
            200 if len(failed) == 0 else 207,  # Success or Multi-Status
        )

    @api.route("/sources/<source_uuid>", methods=["GET", "DELETE"])
    def single_source(source_uuid: str) -> Tuple[flask.Response, int]:
        if request.method == "GET":
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            return jsonify(source.to_json()), 200
        elif request.method == "DELETE":
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            utils.delete_collection(source.filesystem_id)
            return jsonify({"message": "Source and submissions deleted"}), 200
        else:
            abort(405)

    @api.route("/sources/<source_uuid>/add_star", methods=["POST"])
    def add_star(source_uuid: str) -> Tuple[flask.Response, int]:
        source = get_or_404(Source, source_uuid, column=Source.uuid)
        utils.make_star_true(source.filesystem_id)
        db.session.commit()
        return jsonify({"message": "Star added"}), 201

    @api.route("/sources/<source_uuid>/remove_star", methods=["DELETE"])
    def remove_star(source_uuid: str) -> Tuple[flask.Response, int]:
        source = get_or_404(Source, source_uuid, column=Source.uuid)
        utils.make_star_false(source.filesystem_id)
        db.session.commit()
        return jsonify({"message": "Star removed"}), 200

    @api.route("/sources/<source_uuid>/flag", methods=["POST"])
    def flag(source_uuid: str) -> Tuple[flask.Response, int]:
        return (
            jsonify({"message": "Sources no longer need to be flagged for reply"}),
            200,
        )

    @api.route("/sources/<source_uuid>/conversation", methods=["DELETE"])
    def source_conversation(source_uuid: str) -> Tuple[flask.Response, int]:
        if request.method == "DELETE":
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            utils.delete_source_files(source.filesystem_id)
            return jsonify({"message": "Source data deleted"}), 200
        else:
            abort(405)

    @api.route("/sources/<source_uuid>/submissions", methods=["GET"])
    def all_source_submissions(source_uuid: str) -> Tuple[flask.Response, int]:
        source = get_or_404(Source, source_uuid, column=Source.uuid)
        return (
            jsonify({"submissions": [submission.to_json() for submission in source.submissions]}),
            200,
        )

    @api.route("/sources/<source_uuid>/submissions/<submission_uuid>/download", methods=["GET"])
    def download_submission(source_uuid: str, submission_uuid: str) -> flask.Response:
        get_or_404(Source, source_uuid, column=Source.uuid)
        submission = get_or_404(Submission, submission_uuid, column=Submission.uuid)
        return utils.serve_file_with_etag(submission)

    @api.route("/sources/<source_uuid>/replies/<reply_uuid>/download", methods=["GET"])
    def download_reply(source_uuid: str, reply_uuid: str) -> flask.Response:
        get_or_404(Source, source_uuid, column=Source.uuid)
        reply = get_or_404(Reply, reply_uuid, column=Reply.uuid)

        return utils.serve_file_with_etag(reply)

    @api.route(
        "/sources/<source_uuid>/submissions/<submission_uuid>",
        methods=["GET", "DELETE"],
    )
    def single_submission(source_uuid: str, submission_uuid: str) -> Tuple[flask.Response, int]:
        if request.method == "GET":
            get_or_404(Source, source_uuid, column=Source.uuid)
            submission = get_or_404(Submission, submission_uuid, column=Submission.uuid)
            return jsonify(submission.to_json()), 200
        elif request.method == "DELETE":
            get_or_404(Source, source_uuid, column=Source.uuid)
            submission = get_or_404(Submission, submission_uuid, column=Submission.uuid)
            utils.delete_file_object(submission)
            return jsonify({"message": "Submission deleted"}), 200
        else:
            abort(405)

    @api.route("/sources/<source_uuid>/replies", methods=["GET", "POST"])
    def all_source_replies(source_uuid: str) -> Tuple[flask.Response, int]:
        if request.method == "GET":
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            return (
                jsonify({"replies": [reply.to_json() for reply in source.replies]}),
                200,
            )
        elif request.method == "POST":
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            if request.json is None:
                abort(400, "please send requests in valid JSON")

            if "reply" not in request.json:
                abort(400, "reply not found in request body")

            data = request.json
            if not data["reply"]:
                abort(400, "reply should not be empty")

            source.interaction_count += 1
            try:
                filename = Storage.get_default().save_pre_encrypted_reply(
                    source.filesystem_id,
                    source.interaction_count,
                    source.journalist_filename,
                    data["reply"],
                )
            except NotEncrypted:
                return jsonify({"message": "You must encrypt replies client side"}), 400

            # issue #3918
            filename = path.basename(filename)

            reply = Reply(session.get_user(), source, filename, Storage.get_default())

            reply_uuid = data.get("uuid", None)
            if reply_uuid is not None:
                # check that is is parseable
                try:
                    UUID(reply_uuid)
                except ValueError:
                    abort(400, "'uuid' was not a valid UUID")
                reply.uuid = reply_uuid

            try:
                db.session.add(reply)
                seen_reply = SeenReply(reply=reply, journalist=session.get_user())
                db.session.add(seen_reply)
                db.session.add(source)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                if "UNIQUE constraint failed: replies.uuid" in str(e):
                    abort(409, "That UUID is already in use.")
                else:
                    raise e

            return (
                jsonify(
                    {
                        "message": "Your reply has been stored",
                        "uuid": reply.uuid,
                        "filename": reply.filename,
                    }
                ),
                201,
            )
        else:
            abort(405)

    @api.route("/sources/<source_uuid>/replies/<reply_uuid>", methods=["GET", "DELETE"])
    def single_reply(source_uuid: str, reply_uuid: str) -> Tuple[flask.Response, int]:
        get_or_404(Source, source_uuid, column=Source.uuid)
        reply = get_or_404(Reply, reply_uuid, column=Reply.uuid)
        if request.method == "GET":
            return jsonify(reply.to_json()), 200
        elif request.method == "DELETE":
            utils.delete_file_object(reply)
            return jsonify({"message": "Reply deleted"}), 200
        else:
            abort(405)

    @api.route("/submissions", methods=["GET"])
    def get_all_submissions() -> Tuple[flask.Response, int]:
        submissions = Submission.query.all()
        return (
            jsonify(
                {
                    "submissions": [
                        submission.to_json() for submission in submissions if submission.source
                    ]
                }
            ),
            200,
        )

    @api.route("/replies", methods=["GET"])
    def get_all_replies() -> Tuple[flask.Response, int]:
        replies = Reply.query.all()
        return (
            jsonify({"replies": [reply.to_json() for reply in replies if reply.source]}),
            200,
        )

    @api.route("/seen", methods=["POST"])
    def seen() -> Tuple[flask.Response, int]:
        """
        Lists or marks the source conversation items that the journalist has seen.
        """

        if request.method == "POST":
            if request.json is None or not isinstance(request.json, collections.abc.Mapping):
                abort(400, "Please send requests in valid JSON.")

            if not any(map(request.json.get, ["files", "messages", "replies"])):
                abort(400, "Please specify the resources to mark seen.")

            # gather everything to be marked seen. if any don't exist,
            # reject the request.
            targets: Set[Union[Submission, Reply]] = set()
            for file_uuid in request.json.get("files", []):
                f = Submission.query.filter(Submission.uuid == file_uuid).one_or_none()
                if f is None or not f.is_file:
                    abort(404, f"file not found: {file_uuid}")
                targets.add(f)

            for message_uuid in request.json.get("messages", []):
                m = Submission.query.filter(Submission.uuid == message_uuid).one_or_none()
                if m is None or not m.is_message:
                    abort(404, f"message not found: {message_uuid}")
                targets.add(m)

            for reply_uuid in request.json.get("replies", []):
                r = Reply.query.filter(Reply.uuid == reply_uuid).one_or_none()
                if r is None:
                    abort(404, f"reply not found: {reply_uuid}")
                targets.add(r)

            # now mark everything seen.
            utils.mark_seen(list(targets), session.get_user())

            return jsonify({"message": "resources marked seen"}), 200

        abort(405)

    @api.route("/user", methods=["GET"])
    def get_current_user() -> Tuple[flask.Response, int]:
        return jsonify(session.get_user().to_json()), 200

    @api.route("/users", methods=["GET"])
    def get_all_users() -> Tuple[flask.Response, int]:
        users = Journalist.query.all()
        return jsonify({"users": [user.to_json(all_info=False) for user in users]}), 200

    @api.route("/logout", methods=["POST"])
    def logout() -> Tuple[flask.Response, int]:
        session.destroy()
        return jsonify({"message": "Your token has been revoked."}), 200

    def _handle_api_http_exception(
        error: werkzeug.exceptions.HTTPException,
    ) -> Tuple[flask.Response, int]:
        # Workaround for no blueprint-level 404/5 error handlers, see:
        # https://github.com/pallets/flask/issues/503#issuecomment-71383286
        response = jsonify({"error": error.name, "message": error.description})

        return response, error.code  # type: ignore

    for code in default_exceptions:
        api.errorhandler(code)(_handle_api_http_exception)

    return api
