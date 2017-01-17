# -*- coding: utf-8 -*-
from wtforms import Form, StringField, TextAreaField
from wtforms.validators import Length
from wtforms import ValidationError
from wtforms.widgets import TextArea


def validate_pgp_key(form, field):
    if 'PGP PUBLIC KEY' not in field.data:
        raise ValidationError('Please submit inline PGP key!')


class EditProfileForm(Form):
    full_name = StringField('Real name', [Length(min=0, max=64)])
    about = TextAreaField('About me', [Length(min=0, max=3000)])
    pgp_key = TextAreaField('PGP Key', [validate_pgp_key,
                                        Length(min=0, max=20000)],
                            widget=TextArea())
