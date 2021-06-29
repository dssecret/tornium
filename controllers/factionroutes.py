# This file is part of torn-command.
#
# torn-command is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# torn-command is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with torn-command.  If not, see <https://www.gnu.org/licenses/>.

from functools import wraps
import json

from flask import Blueprint, render_template, abort, request
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
        if not current_user.is_authenticated or not current_user.is_admin():
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

    return render_template('faction/bot.html', guildid=faction.guild, vault_config=faction.get_vault_config())
