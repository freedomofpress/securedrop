# -*- coding: utf-8 -*-

from flask_babel import lazy_gettext as gettext, ngettext
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import Field
from wtforms import (TextAreaField, StringField, BooleanField, HiddenField, IntegerField,
                     ValidationError)
from wtforms.validators import InputRequired, Optional, DataRequired, StopValidation

from models import Journalist, InstanceConfig, HOTP_SECRET_LENGTH

from typing import Any

import typing


class RequiredIf(DataRequired):

    def __init__(self,
                 other_field_name: str,
                 custom_message: typing.Optional[str] = None,
                 *args: Any, **kwargs: Any) -> None:

        self.other_field_name = other_field_name
        if custom_message is not None:
            self.custom_message = custom_message
        else:
            self.custom_message = ""

    def __call__(self, form: FlaskForm, field: Field) -> None:
        if self.other_field_name in form:
            other_field = form[self.other_field_name]
            if bool(other_field.data):
                if self.custom_message != "":
                    self.message = self.custom_message
                else:
                    self.message = gettext(
                        'The "{name}" field is required when "{other_name}" is set.'
                        .format(other_name=self.other_field_name, name=field.name))
                super(RequiredIf, self).__call__(form, field)
            else:
                field.errors[:] = []
                raise StopValidation()
        else:
            raise ValidationError(
                gettext(
                    'The "{other_name}" field was not found - it is required by "{name}".'
                    .format(other_name=self.other_field_name, name=field.name))
                )


def otp_secret_validation(form: FlaskForm, field: Field) -> None:
    strip_whitespace = field.data.replace(' ', '')
    input_length = len(strip_whitespace)
    if input_length != HOTP_SECRET_LENGTH:
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
                'Must be at least {num} character long.',
                'Must be at least {num} characters long.',
                Journalist.MIN_USERNAME_LEN
            ).format(num=Journalist.MIN_USERNAME_LEN)
        )


def name_length_validation(form: FlaskForm, field: Field) -> None:
    if len(field.data) > Journalist.MAX_NAME_LEN:
        raise ValidationError(
            ngettext(
                'Cannot be longer than {num} character.',
                'Cannot be longer than {num} characters.',
                Journalist.MAX_NAME_LEN
            ).format(num=Journalist.MAX_NAME_LEN)
        )


def check_orgname(form: FlaskForm, field: Field) -> None:
    if len(field.data) > InstanceConfig.MAX_ORG_NAME_LEN:
        raise ValidationError(
            ngettext(
                'Cannot be longer than {num} character.',
                'Cannot be longer than {num} characters.',
                InstanceConfig.MAX_ORG_NAME_LEN
            ).format(num=InstanceConfig.MAX_ORG_NAME_LEN)
        )


def check_invalid_usernames(form: FlaskForm, field: Field) -> None:
    if field.data in Journalist.INVALID_USERNAMES:
        raise ValidationError(gettext(
            "This username is invalid because it is reserved for internal use by the software."))


def check_message_length(form: FlaskForm, field: Field) -> None:
    msg_len = field.data
    if not isinstance(msg_len, int) or msg_len < 0:
        raise ValidationError(gettext("Please specify an integer value greater than 0."))


class NewUserForm(FlaskForm):
    username = StringField('username', validators=[
        InputRequired(message=gettext('This field is required.')),
        minimum_length_validation, check_invalid_usernames
        ],
        render_kw={'aria-describedby': 'username-notes'},
    )
    first_name = StringField('first_name', validators=[name_length_validation, Optional()],
                             render_kw={'aria-describedby': 'name-notes'})
    last_name = StringField('last_name', validators=[name_length_validation, Optional()],
                            render_kw={'aria-describedby': 'name-notes'})
    password = HiddenField('password')
    is_admin = BooleanField('is_admin')
    is_hotp = BooleanField('is_hotp')
    otp_secret = StringField('otp_secret', validators=[
        RequiredIf("is_hotp"),
        otp_secret_validation
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
    prevent_document_uploads = BooleanField(
                                            'prevent_document_uploads',
                                            false_values=('false', 'False', '')
                                           )
    prevent_short_messages = BooleanField(
                                            'prevent_short_messages',
                                            false_values=('false', 'False', '')
                                           )
    min_message_length = IntegerField('min_message_length',
                                      validators=[
                                          RequiredIf(
                                              'prevent_short_messages',
                                              gettext("To configure a minimum message length, "
                                                      "you must set the required number of "
                                                      "characters.")),
                                          check_message_length],
                                      render_kw={
                                          'aria-describedby': 'message-length-notes'})
    reject_codename_messages = BooleanField(
                                            'reject_codename_messages',
                                            false_values=('false', 'False', '')
                                           )


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
