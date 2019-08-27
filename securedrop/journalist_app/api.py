import json

from datetime import datetime, timedelta
from flask import abort, Blueprint, current_app, jsonify, request
from functools import wraps
from sqlalchemy.exc import IntegrityError
from os import path
from uuid import UUID
from werkzeug.exceptions import default_exceptions  # type: ignore

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
            split = auth_header.split(" ")
            if len(split) != 2 or split[0] != 'Token':
                abort(403, 'Malformed authorization header.')
            auth_token = split[1]
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
                     'replies_url': '/api/v1/replies',
                     'auth_token_url': '/api/v1/token'}
        return jsonify(endpoints), 200

    # Before every post, we validate the payload before processing the request
    @api.before_request
    def validate_data():
        if request.method == 'POST':
            # flag, star, and logout can have empty payloads
            if not request.data:
                dataless_endpoints = [
                    'add_star',
                    'remove_star',
                    'flag',
                    'logout',
                ]
                for endpoint in dataless_endpoints:
                    if request.endpoint == 'api.' + endpoint:
                        return
                return abort(400, 'malformed request')
            # other requests must have valid JSON payload
            else:
                try:
                    json.loads(request.data.decode('utf-8'))
                except (ValueError):
                    return abort(400, 'malformed request')

    @api.route('/token', methods=['POST'])
    def get_token():
        creds = json.loads(request.data.decode('utf-8'))

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
            token_expiry = datetime.utcnow() + timedelta(
                seconds=TOKEN_EXPIRATION_MINS * 60)

            response = jsonify({
                'token': journalist.generate_api_token(expiration=TOKEN_EXPIRATION_MINS * 60),
                'expiration': token_expiry.isoformat() + 'Z',
                'journalist_uuid': journalist.uuid,
            })

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
        sources = Source.query.filter_by(pending=False).all()
        return jsonify(
            {'sources': [source.to_json() for source in sources]}), 200

    @api.route('/sources/<source_uuid>', methods=['GET', 'DELETE'])
    @token_required
    def single_source(source_uuid):
        if request.method == 'GET':
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            return jsonify(source.to_json()), 200
        elif request.method == 'DELETE':
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            utils.delete_collection(source.filesystem_id)
            return jsonify({'message': 'Source and submissions deleted'}), 200

    @api.route('/sources/<source_uuid>/add_star', methods=['POST'])
    @token_required
    def add_star(source_uuid):
        source = get_or_404(Source, source_uuid, column=Source.uuid)
        utils.make_star_true(source.filesystem_id)
        db.session.commit()
        return jsonify({'message': 'Star added'}), 201

    @api.route('/sources/<source_uuid>/remove_star', methods=['DELETE'])
    @token_required
    def remove_star(source_uuid):
        source = get_or_404(Source, source_uuid, column=Source.uuid)
        utils.make_star_false(source.filesystem_id)
        db.session.commit()
        return jsonify({'message': 'Star removed'}), 200

    @api.route('/sources/<source_uuid>/flag', methods=['POST'])
    @token_required
    def flag(source_uuid):
        source = get_or_404(Source, source_uuid,
                            column=Source.uuid)
        source.flagged = True
        db.session.commit()
        return jsonify({'message': 'Source flagged for reply'}), 200

    @api.route('/sources/<source_uuid>/submissions', methods=['GET'])
    @token_required
    def all_source_submissions(source_uuid):
        source = get_or_404(Source, source_uuid, column=Source.uuid)
        return jsonify(
            {'submissions': [submission.to_json() for
                             submission in source.submissions]}), 200

    @api.route('/sources/<source_uuid>/submissions/<submission_uuid>/download',  # noqa
               methods=['GET'])
    @token_required
    def download_submission(source_uuid, submission_uuid):
        get_or_404(Source, source_uuid, column=Source.uuid)
        submission = get_or_404(Submission, submission_uuid,
                                column=Submission.uuid)

        # Mark as downloaded
        submission.downloaded = True
        db.session.commit()

        return utils.serve_file_with_etag(submission)

    @api.route('/sources/<source_uuid>/replies/<reply_uuid>/download',
               methods=['GET'])
    @token_required
    def download_reply(source_uuid, reply_uuid):
        get_or_404(Source, source_uuid, column=Source.uuid)
        reply = get_or_404(Reply, reply_uuid, column=Reply.uuid)

        return utils.serve_file_with_etag(reply)

    @api.route('/sources/<source_uuid>/submissions/<submission_uuid>',
               methods=['GET', 'DELETE'])
    @token_required
    def single_submission(source_uuid, submission_uuid):
        if request.method == 'GET':
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            submission = get_or_404(Submission, submission_uuid,
                                    column=Submission.uuid)
            return jsonify(submission.to_json()), 200
        elif request.method == 'DELETE':
            submission = get_or_404(Submission, submission_uuid,
                                    column=Submission.uuid)
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            utils.delete_file(source.filesystem_id, submission.filename,
                              submission)
            return jsonify({'message': 'Submission deleted'}), 200

    @api.route('/sources/<source_uuid>/replies', methods=['GET', 'POST'])
    @token_required
    def all_source_replies(source_uuid):
        if request.method == 'GET':
            source = get_or_404(Source, source_uuid, column=Source.uuid)
            return jsonify(
                {'replies': [reply.to_json() for
                             reply in source.replies]}), 200
        elif request.method == 'POST':
            source = get_or_404(Source, source_uuid,
                                column=Source.uuid)
            if request.json is None:
                abort(400, 'please send requests in valid JSON')

            if 'reply' not in request.json:
                abort(400, 'reply not found in request body')

            user = get_user_object(request)

            data = request.json
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

            # issue #3918
            filename = path.basename(filename)

            reply = Reply(user, source, filename)

            reply_uuid = data.get('uuid', None)
            if reply_uuid is not None:
                # check that is is parseable
                try:
                    UUID(reply_uuid)
                except ValueError:
                    abort(400, "'uuid' was not a valid UUID")
                reply.uuid = reply_uuid

            try:
                db.session.add(reply)
                db.session.add(source)
                db.session.commit()
            except IntegrityError as e:
                db.session.rollback()
                if 'UNIQUE constraint failed: replies.uuid' in str(e):
                    abort(409, 'That UUID is already in use.')
                else:
                    raise e

            return jsonify({'message': 'Your reply has been stored',
                            'uuid': reply.uuid,
                            'filename': reply.filename}), 201

    @api.route('/sources/<source_uuid>/replies/<reply_uuid>',
               methods=['GET', 'DELETE'])
    @token_required
    def single_reply(source_uuid, reply_uuid):
        source = get_or_404(Source, source_uuid, column=Source.uuid)
        reply = get_or_404(Reply, reply_uuid, column=Reply.uuid)
        if request.method == 'GET':
            return jsonify(reply.to_json()), 200
        elif request.method == 'DELETE':
            utils.delete_file(source.filesystem_id, reply.filename,
                              reply)
            return jsonify({'message': 'Reply deleted'}), 200

    @api.route('/submissions', methods=['GET'])
    @token_required
    def get_all_submissions():
        submissions = Submission.query.all()
        return jsonify({'submissions': [submission.to_json() for
                                        submission in submissions]}), 200

    @api.route('/replies', methods=['GET'])
    @token_required
    def get_all_replies():
        replies = Reply.query.all()
        return jsonify(
            {'replies': [reply.to_json() for reply in replies]}), 200

    @api.route('/user', methods=['GET'])
    @token_required
    def get_current_user():
        user = get_user_object(request)
        return jsonify(user.to_json()), 200

    @api.route('/logout', methods=['POST'])
    @token_required
    def logout():
        user = get_user_object(request)
        auth_token = request.headers.get('Authorization').split(" ")[1]
        utils.revoke_token(user, auth_token)
        return jsonify({'message': 'Your token has been revoked.'}), 200

    def _handle_api_http_exception(error):
        # Workaround for no blueprint-level 404/5 error handlers, see:
        # https://github.com/pallets/flask/issues/503#issuecomment-71383286
        response = jsonify({'error': error.name,
                           'message': error.description})

        return response, error.code

    for code in default_exceptions:
        api.errorhandler(code)(_handle_api_http_exception)

    return api
