# -*- coding: utf-8 -*-

from flask_babel import lazy_gettext as gettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (TextAreaField, StringField, BooleanField, HiddenField,
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
            gettext('Must be at least {min_chars} '
                    'characters long.'
                    .format(min_chars=Journalist.MIN_USERNAME_LEN)))


def name_length_validation(form, field):
    if len(field.data) > Journalist.MAX_NAME_LEN:
        raise ValidationError(gettext(
            'Cannot be longer than {max_chars} characters.'
            .format(max_chars=Journalist.MAX_NAME_LEN)))


def check_invalid_usernames(form, field):
    if field.data in Journalist.INVALID_USERNAMES:
        raise ValidationError(gettext(
            "This username is invalid because it is reserved for internal use by the software."))


class NewUserForm(FlaskForm):
    username = StringField('username', validators=[
        InputRequired(message=gettext('This field is required.')),
        minimum_length_validation, check_invalid_usernames
    ])
    first_name = StringField('first_name', validators=[name_length_validation, Optional()])
    last_name = StringField('last_name', validators=[name_length_validation, Optional()])
    password = HiddenField('password')
    is_admin = BooleanField('is_admin')
    is_hotp = BooleanField('is_hotp')
    otp_secret = StringField('otp_secret', validators=[
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


class SubmissionPreferencesForm(FlaskForm):
    prevent_document_uploads = BooleanField('prevent_document_uploads')


class LogoForm(FlaskForm):
    logo = FileField(validators=[
        FileRequired(message=gettext('File required.')),
        FileAllowed(['png'],
                    message=gettext("You can only upload PNG image files."))
    ])
