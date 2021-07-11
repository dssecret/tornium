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

from math import ceil
from functools import wraps
import json

from flask import Blueprint, render_template, abort, request, flash, redirect
from flask_login import login_required, current_user

from database import session_local
from models.faction import Faction
from models.factionmodel import FactionModel
from models.user import User
import utils
from utils.tornget import tornget

mod = Blueprint('factionroutes', __name__)


def aa_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.aa:
            return abort(403)
        else:
            return f(*args, **kwargs)

    return wrapper


@mod.route('/faction')
@login_required
def index():
    return render_template('faction/index.html')


@mod.route('/faction/members')
@login_required
def members():
    key = current_user.get_key()
    try:
        factionmembers = tornget('faction/?selections=', key)
    except utils.TornError as e:
        error_code = int(str(e))
        return utils.handle_torn_error(error_code)

    members = []

    for member in factionmembers['members']:
        user = User(int(member))
        user.refresh(key=key)
        members.append(user)

    return render_template('faction/members.html', members=members)


@mod.route('/faction/targets', methods=['GET', 'POST'])
@login_required
def targets():
    faction = Faction(current_user.factiontid)

    print(faction.targets)

    if request.method == 'POST':
        if not current_user.is_aa():
            flash('This action requires the user to be an AA user.', category='warning')
            return render_template('faction/targets.html', targets=faction.targets)

        session = session_local()
        faction_model = session.query(FactionModel).filter_by(tid=current_user.factiontid).first()

        if request.form.get('targetid') is not None:
            if int(request.form.get('targetid')) in faction.targets:
                flash('The user attempted to be targeted is already being targeted.')
                return render_template('faction/targets.html', targets=faction.targets)

            try:
                torn_user = utils.tornget('user/?selections=', current_user.key)
            except utils.TornError as e:
                flash(f'The Torn API has returned error code {e}.', category='error')
                return render_template('faction/targets.html', targets=faction.targets)
            except utils.NetworkingError as e:
                flash(f'The Torn API has had a networking error and has returned HTTP {e}', category='error')
                return render_template('faction/targets.html', targets=faction.targets)

            faction.targets[int(torn_user['player_id'])] = {
                'name': torn_user['name'],
                'level': torn_user['level']
            }

            faction_model.targets = json.dumps(faction.targets)
            session.flush()

    return render_template('faction/targets.html', targets=faction.targets)


@mod.route('/faction/targets/<int:tid>/remove')
@login_required
@aa_required
def remove_target(tid):
    faction = Faction(current_user.factiontid)

    if not current_user.is_aa():
        flash('This action requires the user to be an AA user.', category='warning')
        return redirect('/faction/targets')
    elif tid in faction.targets:
        flash('The user attempted to be targeted is already being targeted.')
        return redirect('/faction/targets')

    session = session_local()
    faction_model = session.query(FactionModel).filter_by(tid=current_user.factiontid).first()
    faction.targets.pop(tid)
    faction_model.targets = json.dumps(faction.targets)
    session.flush()

    return redirect('/faction/targets')


@mod.route('/faction/bot', methods=['GET', 'POST'])
@aa_required
@login_required
def bot():
    faction = Faction(current_user.factiontid)
    session = session_local()

    if request.method == 'POST':
        faction_model = session.query(FactionModel).filter_by(tid=current_user.factiontid).first()

        if request.form.get('guildid') is not None:
            try:
                utils.discordget(f'guilds/{request.form.get("guildid")}')
            except utils.DiscordError as e:
                error_code = int(str(e))
                return utils.handle_discord_error(error_code)
            except utils.NetworkingError as e:
                error_code = int(str(e))
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code {error_code}.')

            faction.guild = request.form.get('guildid')
            faction_model.guild = request.form.get('guildid')
            session.flush()
        elif request.form.get('banking') is not None:
            try:
                channel = utils.discordget(f'channels/{request.form.get("banking")}')
            except utils.DiscordError as e:
                error_code = int(str(e))
                return utils.handle_discord_error(error_code)
            except utils.NetworkingError as e:
                error_code = int(str(e))
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code {error_code}.')

            vault_config = faction.get_vault_config()
            vault_config['banking'] = int(channel['id'])
            faction_model.vaultconfig = json.dumps(vault_config)
            session.flush()
        elif request.form.get('banker') is not None:
            try:
                roles = utils.discordget(f'guilds/{faction.guild}/roles')
            except utils.DiscordError as e:
                error_code = int(str(e))
                return utils.handle_discord_error(error_code)
            except utils.NetworkingError as e:
                error_code = int(str(e))
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code {error_code}.')

            for role in roles:
                if role['id'] == request.form.get('banker'):
                    vault_config = faction.get_vault_config()
                    vault_config['banker'] = int(request.form.get('banker'))
                    faction_model.vaultconfig = json.dumps(vault_config)
                    session.flush()
        elif (request.form.get('enabled') is not None) ^ (request.form.get('disabled') is not None):
            config = faction.get_config()

            if request.form.get('enabled') is not None:
                config['vault'] = 1
                faction_model.config = json.dumps(config)
            else:
                config['vault'] = 0
                faction_model.config = json.dumps(config)

            session.flush()

    return render_template('faction/bot.html', guildid=faction.guild, vault_config=faction.get_vault_config(), config=faction.get_config())


@mod.route('/faction/banking')
@mod.route('/faction/banking?<int:page>')
@aa_required
@login_required
def banking(page=1):
    faction = Faction(current_user.factiontid)
    requests = faction.withdrawals[(10 * (page - 1)):(10 * page)]

    for request_index in range(len(requests)):
        requests[request_index]['requester'] = f'{User(requests[request_index]["requester"]).name} [{requests[request_index]["requester"]}]'
        requests[request_index]['fulfiller'] = f'{User(requests[request_index]["fulfiller"]).name} [{requests[request_index]["fulfiller"]}]'

    return render_template('faction/banking.html',
                           requests=requests,
                           lastpage=int(ceil(len(faction.withdrawals) / 10)))
