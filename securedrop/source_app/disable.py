from datetime import date
from flask import render_template
from source_app.decorators import ignore_static
import platform

XENIAL_VER = "16.04"
TRUSTY_DISABLE_DATE = date(2019, 4, 30)


def disable_app(app):

    @app.before_request
    @ignore_static
    def disable_ui():
        if(platform.linux_distribution()[1] != XENIAL_VER and
                date.today() > TRUSTY_DISABLE_DATE):
            return render_template('disabled.html')
