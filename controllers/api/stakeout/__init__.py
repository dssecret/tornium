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

from flask import jsonify, request

from controllers.api.decorators import *
from database import session_local
from models.factionstakeoutmodel import FactionStakeoutModel
from models.keymodel import KeyModel
from models.servermodel import ServerModel
from models.stakeout import Stakeout
from models.user import User
from models.userstakeoutmodel import UserStakeoutModel
from redisdb import get_redis
import utils


@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:stakeouts', 'guilds:admin'})
def create_stakeout(stype, *args, **kwargs):
    session = session_local()
    data = json.loads(request.get_data().decode('utf-8'))
    client = redisdb.get_redis()

    guildid = data.get('guildid')
    tid = data.get('tid')
    keys = data.get('keys')
    name = data.get('name')
    category = data.get('category')

    if guildid is None:
        return jsonify({
            'code': 0,
            'name': 'UnknownGuild',
            'message': 'Server failed to fulfill the request. There was no guild ID provided but a guild ID was '
                       'required.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    elif tid is None:
        return jsonify({
            'code': 0,
            'name': 'UnknownID',
            'message': 'Server failed to fulfill the request. There was no Torn ID provided but a Torn ID was '
                       'required.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    guildid = int(guildid)
    tid = int(tid)

    if stype not in ['faction', 'user']:
        return jsonify({
            'code': 0,
            'name': 'InvalidStakeoutType',
            'message': 'Server failed to create the stakeout. The provided stakeout type did not match a known '
                       'stakeout type.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    elif str(guildid) not in User(session.query(KeyModel).filter_by(key=kwargs['key']).first().ownertid).servers:
        return jsonify({
            'code': 0,
            'name': 'UnknownGuild',
            'message': 'Server failed to fulfill the request. The provided guild ID did not match a guild that the '
                       'owner of the provided Tornium key was marked as an administrator in.'
        }), 403, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    elif stype == 'user' and session.query(UserStakeoutModel).filter_by(tid=tid).first() is not None and str(guildid) \
            in json.loads(session.query(UserStakeoutModel).filter_by(tid=tid).first().guilds):
        return jsonify({
            'code': 0,
            'name': 'StakeoutAlreadyExists',
            'message': 'Server failed to fulfill the request. The provided user ID is already being staked'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    elif stype == 'faction' and session.query(FactionStakeoutModel).filter_by(tid=tid).first() is not None and \
            str(guildid) in json.loads(session.query(FactionStakeoutModel).filter_by(tid=tid).first().guilds):
        return jsonify({
            'code': 0,
            'name': 'StakeoutAlreadyExists',
            'message': 'Server failed to fulfill the request. The provided faction ID is already being staked'
        }), 400, {
                   'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
                   'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
                   'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
               }
    elif stype == 'user' and keys is not None and not set(keys) & {'level', 'status', 'flyingstatus', 'online',
                                                                   'offline'}:
        return jsonify({
            'code': 0,
            'name': 'InvalidStakeoutKey',
            'message': 'Server failed to fulfill the request. The provided array of stakeout keys included a '
                       'stakeout key that was invalid for the provided stakeout type..'
        }), 403, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    elif stype == 'faction' and keys is not None and not set(keys) & {'territory', 'members', 'memberstatus',
                                                                      'memberactivity', 'armory', 'assault',
                                                                      'armorydeposit'}:
        return jsonify({
            'code': 0,
            'name': 'InvalidStakeoutKey',
            'message': 'Server failed to fulfill the request. The provided array of stakeout keys included a '
                       'stakeout key that was invalid for the provided stakeout type..'
        }), 403, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    stakeout = Stakeout(
        tid=tid,
        guild=guildid,
        user=True if stype == 'user' else False,
        key=kwargs['user'].key
    )
    guild = session.query(ServerModel).filter_by(sid=guildid).first()

    if stype == 'user':
        stakeouts = json.loads(guild.userstakeouts)
        stakeouts.append(tid)
        guild.userstakeouts = json.dumps(list(set(stakeouts)))
        session.flush()
    elif stype == 'faction':
        stakeouts = json.loads(guild.factionstakeouts)
        stakeouts.append(tid)
        guild.factionstakeouts = json.dumps(list(set(stakeouts)))
        session.flush()

    payload = {
        'name': f'{stype}-{stakeout.data["name"]}' if name is None else name,
        'type': 0,
        'topic': f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                 f'[{stakeout.data["player_id"] if stype == "user" else stakeout.data["ID"]}] by the Tornium bot.',
        'parent_id': json.loads(guild.stakeoutconfig)['category'] if category is None else category
    }

    channel = utils.tasks.discordpost(f'guilds/{guildid}/channels', payload=payload)
    channel = channel(blocking=True)

    stakeout.guilds[str(guildid)]['channel'] = int(channel['id'])
    if stype == 'user':
        db_stakeout = session.query(UserStakeoutModel).filter_by(tid=tid).first()
        message_payload = {
            'embeds': [
                {
                    'title': 'User Stakeout Creation',
                    'description': f'A stakeout of user {stakeout.data["name"]} has been created in '
                                   f'{guild.name}. This stakeout can be setup or removed in the '
                                   f'[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{guild.sid}) by a '
                                   f'server administrator.',
                    'timestamp': datetime.datetime.utcnow().isoformat()
                }
            ]
        }
    elif stype == 'faction':
        db_stakeout = session.query(FactionStakeoutModel).filter_by(tid=tid).first()
        message_payload = {
            'embeds': [
                {
                    'title': 'Faction Stakeout Creation',
                    'description': f'A stakeout of faction {stakeout.data["name"]} has been created in '
                                   f'{guild.name}. This stakeout can be setup or removed in the '
                                   f'[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{guild.sid}) by a '
                                   f'server administrator.',
                    'timestamp': datetime.datetime.utcnow().isoformat()
                }
            ]
        }

    db_stakeout.guilds = json.dumps(stakeout.guilds)
    session.flush()
    utils.tasks.discordpost(f'channels/{channel["id"]}/messages', payload=message_payload)()

    return jsonify({
        'id': tid,
        'type': stype,
        'config': json.loads(db_stakeout.guilds)[str(guildid)],
        'data': stakeout.data,
        'last_update': stakeout.last_update
    }), 200, {
        'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
        'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
        'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
    }
