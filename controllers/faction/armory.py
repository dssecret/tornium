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

from flask import render_template, request, abort
from flask_login import login_required, current_user

from controllers.faction.decorators import fac_required
from models.factionmodel import FactionModel
from models.usermodel import UserModel
from tasks import tornget
import utils


@login_required
@fac_required
def armory(*args, **kwargs):
    return render_template('faction/armory.html')


@login_required
@fac_required
def armoryitemdata(*args, **kwargs):
    if current_user.aa:
        key = current_user.key
    else:
        faction: FactionModel = kwargs['faction']

        if faction is None:
            return {}
        elif len(faction.keys) == 0:
            return {}

        key = random.choice(faction.keys)

    armorydata = tornget('faction/?selections=armor,temporary,weapons', key=key)
    data = []

    for armor in armorydata['armor']:
        data.append([
            f'{armor["name"]} [{armor["ID"]}]',
            armor['quantity'],
            armor['available'],
            armor['loaned']
        ])

    for temporary in armorydata['temporary']:
        data.append([
            f'{temporary["name"]} [{temporary["ID"]}]',
            temporary['quantity'],
            temporary['available'],
            temporary['loaned']
        ])

    for weapon in armorydata['weapons']:
        data.append([
            f'{weapon["name"]} [{weapon["ID"]}]',
            weapon['quantity'],
            weapon['available'],
            weapon['loaned']
        ])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': len(data),
        'data': data
    }
    return data


@login_required
@fac_required
def item_modal(*args, **kwargs):
    if current_user.aa:
        key = current_user.key
    else:
        faction: FactionModel = kwargs['faction']

        if faction is None:
            return {}
        elif len(faction.keys) == 0:
            return {}

        key = random.choice(faction.keys)

    if request.args.get('tid') is None:
        abort(400)

    armorydata = tornget('faction/?selections=armor,temporary,weapons', key=key)
    item = {}

    for armor in armorydata['armor']:
        if armor['ID'] == int(request.args.get('tid')):
            item['ID'] = armor['ID']
            item['name'] = armor['name']
            item['type'] = armor['type']
            item['quantity'] = armor['quantity']
            item['available'] = armor['available']
            item['loaned'] = armor['loaned']
            item['loaned_to'] = armor['loaned_to']
            break

    for temporary in armorydata['temporary']:
        if len(item) != 0:
            break
        elif temporary['ID'] == int(request.args.get('tid')):
            item['ID'] = temporary['ID']
            item['name'] = temporary['name']
            item['type'] = temporary['type']
            item['quantity'] = temporary['quantity']
            item['available'] = temporary['available']
            item['loaned'] = temporary['loaned']
            item['loaned_to'] = temporary['loaned_to']
            break

    for weapon in armorydata['weapons']:
        if len(item) != 0:
            break
        elif weapon['ID'] == int(request.args.get('tid')):
            item['ID'] = weapon['ID']
            item['name'] = weapon['name']
            item['type'] = weapon['type']
            item['quantity'] = weapon['quantity']
            item['available'] = weapon['available']
            item['loaned'] = weapon['loaned']
            item['loaned_to'] = weapon['loaned_to']
            break

    if len(item) == 0:
        abort(400)

    if type(item['loaned_to']) == str:  # More than one person
        print(item)
        loaned_to = {}

        for user in item['loaned_to'].split(','):
            if not user.isdigit():
                print(f'Bad user: {user}')
                continue

            user_db: UserModel = utils.first(UserModel.objects(tid=int(user)))

            if user_db is None:
                if f' [{user}]' in loaned_to:
                    loaned_to[f' [{user}]'] += 1
                else:
                    loaned_to[f' [{user}]'] = 1
            else:
                if f'{user_db.name} [{user_db.tid}]' in loaned_to:
                    loaned_to[f'{user_db.name} [{user_db.tid}]'] += 1
                else:
                    loaned_to[f'{user_db.name} [{user_db.tid}]'] = 1

        item['loaned_to'] = loaned_to
    elif item['loaned_to'] is None:  # No one
        item['loaned_to'] = {}
    else:  # Only one person
        user: UserModel = utils.first(UserModel.objects(tid=item['loaned_to']))

        if user is not None:
            item['loaned_to'] = {f'{user.name} [{user.tid}]': 1}
        else:
            item['loaned_to'] = {f' [{user.tid}]': 1}

    return render_template(
        'faction/armoryitemmodal.html',
        item=item
    )
