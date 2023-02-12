import binascii
import os
from typing import Optional, Union

import werkzeug
from db import db
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_babel import gettext
from journalist_app.decorators import admin_required
from journalist_app.forms import LogoForm, NewUserForm, OrgNameForm, SubmissionPreferencesForm
from journalist_app.sessions import session
from journalist_app.utils import commit_account_changes, set_diceware_password, validate_hotp_secret
from models import (
    FirstOrLastNameError,
    InstanceConfig,
    InvalidUsernameException,
    Journalist,
    PasswordError,
    Submission,
)
from passphrases import PassphraseGenerator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from two_factor import OtpTokenInvalid, random_base32


_ADMIN_NEW_OTP_IS_TOTP = "admin_new_otp_is_totp"
_ADMIN_NEW_OTP_SECRET = "admin_new_otp_secret"


def make_blueprint() -> Blueprint:
    view = Blueprint("admin", __name__)

    @view.route("/", methods=("GET", "POST"))
    @admin_required
    def index() -> str:
        users = Journalist.query.filter(Journalist.username != "deleted").all()
        return render_template("admin.html", users=users)

    @view.route("/config", methods=("GET", "POST"))
    @admin_required
    def manage_config() -> Union[str, werkzeug.Response]:
        if InstanceConfig.get_default().initial_message_min_len > 0:
            prevent_short_messages = True
        else:
            prevent_short_messages = False

        # The UI document upload prompt ("prevent") is the opposite of the setting ("allow")
        submission_preferences_form = SubmissionPreferencesForm(
            prevent_document_uploads=not InstanceConfig.get_default().allow_document_uploads,
            prevent_short_messages=prevent_short_messages,
            min_message_length=InstanceConfig.get_default().initial_message_min_len,
            reject_codename_messages=InstanceConfig.get_default().reject_message_with_codename,
        )
        organization_name_form = OrgNameForm(
            organization_name=InstanceConfig.get_default().organization_name
        )
        logo_form = LogoForm()
        if logo_form.validate_on_submit():
            f = logo_form.logo.data

            if current_app.static_folder is None:
                abort(500)
            custom_logo_filepath = os.path.join(current_app.static_folder, "i", "custom_logo.png")
            try:
                f.save(custom_logo_filepath)
                flash(gettext("Image updated."), "logo-success")
            except Exception:
                flash(
                    # Translators: This error is shown when an uploaded image cannot be used.
                    gettext("Unable to process the image file. Please try another one."),
                    "logo-error",
                )
            finally:
                return redirect(url_for("admin.manage_config") + "#config-logoimage")
        else:
            for field, errors in list(logo_form.errors.items()):
                for error in errors:
                    flash(error, "logo-error")
            return render_template(
                "config.html",
                submission_preferences_form=submission_preferences_form,
                organization_name_form=organization_name_form,
                max_len=Submission.MAX_MESSAGE_LEN,
                logo_form=logo_form,
            )

    @view.route("/update-submission-preferences", methods=["POST"])
    @admin_required
    def update_submission_preferences() -> Optional[werkzeug.Response]:
        form = SubmissionPreferencesForm()
        if form.validate_on_submit():
            # The UI prompt ("prevent") is the opposite of the setting ("allow"):
            allow_uploads = not form.prevent_document_uploads.data

            if form.prevent_short_messages.data:
                msg_length = form.min_message_length.data
            else:
                msg_length = 0

            reject_codenames = form.reject_codename_messages.data

            InstanceConfig.update_submission_prefs(allow_uploads, msg_length, reject_codenames)
            flash(gettext("Preferences saved."), "submission-preferences-success")
            return redirect(url_for("admin.manage_config") + "#config-preventuploads")
        else:
            for field, errors in list(form.errors.items()):
                for error in errors:
                    flash(
                        gettext("Preferences not updated.") + " " + error,
                        "submission-preferences-error",
                    )
        return redirect(url_for("admin.manage_config") + "#config-preventuploads")

    @view.route("/update-org-name", methods=["POST"])
    @admin_required
    def update_org_name() -> Union[str, werkzeug.Response]:
        form = OrgNameForm()
        if form.validate_on_submit():
            try:
                value = request.form["organization_name"]
                InstanceConfig.set_organization_name(value)
                flash(gettext("Preferences saved."), "org-name-success")
            except Exception:
                flash(gettext("Failed to update organization name."), "org-name-error")
            return redirect(url_for("admin.manage_config") + "#config-orgname")
        else:
            for field, errors in list(form.errors.items()):
                for error in errors:
                    flash(error, "org-name-error")
        return redirect(url_for("admin.manage_config") + "#config-orgname")

    @view.route("/add", methods=("GET", "POST"))
    @admin_required
    def add_user() -> Union[str, werkzeug.Response]:
        form = NewUserForm()
        if form.validate_on_submit():
            form_valid = True
            username = request.form["username"]
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            password = request.form["password"]
            is_admin = bool(request.form.get("is_admin"))

            try:
                otp_secret = None
                if request.form.get("is_hotp", False):
                    otp_secret = request.form.get("otp_secret", "")
                new_user = Journalist(
                    username=username,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_admin=is_admin,
                    otp_secret=otp_secret,
                )
                db.session.add(new_user)
                db.session.commit()
            except PasswordError:
                flash(
                    gettext(
                        "There was an error with the autogenerated password. "
                        "User not created. Please try again."
                    ),
                    "error",
                )
                form_valid = False
            except (binascii.Error, TypeError) as e:
                if "Non-hexadecimal digit found" in str(e):
                    flash(
                        gettext(
                            "Invalid HOTP secret format: "
                            "please only submit letters A-F and numbers 0-9."
                        ),
                        "error",
                    )
                else:
                    flash(
                        gettext("An unexpected error occurred! " "Please inform your admin."),
                        "error",
                    )
                form_valid = False
            except InvalidUsernameException as e:
                form_valid = False
                # Translators: Here, "{message}" explains the problem with the username.
                flash(gettext("Invalid username: {message}").format(message=e), "error")
            except IntegrityError as e:
                db.session.rollback()
                form_valid = False
                if "UNIQUE constraint failed: journalists.username" in str(e):
                    flash(
                        gettext('Username "{username}" already taken.').format(username=username),
                        "error",
                    )
                else:
                    flash(
                        gettext(
                            "An error occurred saving this user"
                            " to the database."
                            " Please inform your admin."
                        ),
                        "error",
                    )
                    current_app.logger.error("Adding user " "'{}' failed: {}".format(username, e))

            if form_valid:
                return redirect(url_for("admin.new_user_two_factor", uid=new_user.id))

        password = PassphraseGenerator.get_default().generate_passphrase(
            preferred_language=g.localeinfo.language
        )
        return render_template("admin_add_user.html", password=password, form=form)

    @view.route("/2fa", methods=("GET", "POST"))
    @admin_required
    def new_user_two_factor() -> Union[str, werkzeug.Response]:
        user = Journalist.query.get(request.args["uid"])

        # Update the user with the new OTP secret, if set. If the user enters a valid token,
        # the new secret is committed. Otherwise, the secret is rolled back after the request
        # completes.
        if _ADMIN_NEW_OTP_IS_TOTP in session and _ADMIN_NEW_OTP_SECRET in session:
            if session[_ADMIN_NEW_OTP_IS_TOTP]:
                user.set_totp_secret(session[_ADMIN_NEW_OTP_SECRET])
            else:
                user.set_hotp_secret(session[_ADMIN_NEW_OTP_SECRET])

        if request.method == "POST":
            token = request.form["token"]
            try:
                user.verify_2fa_token(token)

                db.session.commit()
                flash(
                    gettext(
                        'The two-factor code for user "{user}" was verified ' "successfully."
                    ).format(user=user.username),
                    "notification",
                )
                return redirect(url_for("admin.index"))

            except OtpTokenInvalid:
                db.session.rollback()
                flash(
                    gettext("There was a problem verifying the two-factor code. Please try again."),
                    "error",
                )

        page = render_template("admin_new_user_two_factor.html", user=user)
        db.session.rollback()
        return page

    @view.route("/reset-2fa-totp", methods=["POST"])
    @admin_required
    def reset_two_factor_totp() -> werkzeug.Response:
        uid = request.form["uid"]
        user = Journalist.query.get(uid)
        session[_ADMIN_NEW_OTP_IS_TOTP] = True
        session[_ADMIN_NEW_OTP_SECRET] = random_base32()
        return redirect(url_for("admin.new_user_two_factor", uid=user.id))

    @view.route("/reset-2fa-hotp", methods=["POST"])
    @admin_required
    def reset_two_factor_hotp() -> Union[str, werkzeug.Response]:
        uid = request.form["uid"]
        user = Journalist.query.get(uid)
        otp_secret = request.form.get("otp_secret", None)
        if otp_secret:
            if not validate_hotp_secret(user, otp_secret):
                return render_template("admin_edit_hotp_secret.html", uid=user.id)
            session[_ADMIN_NEW_OTP_IS_TOTP] = False
            session[_ADMIN_NEW_OTP_SECRET] = otp_secret
            return redirect(url_for("admin.new_user_two_factor", uid=user.id))
        else:
            return render_template("admin_edit_hotp_secret.html", uid=user.id)

    @view.route("/edit/<int:user_id>", methods=("GET", "POST"))
    @admin_required
    def edit_user(user_id: int) -> Union[str, werkzeug.Response]:
        user = Journalist.query.get(user_id)

        if request.method == "POST":
            if request.form.get("username", None):
                new_username = request.form["username"]

                try:
                    Journalist.check_username_acceptable(new_username)
                except InvalidUsernameException as e:
                    flash(
                        gettext("Invalid username: {message}").format(message=e),
                        "error",
                    )
                    return redirect(url_for("admin.edit_user", user_id=user_id))

                if new_username == user.username:
                    pass
                elif Journalist.query.filter_by(username=new_username).one_or_none():
                    flash(
                        gettext('Username "{username}" already taken.').format(
                            username=new_username
                        ),
                        "error",
                    )
                    return redirect(url_for("admin.edit_user", user_id=user_id))
                else:
                    user.username = new_username

            try:
                first_name = request.form["first_name"]
                Journalist.check_name_acceptable(first_name)
                user.first_name = first_name
            except FirstOrLastNameError as e:
                # Translators: Here, "{message}" explains the problem with the name.
                flash(gettext("Name not updated: {message}").format(message=e), "error")
                return redirect(url_for("admin.edit_user", user_id=user_id))

            try:
                last_name = request.form["last_name"]
                Journalist.check_name_acceptable(last_name)
                user.last_name = last_name
            except FirstOrLastNameError as e:
                flash(gettext("Name not updated: {message}").format(message=e), "error")
                return redirect(url_for("admin.edit_user", user_id=user_id))

            user.is_admin = bool(request.form.get("is_admin"))

            commit_account_changes(user)

        password = PassphraseGenerator.get_default().generate_passphrase(
            preferred_language=g.localeinfo.language
        )
        return render_template("edit_account.html", user=user, password=password)

    @view.route("/delete/<int:user_id>", methods=("POST",))
    @admin_required
    def delete_user(user_id: int) -> werkzeug.Response:
        user = Journalist.query.get(user_id)
        if user_id == session.get_uid():
            # Do not flash because the interface already has safe guards.
            # It can only happen by manually crafting a POST request
            current_app.logger.error(f"Admin {session.get_user().username} tried to delete itself")
            abort(403)
        elif not user:
            current_app.logger.error(
                "Admin {} tried to delete nonexistent user with pk={}".format(
                    session.get_user().username, user_id
                )
            )
            abort(404)
        elif user.is_deleted_user():
            # Do not flash because the interface does not expose this.
            # It can only happen by manually crafting a POST request
            current_app.logger.error(
                f'Admin {session.get_user().username} tried to delete "deleted" user'
            )
            abort(403)
        else:
            user.delete()
            current_app.session_interface.logout_user(user.id)  # type: ignore
            db.session.commit()
            flash(
                gettext("Deleted user '{user}'.").format(user=user.username),
                "notification",
            )

        return redirect(url_for("admin.index"))

    @view.route("/edit/<int:user_id>/new-password", methods=("POST",))
    @admin_required
    def new_password(user_id: int) -> werkzeug.Response:
        try:
            user = Journalist.query.get(user_id)
        except NoResultFound:
            abort(404)

        if user.id == session.get_uid():
            current_app.logger.error(
                "Admin {} tried to change their password without validation.".format(
                    session.get_user().username
                )
            )
            abort(403)

        password = request.form.get("password")
        if set_diceware_password(user, password, admin=True) is not False:
            current_app.session_interface.logout_user(user.id)  # type: ignore
            db.session.commit()
        return redirect(url_for("admin.edit_user", user_id=user_id))

    @view.route("/ossec-test", methods=("POST",))
    @admin_required
    def ossec_test() -> werkzeug.Response:
        current_app.logger.error("This is a test OSSEC alert")
        flash(
            gettext("Test alert sent. Please check your email."),
            "testalert-notification",
        )
        return redirect(url_for("admin.manage_config") + "#config-testalert")

    return view
