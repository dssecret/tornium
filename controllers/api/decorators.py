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
import datetime
from functools import wraps, partial

from flask import jsonify, request

from models.keymodel import KeyModel
from models.usermodel import UserModel
import redisdb
import utils


def ratelimit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        client = redisdb.get_redis()
        key = kwargs['user'].tid
        limit = 250 if kwargs['user'].pro else 150

        if client.setnx(key, limit):
            client.expire(key, 60 - datetime.datetime.utcnow().second)

        value = client.get(key)

        if client.ttl(key) < 0:
            client.expire(key, 1)

        if value and int(value) > 0:
            client.decrby(key, 1)
        else:
            return jsonify({
                'code': 4000,
                'name': 'Too Many Requests',
                'message': 'Server failed to respond to request. Too many requests were received.'
            }), 429, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
                'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
            }

        return func(*args, **kwargs)

    return wrapper


def requires_scopes(func=None, scopes=None):
    if not func:
        return partial(requires_scopes, scopes=scopes)

    @wraps(func)
    def wrapper(*args, **kwargs):
        client = redisdb.get_redis()

        if kwargs['keytype'] == 'Tornium' and not set(utils.first(KeyModel.objects(key=kwargs['key'])).scopes) & scopes:
            return jsonify({
                'code': 4004,
                'name': 'InsufficientPermissions',
                'message': 'Server failed to fulfill the request. The scope of the Tornium key provided was not '
                           'sufficient for the request.'
            }), 403, {
                'X-RateLimit-Limit': 250 if kwargs['user'].pro else 150,
                'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
                'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
            }

        return func(*args, **kwargs)

    return wrapper


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

        user = utils.first(UserModel.objects(key=authorization))

        if user is None:
            return jsonify({
                'code': 4001,
                'name': 'InvalidAuthenticationInformation',
                'message': 'Server failed to authenticate the request. The provided authentication code was invalid.'
            }), 401

        kwargs['user'] = user
        kwargs['keytype'] = 'Torn'
        kwargs['key'] = authorization

        return func(*args, **kwargs)

    return wrapper


def tornium_key_required(func):
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

        key = utils.first(KeyModel.objects(key=authorization))

        if key is None:
            return jsonify({
                'code': 4001,
                'name': 'InvalidAuthenticationInformation',
                'message': 'Server failed to authenticate the request. The provided authentication code was invalid.'
            }), 401

        kwargs['user'] = utils.first(UserModel.objects(tid=key.ownertid))
        kwargs['keytype'] = 'Tornium'
        kwargs['key'] = authorization

        return func(*args, **kwargs)

    return wrapper


def key_required(func):
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

        key = utils.first(KeyModel.objects(key=authorization))
        user = utils.first(UserModel.objects(key=authorization))

        if user is not None:
            kwargs['user'] = user
            kwargs['keytype'] = 'Torn'
            kwargs['key'] = authorization
        elif key is not None:
            kwargs['user'] = utils.first(UserModel.objects(tid=key.ownertid))
            kwargs['keytype'] = 'Tornium'
            kwargs['key'] = authorization
        else:
            return jsonify({
                'code': 4001,
                'name': 'InvalidAuthenticationInformation',
                'message': 'Server failed to authenticate the request. The provided authentication code was invalid.'
            }), 401

        return func(*args, **kwargs)

    return wrapper
