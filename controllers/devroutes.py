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

from flask import Blueprint, render_template, jsonify, redirect
from flask_login import login_required

from controllers.adminroutes import admin_required
from database import session_local
from models.faction import Faction
from models.factionmodel import FactionModel
from models.server import Server
from models.servermodel import ServerModel
from models.user import User
from models.usermodel import UserModel

mod = Blueprint('devroutes', __name__)


@mod.route('/base')
@admin_required
def base():
    return render_template('base.html')


@mod.route('/user/<int:id>')
@admin_required
def user(id):
    user = User(id)
    return jsonify(
        tid=user.tid,
        name=user.name,
        level=user.level,
        admin=user.admin,
        key=user.key,
        discord_id=user.discord_id,
        servers=user.servers,
        faction_id=user.factiontid,
        aa=user.aa,
        last_refresh=user.last_refresh,
        status=user.status,
        last_action=user.last_action
    )


@mod.route('/user/<int:id>/<string:key>/<string:value>')
@admin_required
def edit_user(id, key, value):
    session = session_local()
    usermodel = session.query(UserModel).filter_by(tid=id)

    if key == "servers":
        usermodel.servers = value
        session.flush()
    else:
        raise NotImplementedError

    return redirect(f'/user/{id}')


@mod.route('/faction/<int:id>')
@admin_required
def faction(id):
    faction = Faction(id)
    return jsonify(
        tid=faction.tid,
        name=faction.name,
        respect=faction.respect,
        capacity=faction.capacity,
        keys=faction.keys,
        last_members=faction.last_members,
        withdrawals=faction.withdrawals,
        guild=faction.guild,
        vault_config=faction.vault_config
    )


@mod.route('/faction/<int:id>/<string:key>/<string:value>')
@admin_required
def edit_faction(id, key, value):
    session = session_local()
    factionmodel = session.query(FactionModel).filter_by(tid=id).first()

    if key == "keys":
        factionmodel.keys = value
        session.flush()
    else:
        raise NotImplementedError

    return redirect(f'/faction/{id}')


@mod.route('/server/<int:id>')
@admin_required
def server(id):
    server = Server(id)
    return jsonify(
        sid=server.sid,
        name=server.name,
        admins=server.admins,
        prefix=server.prefix,
        factions=server.factions
    )


@mod.route('/server/<int:id>/<string:key>/<string:value>')
@admin_required
def edit_server(id, key, value):
    session = session_local()
    servermodel = session.query(ServerModel).filter_by(sid=id).first()

    if key == "factions":
        pass
