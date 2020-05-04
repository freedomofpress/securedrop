from flask import current_app
from flask_babel import lazy_gettext as gettext
from flask_wtf import FlaskForm
from wtforms import FileField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Regexp, Length, ValidationError

from models import Source, Submission


class LoginForm(FlaskForm):
    codename = PasswordField('codename', validators=[
        InputRequired(message=gettext('This field is required.')),
        Length(1, Source.MAX_CODENAME_LEN,
               message=gettext(
                   'Field must be between 1 and '
                   '{max_codename_len} characters long.'.format(
                       max_codename_len=Source.MAX_CODENAME_LEN))),
        # Make sure to allow dashes since some words in the wordlist have them
        Regexp(r'[\sA-Za-z0-9-]+$', message=gettext('Invalid input.'))
    ])


class SubmissionForm(FlaskForm):
    msg = TextAreaField("msg", render_kw={"placeholder": gettext("Write a message.")})
    fh = FileField("fh")

    def validate_msg(self, field):
        if len(field.data) > Submission.MAX_MESSAGE_LEN:
            message = gettext("Message text too long.")
            if current_app.instance_config.allow_document_uploads:
                message = "{} {}".format(
                    message,
                    gettext(
                        "Large blocks of text must be uploaded as a file, not copied and pasted."
                    )
                )
            raise ValidationError(message)
