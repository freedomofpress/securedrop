import wtforms
from flask import abort
from flask_babel import lazy_gettext as gettext
from flask_wtf import FlaskForm
from models import InstanceConfig, Submission
from passphrases import PassphraseGenerator
from wtforms import FileField, PasswordField, StringField, TextAreaField
from wtforms.validators import InputRequired, Length, Regexp, ValidationError


class LoginForm(FlaskForm):

    codename = PasswordField(
        "codename",
        validators=[
            InputRequired(message=gettext("This field is required.")),
            Length(
                1,
                PassphraseGenerator.MAX_PASSPHRASE_LENGTH,
                message=gettext(
                    "Field must be between 1 and "
                    "{max_codename_len} characters long.".format(
                        max_codename_len=PassphraseGenerator.MAX_PASSPHRASE_LENGTH
                    )
                ),
            ),
            # Make sure to allow dashes since some words in the wordlist have them
            Regexp(r"[\sA-Za-z0-9-]+$", message=gettext("Invalid input.")),
        ],
    )


class SubmissionForm(FlaskForm):
    msg = TextAreaField(
        "msg",
        render_kw={
            "placeholder": gettext("Write a message."),
            "aria-label": gettext("Write a message."),
        },
    )
    fh = FileField("fh", render_kw={"aria-label": gettext("Select a file to upload.")})
    antispam = StringField(id="text", name="text")

    def validate_msg(self, field: wtforms.Field) -> None:
        if len(field.data) > Submission.MAX_MESSAGE_LEN:
            message = gettext("Message text too long.")
            if InstanceConfig.get_default().allow_document_uploads:
                message = "{} {}".format(
                    message,
                    gettext(
                        "Large blocks of text must be uploaded as a file, not copied and pasted."
                    ),
                )
            raise ValidationError(message)

    def validate_antispam(self, field: wtforms.Field) -> None:
        """If the antispam field has any contents, abort with a 403"""
        if field.data:
            abort(403)
