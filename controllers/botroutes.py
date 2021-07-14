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

from flask import Blueprint, render_template, abort, request, redirect, flash
from flask_login import current_user, login_required

from database import session_local
from models.faction import Faction
from models.server import Server
from models.servermodel import ServerModel

mod = Blueprint('botroutes', __name__)


@mod.route('/bot')
@login_required
def index():
    return render_template('bot/index.html')


@mod.route('/bot/documentation')
@login_required
def documentation():
    return render_template('bot/documentation.html')


@mod.route('/bot/host')
@login_required
def hosting():
    return render_template('bot/host.html')


@mod.route('/bot/dashboard')
@login_required
def dashboard():
    servers = []

    for server in current_user.servers:
        servers.append(Server(server))

    return render_template('bot/dashboard.html', servers=servers)


@mod.route('/bot/dashboard/<int:guildid>', methods=['GET', 'POST'])
@login_required
def guild_dashboard(guildid: int):  # TODO: Add check to see if user is guild admin
    if str(guildid) not in current_user.servers:
        abort(403)

    session = session_local()
    server = Server(guildid)
    factions = []

    if request.method == 'POST':
        if request.form.get('factionid') is not None:
            server.factions.append(int(request.form.get('factionid')))
            server_model = session.query(ServerModel).filter_by(sid=guildid).first()
            server_model.factions = json.dumps(server.factions)
            session.flush()
        elif request.form.get('prefix') is not None:  # TODO: Check if prefix is valid character
            if len(request.form.get('prefix')) != 1:
                flash('The length of the bot prefix must be one character long.')
                return render_template('bot/guild.html', server=server, factions=factions)

            server.prefix = request.form.get('prefix')
            server_model = session.query(ServerModel).filter_by(sid=guildid).first()
            server_model.prefix = request.form.get('prefix')
            session.flush()

    for faction in server.factions:
        factions.append(Faction(faction))

    return render_template('bot/guild.html', server=server, factions=factions)


@mod.route('/bot/dashboard/<int:guildid>/<int:factiontid>', methods=['POST'])
@login_required
def update_guild(guildid: int, factiontid: int):  # TODO: Add check to see if user is guild admin
    if guildid not in current_user.servers:
        abort(403)

    session = session_local()

    server = Server(guildid)
    server.factions.remove(factiontid)
    server_model = session.query(ServerModel).filter_by(sid=guildid).first()
    server_model.factions = json.dumps(server.factions)
    session.flush()

    return redirect(f'/bot/dashboard/{guildid}')
