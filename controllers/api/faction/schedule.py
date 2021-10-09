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

import uuid

from controllers.api.decorators import *
from models.schedule import Schedule
from models.user import User


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def create_schedule(*args, **kwargs):
    client = redisdb.get_redis()
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
           'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
           'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
           'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    schedule = Schedule(uuid=uuid.uuid4().hex, factiontid=user.factiontid)

    return schedule.file, 200, {
       'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
       'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
       'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def delete_schedule(*args, **kwargs):
    client = redisdb.get_redis()
    data = json.loads(request.get_data().decode('utf-8'))
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    Schedule(uuid=data['uuid'], factiontid=user.factiontid).delete()

    return {
        'code': 0,
        'name': 'OK',
        'message': 'Server request was successful.'
    }, 200, {
        'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
        'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
        'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:faction', 'faction:admin'})
def add_chain_watcher(*args, **kwargs):
    client = redisdb.get_redis()
    data = json.loads(request.get_data().decode('utf-8'))
    user = User(kwargs['user'].tid)

    if not user.aa:
        return jsonify({
            'code': 4005,
            'name': 'InsufficientFactionPermissions',
            'message': 'Server failed to fulfill the request. The provided authentication code was not sufficient '
                       'for an AA level request.'
        }), 403, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    schedule = Schedule(uuid=data['uuid'], factiontid=user.factiontid)
    schedule.add_activity(tid=data['tid'], activity=None)
    schedule.set_weight(tid=data['tid'], weight=data['weight'])

    return schedule.file, 200, {
       'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
       'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
       'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }
