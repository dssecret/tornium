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
import json
import secrets
import time

from flask import Blueprint, render_template, request, jsonify

from database import session_local
from models.faction import Faction
from models.factionmodel import FactionModel
from models.factionstakeoutmodel import FactionStakeoutModel
from models.keymodel import KeyModel
from models.servermodel import ServerModel
from models.stakeout import Stakeout
from models.user import User
from models.usermodel import UserModel
from models.userstakeoutmodel import UserStakeoutModel
import redisdb
import utils

mod = Blueprint('apiroutes', __name__)


def ratelimit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        client = redisdb.get_redis()
        key = kwargs['user'].tid
        limit = 150

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
                'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
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
        session = session_local()
        client = redisdb.get_redis()

        if not set(json.loads(session.query(KeyModel).filter_by(key=kwargs['key']).first().scopes)) & scopes:
            return jsonify({
                'code': 4004,
                'name': 'InsufficientPermissions',
                'message': 'Server failed to fulfill the request. The scope of the Tornium key provided was not '
                           'sufficient for the request.'
            }), 403, {
                'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
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

        session = session_local()
        user = session.query(UserModel).filter_by(key=authorization).first()

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

        session = session_local()
        key = session.query(KeyModel).filter_by(key=authorization).first()

        if key is None:
            return jsonify({
                'code': 4001,
                'name': 'InvalidAuthenticationInformation',
                'message': 'Server failed to authenticate the request. The provided authentication code was invalid.'
            }), 401

        kwargs['user'] = session.query(UserModel).filter_by(tid=key.ownertid).first()
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

        session = session_local()
        key = session.query(KeyModel).filter_by(key=authorization).first()
        user = session.query(UserModel).filter_by(key=authorization).first()

        if user is not None:
            kwargs['user'] = user
            kwargs['keytype'] = 'Torn'
            kwargs['key'] = authorization
        elif key is not None:
            kwargs['user'] = session.query(UserModel).filter_by(tid=key.ownertid).first()
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


@mod.route('/api')
def index():
    return render_template('api/index.html')


@mod.route('/api/key')
@torn_key_required
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


@mod.route('/api/keys', methods=['POST'])
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
    })


@mod.route('/api/faction/banking', methods=['POST'])
@key_required
@ratelimit
@requires_scopes(scopes={'admin', 'write:banking', 'write:faction', 'faction:admin'})
def banking_request(*args, **kwargs):
    session = session_local()
    data = json.loads(request.get_data().decode('utf-8'))
    client = redisdb.get_redis()
    user = User(kwargs['user'].tid)

    amount_requested = data.get('amount_requested')

    if amount_requested is None:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. There was no amount requested provided but an amount '
                       'requested was required.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    user.refresh()

    if user.factiontid == 0:
        user.refresh(force=True)

        if user.factiontid == 0:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The API key\'s user is required to be in a Torn '
                           'faction.'
            }), 400, {
                'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
                'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
                'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
            }

    faction = Faction(user.factiontid, key=user.key)
    vault_config = faction.get_vault_config()
    config = faction.get_config()

    if vault_config.get('banking') == 0 or vault_config.get('banker') == 0 or config.get('vault') == 0:
        return jsonify({
            'code': 0,
            'name': 'GeneralError',
            'message': 'Server failed to fulfill the request. The user\'s faction\'s bot configuration needs to be '
                       'configured by faction AA members.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }

    vault_balances = utils.tasks.tornget(f'faction/?selections=donations', faction.rand_key())(blocking=True)

    if str(user.tid) in vault_balances['donations']:
        if amount_requested > vault_balances['donations'][str(user.tid)]['money_balance']:
            return jsonify({
                'code': 0,
                'name': 'GeneralError',
                'message': 'Server failed to fulfill the request. The amount requested was greater than the amount in '
                           'the user\'s faction vault balance.'
            }), 400, {
                'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
                'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
                'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
            }

        request_id = len(faction.withdrawals) + 1
        message_payload = {
            'content': f'<@&{vault_config["banker"]}>',
            'embeds': [
                {
                    'title': f'Vault Request #{request_id}',
                    'description': f'{user.name} [{user.tid}] is requesting {amount_requested} from the faction vault. '
                                   f'To fulfill this request, enter `?f {request_id}` in this channel.',
                    'timestamp': datetime.datetime.utcnow().isoformat()
                }
            ]
        }
        message = utils.tasks.discordpost(f'channels/{vault_config["withdrawal"]}/messages', payload=message_payload)
        message = message(blocking=True)

        faction.withdrawals.append({
            'id': request_id,
            "amount": amount_requested,
            'requester': user.tid,
            'fulfilled': False,
            'timerequested': time.ctime(),
            'fulfiller': 0,
            'timefulfilled': 0,
            'withdrawalmessage': message['id']
        })

        dbfaction = session.query(FactionModel).filter_by(tid=faction.tid).first()
        dbfaction.withdrawals = json.dumps(faction.withdrawals)
        session.flush()

        return jsonify({
            'id': request_id,
            'amount': amount_requested,
            'requester': user.tid,
            'timerequested': faction.withdrawals[request_id - 1]['timerequested'],
            'withdrawalmessage': message['id']
        }), 200, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }
    else:
        return jsonify({
            'code': 0,
            'name': 'UnknownFaction',
            'message': 'Server failed to fulfill the request. There was no faction stored with that faction ID.'
        }), 400, {
            'X-RateLimit-Limit': 150,  # TODO: Update based on per-user quota
            'X-RateLimit-Remaining': client.get(kwargs['user'].tid),
            'X-RateLimit-Reset': client.ttl(kwargs['user'].tid)
        }


@mod.route('/api/stakeouts/<string:stype>', methods=['POST'])
@tornium_key_required
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
            'name': 'UnkownID',
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
    elif stype == 'user' and keys is not None and not set(keys) & {'level', 'status', 'flyingstatus', 'online', 'offline'}:
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
    elif stype == 'faction' and keys is not None and not set(keys) & {'territory', 'members', 'memberstatus', 'memberactivity'}:
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
    elif stype == 'faction':
        db_stakeout = session.query(FactionStakeoutModel).filter_by(tid=tid).first()

    db_stakeout.guilds = json.dumps(stakeout.guilds)
    session.flush()

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
