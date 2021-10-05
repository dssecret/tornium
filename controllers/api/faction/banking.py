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

import time

from flask import jsonify

from controllers.api.decorators import *
from database import session_local
from models.faction import Faction
from models.factionmodel import FactionModel
from models.user import User
from models.usermodel import UserModel
from redisdb import get_redis
import utils


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

    amount_requested = int(amount_requested)
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

    vault_balances = utils.tasks.tornget.call_local(f'faction/?selections=donations', faction.rand_key())

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
        message = utils.tasks.discordpost(f'channels/{vault_config["banking"]}/messages', payload=message_payload)(blocking=True)

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
