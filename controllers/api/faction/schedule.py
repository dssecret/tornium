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
