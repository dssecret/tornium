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

from flask import render_template, request, flash, redirect
from flask_login import login_required

from controllers.faction. decorators import *
from models.faction import Faction
from models.factionmodel import FactionModel
import utils
from utils.tasks import tornget


@login_required
def targets():
    faction = Faction(current_user.factiontid)

    if request.method == 'POST':
        if not current_user.aa:
            flash('This action requires the user to be an AA user.', category='warning')
            return render_template('faction/targets.html', targets=faction.targets)

        faction_model = utils.first(FactionModel.objects(tid=current_user.factiontid))

        if request.form.get('targetid') is not None:
            if request.form.get('targetid') in faction.targets:
                flash('The user attempted to be targeted is already being targeted.', category='warning')
                return render_template('faction/targets.html', targets=faction.targets)

            try:
                torn_user = tornget.call_local(f'user/{request.form.get("targetid")}?selections=', current_user.key)
            except utils.TornError as e:
                return utils.handle_torn_error(str(e))
            except Exception as e:
                raise e

            faction.targets[torn_user['player_id']] = {
                'last_update': utils.now(),
                'name': torn_user['name'],
                'level': torn_user['level']
            }

            faction_model.targets = faction.targets
            faction_model.save()

    return render_template('faction/targets.html', targets=faction.targets)


@login_required
@aa_required
def remove_target(tid):
    faction = Faction(current_user.factiontid)

    if not current_user.aa:
        flash('This action requires the user to be an AA user.', category='warning')
        return redirect('/faction/targets')

    faction_model = utils.first(FactionModel.objects(tid=current_user.factiontid))
    faction.targets.pop(str(tid))
    faction_model.targets = faction.targets
    faction_model.save()

    return redirect('/faction/targets')


@login_required
def refresh_target(tid):
    faction = Faction(current_user.factiontid)

    try:
        torn_user = tornget.call_local(f'user/{tid}?selections=', current_user.key)
    except utils.TornError as e:
        return utils.handle_torn_error(str(e))
    except Exception as e:
        raise e

    faction.targets[str(torn_user['player_id'])]['name'] = torn_user['name']
    faction.targets[str(torn_user['player_id'])]['level'] = torn_user['level']
    faction.targets[str(torn_user['player_id'])]['last_update'] = utils.now()

    faction_model = utils.first(FactionModel.objects(tid=current_user.factiontid))
    faction_model.targets = json.dumps(faction.targets)
    faction_model.save()

    return redirect('/faction/targets')
