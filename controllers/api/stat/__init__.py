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

import random

from mongoengine.queryset.visitor import Q

from controllers.api.decorators import *
from models.statmodel import StatModel


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'read:stats'})
def generate_chain_list(*args, **kwargs):
    # curl -H "Authorization: Basic " localhost:8000/api/stat
    client = redisdb.get_redis()
    defender_stats = request.args.get('dstats') if request.args.get('dstats') is not None else 0.75
    variance = request.args.get('variance') if request.args.get('variance') is not None else 0.1

    if kwargs['user'].battlescore == 0:
        return jsonify({
            'code': 0,
            'name': 'General Error',
            'message': 'Server failed the fulfill the request. There was no battle stats scored for the user but the '
                       'battle stats are required.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    stat_entries = StatModel.objects((Q(globalstat=1) |
                                      Q(addedfactiontid=kwargs['user'].factionid)) &
                                     Q(battlescore__gte=(kwargs['user']['battlescore'] * (defender_stats - variance))) &
                                     Q(battlescore__lte=(kwargs['user']['battlescore'] * (defender_stats + variance))) &
                                     Q(timeadded__gte=(utils.now() - 2678400)))  # Thirty one days
    stat_entries = list(stat_entries.all().values_list('statid'))
    random.shuffle(stat_entries)
    stat_entries = stat_entries[:10]
    jsonified_stat_entires = []

    for stat_entry in stat_entries:
        stat = StatModel.objects(statid=stat_entry).first()
        jsonified_stat_entires.append({
            'statid': stat.statid,
            'tid': stat.tid,
            'battlescore': stat.battlescore,
            'timeadded': stat.addedid
        })

    return jsonify({
        'defender_stats': defender_stats,
        'variance': variance,
        'data': jsonified_stat_entires
    }), 200, {
        'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
        'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
        'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'read:stats'})
def get_user(tid, *args, **kwargs):
    client = redisdb.get_redis()
    limit = request.args.get('limit') if request.args.get('limit') is not None else 10

    stat_entries = StatModel.objects((Q(globalstat=1) |
                                      Q(addedfactiontid=kwargs['user'].factionid)) &
                                     Q(tid=tid)).order_by('-statid')[:limit].all()
    jsonified_stat_entries = []

    for stat_entry in stat_entries:
        jsonified_stat_entries.append({
            'statid': stat_entry.statid,
            'tid': stat_entry.tid,
            'battlescore': stat_entry.battlescore,
            'timeadded': stat_entry.addedid
        })

    return jsonify({
        'limit': limit,
        'data': jsonified_stat_entries
    }), 200, {
        'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
        'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
        'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }
