from datetime import datetime, timedelta
from functools import wraps
import json
from werkzeug.exceptions import default_exceptions  # type: ignore

from flask import abort, Blueprint, current_app, jsonify, request, send_file

from db import db
from journalist_app import utils
from models import (Journalist, Reply, Source, Submission,
                    LoginThrottledException, InvalidUsernameException,
                    BadTokenException, WrongPasswordException)
from store import NotEncrypted


TOKEN_EXPIRATION_MINS = 60 * 8


def get_user_object(request):
    """Helper function to use in token_required views that need a user
    object
    """
    auth_token = request.headers.get('Authorization').split(" ")[1]
    user = Journalist.validate_api_token_and_get_user(auth_token)
    return user


def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers['Authorization']
        except KeyError:
            return abort(403, 'API token not found in Authorization header.')

        if auth_header:
            auth_token = auth_header.split(" ")[1]
        else:
            auth_token = ''
        if not Journalist.validate_api_token_and_get_user(auth_token):
            return abort(403, 'API token is invalid or expired.')
        return f(*args, **kwargs)
    return decorated_function


def get_or_404(model, object_id, column=''):
    if column:
        result = model.query.filter(column == object_id).one_or_none()
    else:
        result = model.query.get(object_id)
    if result is None:
        abort(404)
    return result


def make_blueprint(config):
    api = Blueprint('api', __name__)

    @api.route('/')
    def get_endpoints():
        endpoints = {'sources_url': '/api/v1/sources',
                     'current_user_url': '/api/v1/user',
                     'submissions_url': '/api/v1/submissions',
                     'auth_token_url': '/api/v1/token'}
        return jsonify(endpoints), 200

    @api.route('/token', methods=['POST'])
    def get_token():
        creds = json.loads(request.data)

        username = creds.get('username', None)
        passphrase = creds.get('passphrase', None)
        one_time_code = creds.get('one_time_code', None)

        if username is None:
            return abort(400, 'username field is missing')
        if passphrase is None:
            return abort(400, 'passphrase field is missing')
        if one_time_code is None:
            return abort(400, 'one_time_code field is missing')

        try:
            journalist = Journalist.login(username, passphrase, one_time_code)
            token_expiry = datetime.now() + timedelta(
                seconds=TOKEN_EXPIRATION_MINS * 60)
            response = jsonify({'token': journalist.generate_api_token(
                 expiration=TOKEN_EXPIRATION_MINS * 60),
                 'expiration': token_expiry.isoformat()})

            # Update access metadata
            journalist.last_access = datetime.utcnow()
            db.session.add(journalist)
            db.session.commit()

            return response, 200
        except (LoginThrottledException, InvalidUsernameException,
                BadTokenException, WrongPasswordException):
            return abort(403, 'Token authentication failed.')

    @api.route('/sources', methods=['GET'])
    @token_required
    def get_all_sources():
        sources = Source.query.all()
        return jsonify(
            {'sources': [source.to_json() for source in sources]}), 200

    @api.route('/sources/<filesystem_id>', methods=['GET', 'DELETE'])
    @token_required
    def single_source(filesystem_id):
        if request.method == 'GET':
            source = get_or_404(Source, filesystem_id,
                                column=Source.filesystem_id)
            return jsonify(source.to_json()), 200
        elif request.method == 'DELETE':
            source = get_or_404(Source, filesystem_id,
                                column=Source.filesystem_id)
            utils.delete_collection(source.filesystem_id)
            return jsonify({'message': 'Source and submissions deleted'}), 200

    @api.route('/sources/<filesystem_id>/add_star', methods=['POST'])
    @token_required
    def add_star(filesystem_id):
        source = get_or_404(Source, filesystem_id,
                            column=Source.filesystem_id)
        utils.make_star_true(source.filesystem_id)
        db.session.commit()
        return jsonify({'message': 'Star added'}), 201

    @api.route('/sources/<filesystem_id>/remove_star', methods=['DELETE'])
    @token_required
    def remove_star(filesystem_id):
        source = get_or_404(Source, filesystem_id,
                            column=Source.filesystem_id)
        utils.make_star_false(source.filesystem_id)
        db.session.commit()
        return jsonify({'message': 'Star removed'}), 200

    @api.route('/sources/<filesystem_id>/flag', methods=['POST'])
    @token_required
    def flag(filesystem_id):
        source = get_or_404(Source, filesystem_id,
                            column=Source.filesystem_id)
        source.flagged = True
        db.session.commit()
        return jsonify({'message': 'Source flagged for reply'}), 200

    @api.route('/sources/<filesystem_id>/submissions', methods=['GET'])
    @token_required
    def all_source_submissions(filesystem_id):
        source = get_or_404(Source, filesystem_id,
                            column=Source.filesystem_id)
        return jsonify(
            {'submissions': [submission.to_json() for
                             submission in source.submissions]}), 200

    @api.route('/sources/<filesystem_id>/submissions/<int:submission_id>/download',  # noqa
               methods=['GET'])
    @token_required
    def download_submission(filesystem_id, submission_id):
        source = get_or_404(Source, filesystem_id,
                            column=Source.filesystem_id)
        submission = get_or_404(Submission, submission_id)

        # Mark as downloaded
        submission.downloaded = True
        db.session.commit()

        return send_file(current_app.storage.path(source.filesystem_id,
                                                  submission.filename),
                         mimetype="application/pgp-encrypted",
                         as_attachment=True)

    @api.route('/sources/<filesystem_id>/submissions/<int:submission_id>',
               methods=['GET', 'DELETE'])
    @token_required
    def single_submission(filesystem_id, submission_id):
        if request.method == 'GET':
            submission = get_or_404(Submission, submission_id)
            return jsonify(submission.to_json()), 200
        elif request.method == 'DELETE':
            submission = get_or_404(Submission, submission_id)
            source = get_or_404(Source, filesystem_id,
                                column=Source.filesystem_id)
            utils.delete_file(source.filesystem_id, submission.filename,
                              submission)
            return jsonify({'message': 'Submission deleted'}), 200

    @api.route('/sources/<filesystem_id>/reply', methods=['POST'])
    @token_required
    def post_reply(filesystem_id):
        source = get_or_404(Source, filesystem_id,
                            column=Source.filesystem_id)
        if request.json is None:
            abort(400, 'please send requests in valid JSON')

        if 'reply' not in request.json:
            abort(400, 'reply not found in request body')

        user = get_user_object(request)

        data = json.loads(request.data)
        if not data['reply']:
            abort(400, 'reply should not be empty')

        source.interaction_count += 1
        try:
            filename = current_app.storage.save_pre_encrypted_reply(
                source.filesystem_id,
                source.interaction_count,
                source.journalist_filename,
                data['reply'])
        except NotEncrypted:
            return jsonify(
                {'message': 'You must encrypt replies client side'}), 400

        reply = Reply(user, source,
                      current_app.storage.path(source.filesystem_id, filename))
        db.session.add(reply)
        db.session.add(source)
        db.session.commit()
        return jsonify({'message': 'Your reply has been stored'}), 201

    @api.route('/submissions', methods=['GET'])
    @token_required
    def get_all_submissions():
        submissions = Submission.query.all()
        return jsonify({'submissions': [submission.to_json() for
                                        submission in submissions]}), 200

    @api.route('/user', methods=['GET'])
    @token_required
    def get_current_user():
        user = get_user_object(request)
        return jsonify(user.to_json()), 200

    def _handle_http_exception(error):
        # Workaround for no blueprint-level 404/5 error handlers, see:
        # https://github.com/pallets/flask/issues/503#issuecomment-71383286
        response = jsonify({'error': error.name,
                           'message': error.description})

        return response, error.code

    for code in default_exceptions:
        api.errorhandler(code)(_handle_http_exception)

    return api
