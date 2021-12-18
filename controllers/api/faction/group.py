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

import json
import uuid

from controllers.api.decorators import *
from models.factiongroupmodel import FactionGroupModel
from models.user import User
import utils


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'faction:admin'})
def group_modify(*args, **kwargs):
    data = json.loads(request.get_data().decode('utf-8'))
    client = redisdb.get_redis()
    user = User(kwargs['user'].tid)
    group: FactionGroupModel = utils.first(FactionGroupModel.objects(tid=data.get('groupid')))

    if group is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The provided faction group ID was not a valid ID.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    elif user.factiontid != group.creator:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. THe provided faction group can not be modified. Only AA '
                       'users within the creating faction can modify the faction group.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    action = data.get('action')
    value = data.get('value')

    if action is None or action not in ['name', 'remove', 'invite']:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. There was no correct action provided but was required.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    elif value is None and action in ['name']:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. There was no correct value provided but was required.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    if action == 'name':
        group.name = value
        group.save()
    elif action == 'remove':
        if value == group.creator:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The group creator can not be removed from the group.'
            }), 400, {
                'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
                'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
                'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
            }

        group.members.remove(value)
        group.save()
    elif action == 'invite':
        group.invite = uuid.uuid4().hex
        group.save()

    return jsonify({
        'tid': group.tid,
        'name': group.name,
        'creator': group.creator,
        'members': group.members
    }), 200, {
        'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
        'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
        'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }
