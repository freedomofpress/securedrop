from functools import wraps
from itsdangerous import TimedJSONWebSignatureSerializer
import json

from flask import g, jsonify, request, current_app, url_for, abort, send_file
from flask import Blueprint

import config
import crypto_util
from db import Source, Submission, db_session, Journalist, Reply, SourceStar
import store
import worker

api = Blueprint('api', __name__)



def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
        except:
            return forbidden('API token not found in Authorization header.')

        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        if not Journalist.verify_api_token(auth_token):
            return forbidden('API token is invalid or expired.')
        return f(*args, **kwargs)
    return decorated_function

# Errors

def forbidden(message):
    abort(403, message)


def get_or_404(model, object_id):
    rv = model.query.get(object_id)
    if rv is None:
        abort(404)
    return rv

# Authentication

@api.route('/token/', methods=['POST'])
def get_token():
    creds = json.loads(request.data)
    username = creds['username']
    password = creds['password']
    one_time_code = creds['one_time_code']
    try:
        journalist = Journalist.login(username, password, one_time_code)
        return jsonify({'token': journalist.generate_api_token(
             expiration=1800), 'expiration': 1800}), 200
    except:
        return forbidden('Token authentication failed.')

# Root endpoint

@api.route('/')
def get_endpoints():
    endpoints = {'sources_url': '/api/v1/sources/',
                 'current_user_url': '/api/v1/user/',
                 'submissions_url': '/api/v1/submissions/',
                 'auth_token_url': '/api/v1/token/'}
    return jsonify(endpoints), 200

# Sources

@api.route('/sources/', methods=['GET'])
@token_required
def get_all_sources():
    sources = Source.query.all()
    return jsonify({'sources': [source.to_json() for source in sources]}), 200


@api.route('/sources/<int:source_id>/', methods=['GET'])
@token_required
def single_source(source_id):
    source = get_or_404(Source, source_id)
    return jsonify(source.to_json()), 200


@api.route('/sources/<int:source_id>/add_star/', methods=['POST'])
@token_required
def add_star(source_id):
    source = get_or_404(Source, source_id)

    if source.star:
        source.star.starred = True
    else:
        source_star = SourceStar(source)
        db_session.add(source_star)
        db_session.commit()

    return jsonify({'message': 'Star added'}), 201


@api.route('/sources/<int:source_id>/remove_star/', methods=['DELETE'])
@token_required
def remove_star(source_id):
    source = get_or_404(Source, source_id)

    if not source.star:
        source_star = SourceStar(source)
        db_session.add(source_star)
        db_session.commit()
    source.star.starred = False

    return jsonify({'message': 'Star removed'}), 200


@api.route('/sources/<int:source_id>/submissions/', methods=['GET', 'DELETE'])
@token_required
def all_source_submissions(source_id):

    if request.method == 'GET':
        source = get_or_404(Source, source_id)
        return jsonify({'submissions': [submission.to_json() for submission in source.submissions]}), 200

    elif request.method == 'DELETE':
        source = get_or_404(Source, source_id)
        job = worker.enqueue(store.delete_source_directory, source.filesystem_id)

        # Delete the source's reply keypair
        crypto_util.delete_reply_keypair(source.filesystem_id)

        # Delete their entry in the db
        db_session.delete(source)
        db_session.commit()
        return jsonify({'message': 'Source and submissions deleted'}), 200


@api.route('/sources/<int:source_id>/submissions/<int:submission_id>/download/',
           methods=['GET'])
@token_required
def download_submission(source_id, submission_id):
    source = get_or_404(Source, source_id)
    submission = get_or_404(Submission, submission_id)

    # Mark as downloaded
    submission.downloaded = True
    db_session.commit()

    return send_file(store.path(source.filesystem_id, submission.filename),
                     mimetype="application/pgp-encrypted",
                     as_attachment=True)


@api.route('/sources/<int:source_id>/submissions/<int:submission_id>/', methods=['GET', 'DELETE'])
@token_required
def single_submission(source_id, submission_id):

    if request.method == 'GET':
        submission = get_or_404(Submission, submission_id)
        return jsonify(submission.to_json()), 200

    elif request.method == 'DELETE':
        submission = get_or_404(Submission, submission_id)
        source = get_or_404(Source, source_id)
        submission_path = store.path(source.filesystem_id, submission.filename)
        worker.enqueue(store.secure_unlink, submission_path)
        db_session.delete(submission)
        db_session.commit()
        return jsonify({'message': 'Submission deleted'}), 200


@api.route('/sources/<int:source_id>/reply/', methods=['POST'])
@token_required
def post_reply(source_id):
    source = get_or_404(Source, source_id)

    # Get current user from token
    auth_token = request.headers.get('Authorization').split(" ")[1]
    user = Journalist.verify_api_token(auth_token)

    source.interaction_count += 1
    filename = "{0}-{1}-reply.gpg".format(source.interaction_count,
                                          source.journalist_filename)

    data = json.loads(request.data)
    # input validation on msg? (also not present in regular journalist code)
    crypto_util.encrypt(data['reply'],
                        [crypto_util.getkey(source.filesystem_id),
                        config.JOURNALIST_KEY],
                        output=store.path(source.filesystem_id, filename))
    reply = Reply(user, source, filename)
    db_session.add(reply)
    db_session.commit()
    return jsonify({'message': 'Your reply has been stored'}), 201


# Submissions
@api.route('/submissions/', methods=['GET'])
@token_required
def get_all_submissions():
    submissions = Submission.query.all()
    return jsonify({'submissions': [submission.to_json() for submission in submissions]}), 200


# Users
@api.route('/user/', methods=['GET'])
@token_required
def get_current_user():
    # Get current user from token
    auth_token = request.headers.get('Authorization').split(" ")[1]
    user = Journalist.verify_api_token(auth_token)
    return jsonify({'user': user.to_json()}), 200
