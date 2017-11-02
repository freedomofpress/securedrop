# -*- coding: utf-8 -*-

from datetime import datetime
from flask import (Blueprint, request, current_app, session, url_for, redirect,
                   render_template, g, flash, abort)
from flask_babel import gettext

from db import db_session, Source, SourceStar, Submission
from journalist_app.decorators import login_required
from journalist_app.utils import (validate_user, bulk_delete, download,
                                  confirm_bulk_delete, get_source)


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
                return redirect(url_for('main.index'))

        return render_template("login.html")

    @view.route('/logout')
    def logout():
        session.pop('uid', None)
        session.pop('expires', None)
        return redirect(url_for('main.index'))

    @view.route('/')
    @login_required
    def index():
        unstarred = []
        starred = []

        # Long SQLAlchemy statements look best when formatted according to
        # the Pocoo style guide, IMHO:
        # http://www.pocoo.org/internal/styleguide/
        sources = Source.query.filter_by(pending=False) \
                              .order_by(Source.last_updated.desc()) \
                              .all()
        for source in sources:
            star = SourceStar.query.filter_by(source_id=source.id).first()
            if star and star.starred:
                starred.append(source)
            else:
                unstarred.append(source)
            source.num_unread = len(
                Submission.query.filter_by(source_id=source.id,
                                           downloaded=False).all())

        return render_template('index.html',
                               unstarred=unstarred,
                               starred=starred)

    @view.route('/flag', methods=('POST',))
    @login_required
    def flag():
        g.source.flagged = True
        db_session.commit()
        return render_template('flag.html', filesystem_id=g.filesystem_id,
                               codename=g.source.journalist_designation)

    @view.route('/bulk', methods=('POST',))
    @login_required
    def bulk():
        action = request.form['action']

        doc_names_selected = request.form.getlist('doc_names_selected')
        selected_docs = [doc for doc in g.source.collection
                         if doc.filename in doc_names_selected]
        if selected_docs == []:
            if action == 'download':
                flash(gettext("No collections selected for download."),
                      "error")
            elif action in ('delete', 'confirm_delete'):
                flash(gettext("No collections selected for deletion."),
                      "error")
            return redirect(url_for('col', filesystem_id=g.filesystem_id))

        if action == 'download':
            source = get_source(g.filesystem_id)
            return download(source.journalist_filename, selected_docs)
        elif action == 'delete':
            return bulk_delete(g.filesystem_id, selected_docs)
        elif action == 'confirm_delete':
            return confirm_bulk_delete(g.filesystem_id, selected_docs)
        else:
            abort(400)

    return view
