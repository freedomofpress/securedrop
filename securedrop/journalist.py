# -*- coding: utf-8 -*-

from flask import (send_file,
                   abort)
from sqlalchemy.orm.exc import NoResultFound

import config
import store
from db import db_session, Submission

from journalist_app import create_app
from journalist_app.decorators import login_required

app = create_app(config)


@app.route('/col/<filesystem_id>/<fn>')
@login_required
def download_single_submission(filesystem_id, fn):
    """Sends a client the contents of a single submission."""
    if '..' in fn or fn.startswith('/'):
        abort(404)

    try:
        Submission.query.filter(
            Submission.filename == fn).one().downloaded = True
        db_session.commit()
    except NoResultFound as e:
        app.logger.error("Could not mark " + fn + " as downloaded: %s" % (e,))

    return send_file(store.path(filesystem_id, fn),
                     mimetype="application/pgp-encrypted")


if __name__ == "__main__":  # pragma: no cover
    debug = getattr(config, 'env', 'prod') != 'prod'
    app.run(debug=debug, host='0.0.0.0', port=8081)
