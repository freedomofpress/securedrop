import operator
import os

from datetime import datetime
from flask import (Blueprint, render_template, flash, redirect, url_for, g,
                   session, current_app)
from flask_babel import gettext
from sqlalchemy.exc import IntegrityError

import crypto_util
import store

from db import Source, db_session
from source_app.decorators import login_required
from source_app.utils import logged_in, generate_unique_codename, async_genkey


def add_blueprints(app):
    app.register_blueprint(_main_blueprint())


def _main_blueprint():
    view = Blueprint('main', 'main')

    @view.route('/')
    def index():
        return render_template('index.html')

    @view.route('/generate', methods=('GET', 'POST'))
    def generate():
        if logged_in():
            flash(gettext(
                "You were redirected because you are already logged in. "
                "If you want to create a new account, you should log out "
                "first."),
                  "notification")
            return redirect(url_for('.lookup'))

        codename = generate_unique_codename()
        session['codename'] = codename
        return render_template('generate.html', codename=codename)

    @view.route('/create', methods=['POST'])
    def create():
        filesystem_id = crypto_util.hash_codename(session['codename'])

        source = Source(filesystem_id, crypto_util.display_id())
        db_session.add(source)
        try:
            db_session.commit()
        except IntegrityError as e:
            current_app.logger.error(
                "Attempt to create a source with duplicate codename: %s" %
                (e,))
        else:
            os.mkdir(store.path(filesystem_id))

        session['logged_in'] = True
        return redirect(url_for('.lookup'))

    @view.route('/lookup', methods=('GET',))
    @login_required
    def lookup():
        replies = []
        for reply in g.source.replies:
            reply_path = store.path(g.filesystem_id, reply.filename)
            try:
                reply.decrypted = crypto_util.decrypt(
                    g.codename,
                    open(reply_path).read()).decode('utf-8')
            except UnicodeDecodeError:
                current_app.logger.error("Could not decode reply %s" %
                                         reply.filename)
            else:
                reply.date = datetime.utcfromtimestamp(
                    os.stat(reply_path).st_mtime)
                replies.append(reply)

        # Sort the replies by date
        replies.sort(key=operator.attrgetter('date'), reverse=True)

        # Generate a keypair to encrypt replies from the journalist
        # Only do this if the journalist has flagged the source as one
        # that they would like to reply to. (Issue #140.)
        if not crypto_util.getkey(g.filesystem_id) and g.source.flagged:
            async_genkey(g.filesystem_id, g.codename)

        return render_template(
            'lookup.html',
            codename=g.codename,
            replies=replies,
            flagged=g.source.flagged,
            haskey=crypto_util.getkey(
                g.filesystem_id))

    return view
