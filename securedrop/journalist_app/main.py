from datetime import datetime, timezone
from pathlib import Path
from typing import Union

import store
import werkzeug
from actions.sources_actions import GetSingleSourceAction, SearchSourcesAction
from db import db
from encryption import EncryptionManager
from flask import (
    Blueprint,
    Markup,
    abort,
    current_app,
    escape,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_babel import gettext
from journalist_app.forms import ReplyForm
from journalist_app.sessions import session
from journalist_app.utils import bulk_delete, download, validate_user
from models import Reply, SeenReply, Submission
from sqlalchemy.sql import func
from store import Storage


def make_blueprint() -> Blueprint:
    view = Blueprint("main", __name__)

    @view.route("/login", methods=("GET", "POST"))
    def login() -> Union[str, werkzeug.Response]:
        if request.method == "POST":
            user = validate_user(
                request.form["username"],
                request.form["password"],
                request.form["token"],
            )
            if user:
                current_app.logger.info(
                    "'{}' logged in with the two-factor code {}".format(
                        request.form["username"], request.form["token"]
                    )
                )

                # Update access metadata
                user.last_access = datetime.now(timezone.utc)
                db.session.add(user)
                db.session.commit()

                session["uid"] = user.id
                session.regenerate()
                return redirect(url_for("main.index"))

        return render_template("login.html")

    @view.route("/logout")
    def logout() -> werkzeug.Response:
        session.destroy()
        return redirect(url_for("main.index"))

    @view.route("/")
    def index() -> str:
        # Fetch all sources
        all_sources = SearchSourcesAction(db_session=db.session).perform()

        # Add "num_unread" attributes to the source entities
        # First gather the count of unread submissions for each source ID
        # TODO(AD): Remove this and add support for pagination; switch to a (hybrid?) property
        unread_submission_counts_results = (
            db.session.query(Submission.source_id, func.count("*"))
            .filter_by(downloaded=False)
            .group_by(Submission.source_id)
            .all()
        )
        source_ids_to_unread_submission_counts = {
            source_id: subs_count for source_id, subs_count in unread_submission_counts_results
        }
        # TODO(AD): Remove this dynamically-added attribute; switch to a (hybrid?) property
        for source in all_sources:
            source.num_unread = source_ids_to_unread_submission_counts.get(source.id, 0)

        response = render_template(
            "index.html",
            unstarred=[src for src in all_sources if not src.is_starred],
            starred=[src for src in all_sources if src.is_starred],
        )
        return response

    @view.route("/reply", methods=("POST",))
    def reply() -> werkzeug.Response:
        """Attempt to send a Reply from a Journalist to a Source. Empty
        messages are rejected, and an informative error message is flashed
        on the client. In the case of unexpected errors involving database
        transactions (potentially caused by racing request threads that
        modify the same the database object) logging is done in such a way
        so as not to write potentially sensitive information to disk, and a
        generic error message is flashed on the client.

        Returns:
           flask.Response: The user is redirected to the same Source
               collection view, regardless if the Reply is created
               successfully.
        """
        form = ReplyForm()
        if not form.validate_on_submit():
            for error in form.message.errors:
                flash(error, "error")
            return redirect(url_for("col.col", filesystem_id=g.filesystem_id))

        source = GetSingleSourceAction(
            db_session=db.session, filesystem_id=g.filesystem_id
        ).perform()
        source.interaction_count += 1
        filename = "{}-{}-reply.gpg".format(source.interaction_count, source.journalist_filename)
        EncryptionManager.get_default().encrypt_journalist_reply(
            for_source_with_filesystem_id=g.filesystem_id,
            reply_in=form.message.data,
            encrypted_reply_path_out=Path(Storage.get_default().path(g.filesystem_id, filename)),
        )

        try:
            reply = Reply(session.get_user(), source, filename, Storage.get_default())
            db.session.add(reply)
            seen_reply = SeenReply(reply=reply, journalist=session.get_user())
            db.session.add(seen_reply)
            db.session.commit()
            store.async_add_checksum_for_file(reply, Storage.get_default())
        except Exception as exc:
            flash(
                gettext("An unexpected error occurred! Please " "inform your admin."),
                "error",
            )
            # We take a cautious approach to logging here because we're dealing
            # with responses to sources. It's possible the exception message
            # could contain information we don't want to write to disk.
            current_app.logger.error(
                "Reply from '{}' (ID {}) failed: {}!".format(
                    session.get_user().username, session.get_uid(), exc.__class__
                )
            )
        else:

            flash(
                Markup(
                    "<b>{}</b> {}".format(
                        # Translators: Precedes a message confirming the success of an operation.
                        escape(gettext("Success!")),
                        escape(
                            gettext("The source will receive your reply " "next time they log in.")
                        ),
                    )
                ),
                "success",
            )
        finally:
            return redirect(url_for("col.col", filesystem_id=g.filesystem_id))

    @view.route("/bulk", methods=("POST",))
    def bulk() -> Union[str, werkzeug.Response]:
        action = request.form["action"]
        error_redirect = url_for("col.col", filesystem_id=g.filesystem_id)
        doc_names_selected = request.form.getlist("doc_names_selected")

        source = GetSingleSourceAction(
            db_session=db.session, filesystem_id=g.filesystem_id
        ).perform()
        selected_docs = [doc for doc in source.collection if doc.filename in doc_names_selected]

        if selected_docs == []:
            if action == "download":
                flash(
                    Markup(
                        "<b>{}</b> {}".format(
                            # Translators: Error shown when a user has not selected items to act on.
                            escape(gettext("Nothing Selected")),
                            escape(gettext("You must select one or more items for download")),
                        )
                    ),
                    "error",
                )
            elif action == "delete":
                flash(
                    Markup(
                        "<b>{}</b> {}".format(
                            # Translators: Error shown when a user has not selected items to act on.
                            escape(gettext("Nothing Selected")),
                            escape(gettext("You must select one or more items for deletion")),
                        )
                    ),
                    "error",
                )
            else:
                abort(400)

            return redirect(error_redirect)

        if action == "download":
            source = GetSingleSourceAction(
                db_session=db.session, filesystem_id=g.filesystem_id
            ).perform()
            return download(
                source.journalist_filename,
                selected_docs,
                on_error_redirect=error_redirect,
            )
        elif action == "delete":
            return bulk_delete(g.filesystem_id, selected_docs)
        else:
            abort(400)

    @view.route("/download_unread/<filesystem_id>")
    def download_unread_filesystem_id(filesystem_id: str) -> werkzeug.Response:
        source = GetSingleSourceAction(db_session=db.session, filesystem_id=filesystem_id).perform()

        unseen_submissions = (
            Submission.query.filter(Submission.source_id == source.id)
            .filter(~Submission.seen_files.any(), ~Submission.seen_messages.any())
            .all()
        )
        if len(unseen_submissions) == 0:
            flash(gettext("No unread submissions for this source."), "error")
            return redirect(url_for("col.col", filesystem_id=filesystem_id))

        return download(source.journalist_filename, unseen_submissions)

    return view
