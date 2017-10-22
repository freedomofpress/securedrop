# -*- coding: utf-8 -*-

from flask_babel import gettext
from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import InputRequired


class ReplyForm(FlaskForm):
    message = TextAreaField(
        u'Message',
        id="content-area",
        validators=[
            InputRequired(message=gettext('You cannot send an empty reply.')),
        ],
    )
