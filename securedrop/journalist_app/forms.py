# -*- coding: utf-8 -*-

from flask_babel import lazy_gettext as gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (TextAreaField, TextField, BooleanField, HiddenField,
                     ValidationError)
from wtforms.validators import InputRequired, Optional

from models import Journalist


def otp_secret_validation(form, field):
    strip_whitespace = field.data.replace(' ', '')
    if len(strip_whitespace) != 40:
        raise ValidationError(gettext(
            'HOTP secrets are 40 characters long - '
            'you have entered {num_chars}.'.format(
                num_chars=len(strip_whitespace)
            )))


def minimum_length_validation(form, field):
    if len(field.data) < Journalist.MIN_USERNAME_LEN:
        raise ValidationError(
            gettext('Field must be at least {min_chars} '
                    'characters long but only got '
                    '{num_chars}.'.format(
                        min_chars=Journalist.MIN_USERNAME_LEN,
                        num_chars=len(field.data))))


def name_length_validation(form, field):
    if len(field.data) > Journalist.MAX_NAME_LEN:
        raise ValidationError(gettext(
            'Field can not be more than {max_chars} characters.'
            .format(max_chars=Journalist.MAX_NAME_LEN)))


class NewUserForm(FlaskForm):
    username = TextField('username', validators=[
        InputRequired(message=gettext('This field is required.')),
        minimum_length_validation
    ])
    first_name = TextField('first_name', validators=[name_length_validation, Optional()])
    last_name = TextField('last_name', validators=[name_length_validation, Optional()])
    password = HiddenField('password')
    is_admin = BooleanField('is_admin')
    is_hotp = BooleanField('is_hotp')
    otp_secret = TextField('otp_secret', validators=[
        otp_secret_validation,
        Optional()
    ])


class ReplyForm(FlaskForm):
    message = TextAreaField(
        'Message',
        id="content-area",
        validators=[
            InputRequired(message=gettext(
                'You cannot send an empty reply.')),
        ],
    )


class LogoForm(FlaskForm):
    logo = FileField(validators=[
        FileRequired(message=gettext('File required.')),
        FileAllowed(['png'],
                    message=gettext("You can only upload PNG image files."))
    ])
