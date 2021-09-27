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

from flask import jsonify

from controllers.api.decorators import *
from database import session_local
from models.keymodel import KeyModel
from redisdb import get_redis
import utils


@key_required
@ratelimit
def test_key(*args, **kwargs):
    client = redisdb.get_redis()

    return jsonify({
        'code': 1,
        'name': 'OK',
        'message': 'Server request was successful. Authentication was successful.'
    }), 200, {
        'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
        'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
        'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }


@torn_key_required
@ratelimit
def create_key(*args, **kwargs):
    user = User(kwargs['user'].tid)
    session = session_local()
    data = json.loads(request.get_data().decode('utf-8'))

    scopes = data.get('scopes')
    expires = data.get('expires')

    if expires is not None and expires <= utils.now():
        client = redisdb.get_redis()

        return jsonify({
            'code': 0,
            'name': 'InvalidExpiryTimestamp',
            'message': 'Server failed to create the key. The provided timestamp was greater than the current '
                       'timestamp on the server.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    if scopes is None:
        scopes = []

    for scope in scopes:
        if scope not in []:
            client = redisdb.get_redis()

            return jsonify({
                'code': 0,
                'name': 'InvalidScope',
                'message': 'Server failed to create the key. The provided array of scopes included an invalid scope.'
            }), 400, {
                'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
                'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
                'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
            }

    key = base64.b64encode(f'{user.tid}:{secrets.token_urlsafe(32)}'.encode('utf-8')).decode('utf-8')
    keydb = KeyModel(
        key=key,
        ownertid=user.tid,
        scopes=json.dumps(scopes)
    )
    session.add(keydb)
    session.flush()

    return jsonify({
        'key': key,
        'ownertid': user.tid,
        'scopes': scopes,
        'expires': expires
    }), 200, {
        'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
        'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
        'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }
