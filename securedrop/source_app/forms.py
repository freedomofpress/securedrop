from flask_babel import lazy_gettext
from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import InputRequired, Regexp, Length

from db import Source


class LoginForm(FlaskForm):
    codename = PasswordField('codename', validators=[
        InputRequired(message=lazy_gettext('This field is required.')),
        Length(1, Source.MAX_CODENAME_LEN,
               message=lazy_gettext(
                   'Field must be between 1 and '
                   '{max_codename_len} characters long.'.format(
                       max_codename_len=Source.MAX_CODENAME_LEN))),
        # Make sure to allow dashes since some words in the wordlist have them
        Regexp(r'[\sA-Za-z0-9-]+$', message=lazy_gettext('Invalid input.'))
    ])
