from flask_babel import gettext
from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import InputRequired, Regexp, Length

from db import Source


class LoginForm(FlaskForm):
    codename = PasswordField('codename', validators=[
        InputRequired(message=gettext('This field is required.')),
        Length(1, Source.MAX_CODENAME_LEN,
               message=gettext('Field must be between 1 and '
                               '{max_codename_len} characters long. '.format(
                                   max_codename_len=Source.MAX_CODENAME_LEN))),
        # The regex here allows either whitespace (\s) or
        # alphanumeric characters (\W) except underscore (_)
        Regexp(r'(\s|[^\W_])+$', message=gettext('Invalid input.'))
    ])
