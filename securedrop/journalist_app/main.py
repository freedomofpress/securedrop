# -*- coding: utf-8 -*-

from datetime import datetime
from flask import (Blueprint, request, current_app, session, url_for, redirect,
                   render_template)

from db import db_session
from journalist_app.utils import validate_user


def make_blueprint(config):
    view = Blueprint('main', __name__)

    @view.route('/login', methods=('GET', 'POST'))
    def login():
        if request.method == 'POST':
            user = validate_user(request.form['username'],
                                 request.form['password'],
                                 request.form['token'])
            if user:
                current_app.logger.info("'{}' logged in with the token {}"
                                        .format(request.form['username'],
                                                request.form['token']))

                # Update access metadata
                user.last_access = datetime.utcnow()
                db_session.add(user)
                db_session.commit()

                session['uid'] = user.id
                return redirect(url_for('index'))

        return render_template("login.html")

    @view.route('/logout')
    def logout():
        session.pop('uid', None)
        session.pop('expires', None)
        return redirect(url_for('index'))

    return view
