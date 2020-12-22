# -*- coding: utf-8 -*-

from flask_babel import lazy_gettext as gettext, ngettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import Field
from wtforms import (TextAreaField, StringField, BooleanField, HiddenField,
                     ValidationError)
from wtforms.validators import InputRequired, Optional

from models import Journalist, InstanceConfig


def otp_secret_validation(form: FlaskForm, field: Field) -> None:
    strip_whitespace = field.data.replace(' ', '')
    input_length = len(strip_whitespace)
    if input_length != 40:
        raise ValidationError(
            ngettext(
                'HOTP secrets are 40 characters long - you have entered {num}.',
                'HOTP secrets are 40 characters long - you have entered {num}.',
                input_length
            ).format(num=input_length)
        )


def minimum_length_validation(form: FlaskForm, field: Field) -> None:
    if len(field.data) < Journalist.MIN_USERNAME_LEN:
        raise ValidationError(
            ngettext(
                'Must be at least {num} characters long.',
                'Must be at least {num} characters long.',
                Journalist.MIN_USERNAME_LEN
            ).format(num=Journalist.MIN_USERNAME_LEN)
        )


def name_length_validation(form: FlaskForm, field: Field) -> None:
    if len(field.data) > Journalist.MAX_NAME_LEN:
        raise ValidationError(
            ngettext(
                'Cannot be longer than {num} characters.',
                'Cannot be longer than {num} characters.',
                Journalist.MAX_NAME_LEN
            ).format(num=Journalist.MAX_NAME_LEN)
        )


def check_orgname(form: FlaskForm, field: Field) -> None:
    if len(field.data) > InstanceConfig.MAX_ORG_NAME_LEN:
        raise ValidationError(
            ngettext(
                'Cannot be longer than {num} characters.',
                'Cannot be longer than {num} characters.',
                InstanceConfig.MAX_ORG_NAME_LEN
            ).format(num=InstanceConfig.MAX_ORG_NAME_LEN)
        )


def check_invalid_usernames(form: FlaskForm, field: Field) -> None:
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


class OrgNameForm(FlaskForm):
    organization_name = StringField('organization_name', validators=[
        InputRequired(message=gettext('This field is required.')),
        check_orgname
    ])


class LogoForm(FlaskForm):
    logo = FileField(validators=[
        FileRequired(message=gettext('File required.')),
        FileAllowed(['png'],
                    message=gettext("You can only upload PNG image files."))
    ])
