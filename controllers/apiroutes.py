# This file is part of Tornium.
#
# Tornium is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tornium is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Tornium.  If not, see <https://www.gnu.org/licenses/>.

import base64
from functools import wraps
import json
import secrets

from flask import Blueprint, render_template, request, jsonify

from database import session_local
from models.user import User
from models.usermodel import UserModel
import utils

mod = Blueprint('apiroutes', __name__)


def torn_key_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.headers.get('Authorization') is None:
            return jsonify({
                'code': 4001,
                'name': 'NoAuthenticationInformation',
                'message': 'Server failed to authenticate the request. No authentication code was provided.'
            }), 401
        elif request.headers.get('Authorization').split(' ')[0] != 'Basic':
            return jsonify({
                'code': 4003,
                'name': 'InvalidAuthenticationType',
                'message': 'Server failed to authenticate the request. The provided authentication type was not '
                           '"Basic" and therefore invalid.'
            }), 401

        authorization = str(base64.b64decode(request.headers.get('Authorization').split(' ')[1]), 'utf-8').split(':')[0]

        if authorization == '':
            return jsonify({
                'code': 4001,
                'name': 'NoAuthenticationInformation',
                'message': 'Server failed to authenticate the request. No authentication code was provided.'
            }), 401

        session = session_local()
        user = session.query(UserModel).filter_by(key=authorization).first()

        if user is None:
            return jsonify({
                'code': 4001,
                'name': 'InvalidAuthenticationInformation',
                'message': 'Server failed to authenticate the request. The provided authentication code was invalid.'
            }), 401

        kwargs['user'] = user

        return func(*args, **kwargs)

    return wrapper


@mod.route('/api')
def index():
    return render_template('api/index.html')


@mod.route('/api/test')
@torn_key_required
def test(*args, **kwargs):
    return jsonify({
        'code': 1,
        'name': 'OK',
        'message': 'Server request was successful. Authentication was successful.'
    }), 200


@mod.route('/api/keys', methods=['POST'])
@torn_key_required
def create_key(*args, **kwargs):
    user = User(kwargs['user'].tid)
    session = session_local()
    user_db = session.query(UserModel).filter_by(tid=user.tid).first()
    data = json.loads(request.get_data().decode('utf-8'))

    scopes = data.get('scopes')
    expires = data.get('expires')

    if expires <= utils.now():
        return jsonify({
            'code': 0,
            'name': 'InvalidExpiryTimestamp',
            'message': 'Server failed to create the key. The provided timestamp was greater than the current '
                       'timestamp on the server.'
        }), 400
    if scopes is None:
        scopes = []

    for scope in scopes:
        if scope not in []:
            return jsonify({
                'code': 0,
                'name': 'InvalidScope',
                'message': 'Server failed to create the key. The provided array of scopes included an invalid scope.'
            }), 400

    key = base64.b64encode(f'{user.tid}:{secrets.token_urlsafe(32)}'.encode('utf-8')).decode('utf-8')
    user.keys[key] = {
        'scopes': json.loads(scopes),
        'expires': expires if expires is not None else utils.now() + 2592000  # One month from now
    }
    user_db.keys = json.dumps(user.keys)

