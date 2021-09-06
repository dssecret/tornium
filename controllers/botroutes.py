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

import datetime
import json

from flask import Blueprint, render_template, abort, request, redirect, flash, jsonify
from flask_login import current_user, login_required
from is_safe_url import is_safe_url

from database import session_local
from models.faction import Faction
from models.factionstakeoutmodel import FactionStakeoutModel
from models.settingsmodel import get
from models.server import Server
from models.servermodel import ServerModel
from models.stakeout import Stakeout
from models.user import User
from models.userstakeoutmodel import UserStakeoutModel
import utils
from utils.tasks import discordpost, discorddelete

mod = Blueprint('botroutes', __name__)


@mod.route('/bot')
def index():
    return render_template('bot/index.html')


@mod.route('/bot/documentation')
def documentation():
    return render_template('bot/documentation.html')


@mod.route('/bot/host')
def hosting():
    return render_template('bot/host.html')


@mod.route('/bot/dashboard')
@login_required
def dashboard():
    servers = []

    for server in current_user.servers:
        servers.append(Server(server))

    return render_template('bot/dashboard.html', servers=servers)


@mod.route('/bot/dashboard/<string:guildid>', methods=['GET', 'POST'])
@login_required
def guild_dashboard(guildid: str):
    if guildid not in current_user.servers:
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

    return render_template('bot/guild.html', server=server, factions=factions, guildid=guildid)


@mod.route('/bot/dashboard/<string:guildid>/<int:factiontid>', methods=['POST'])
@login_required
def update_guild(guildid: str, factiontid: int):
    if guildid not in current_user.servers:
        abort(403)

    session = session_local()

    server = Server(guildid)
    server.factions.remove(factiontid)
    server_model = session.query(ServerModel).filter_by(sid=guildid).first()
    server_model.factions = json.dumps(server.factions)
    session.flush()

    return redirect(f'/bot/dashboard/{guildid}')


@mod.route('/bot/stakeouts/<string:guildid>', methods=['GET', 'POST'])
@login_required
def stakeouts_dashboard(guildid: str):
    if guildid not in current_user.servers:
        abort(403)

    server = Server(guildid)

    if request.method == 'POST':
        session = session_local()
        server_db = session.query(ServerModel).filter_by(sid=guildid).first()

        if request.form.get('factionid') is not None:
            if session.query(FactionStakeoutModel).filter_by(tid=request.form.get('factionid')).first() is None:
                stakeout = Stakeout(int(request.form.get('factionid')), user=False, key=current_user.key,
                                    guild=int(guildid))
                server.faction_stakeouts.append(int(request.form.get('factionid')))
                server_db.factionstakeouts = json.dumps(list(set(server.faction_stakeouts)))
                session.flush()

                payload = {
                    'name': f'faction-{stakeout.data["name"]}',
                    'type': 0,
                    'topic': f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                             f'[{stakeout.data["ID"]}] by the Tornium bot.',
                    'parent_id': server.stakeout_config['category']
                }  # TODO: Add permission overwrite: everyone write false

                channel = discordpost(f'guilds/{guildid}/channels', payload=payload)
                channel = channel(blocking=True)

                stakeout.guilds[guildid]['channel'] = int(channel['id'])
                db_stakeout = session.query(FactionStakeoutModel).filter_by(tid=request.form.get('factionid')).first()
                db_stakeout.guilds = json.dumps(stakeout.guilds)
                session.flush()

                message_payload = {
                    'embeds': [
                        {
                            'title': 'Faction Stakeout Creation',
                            'description': f'A stakeout of faction {stakeout.data["name"]} has been created in '
                                           f'{server.name}. This stakeout can be setup or removed in the '
                                           f'[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{server.sid}) by a '
                                           f'server administrator.',
                            'timestamp': datetime.datetime.utcnow().isoformat()
                        }
                    ]
                }
                discordpost(f'channels/{channel["id"]}/messages', payload=message_payload)()
            else:
                flash(f'Faction ID {request.form.get("factionid")} is already being staked out in {server.name}.',
                      category='error')
        elif request.form.get('userid') is not None:
            if session.query(UserStakeoutModel).filter_by(tid=request.form.get('userid')).first() is None:
                stakeout = Stakeout(int(request.form.get('userid')), key=current_user.key, guild=int(guildid))
                server.user_stakeouts.append(int(request.form.get('userid')))
                server_db.userstakeouts = json.dumps(list(set(server.user_stakeouts)))

                payload = {
                    'name': f'user-{stakeout.data["name"]}',
                    'type': 0,
                    'topic': f'The bot-created channel for stakeout notifications for {stakeout.data["name"]} '
                             f'[{stakeout.data["player_id"]}] by the Tornium bot.',
                    'parent_id': server.stakeout_config['category']
                }  # TODO: Add permission overwrite: everyone write false

                channel = discordpost(f'guilds/{guildid}/channels', payload=payload)
                channel = channel(blocking=True)

                stakeout.guilds[guildid]['channel'] = int(channel['id'])
                db_stakeout = session.query(UserStakeoutModel).filter_by(tid=request.form.get('userid')).first()
                db_stakeout.guilds = json.dumps(stakeout.guilds)
                session.flush()

                message_payload = {
                    'embeds': [
                        {
                            'title': 'User Stakeout Creation',
                            'description': f'A stakeout of user {stakeout.data["name"]} has been created in '
                                           f'{server.name}. This stakeout can be setup or removed in the '
                                           f'[Tornium Dashboard](https://torn.deek.sh/bot/stakeouts/{server.sid}) by a '
                                           f'server administrator.',
                            'timestamp': datetime.datetime.utcnow().isoformat()
                        }
                    ]
                }
                discordpost(f'channels/{channel["id"]}/messages', payload=message_payload)()
            else:
                flash(f'User ID {request.form.get("userid")} is already being staked out in {server.name}.',
                      category='error')

    return render_template('bot/stakeouts.html', guildid=guildid)


@mod.route('/bot/stakeouts/<string:guildid>/<int:stype>')
@login_required
def stakeouts(guildid: str, stype: int):
    if guildid not in current_user.servers:
        abort(403)

    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    server = Server(guildid)
    stakeouts = []

    if stype == 0:  # user
        filtered = len(server.user_stakeouts)
        for stakeout in server.user_stakeouts:
            stakeout = Stakeout(int(stakeout), key=current_user.key)
            stakeouts.append(
                [stakeout.tid, stakeout.guilds[guildid]['keys'], utils.rel_time(datetime.datetime.fromtimestamp(stakeout.last_update))]
            )
    elif stype == 1:  # faction
        filtered = len(server.faction_stakeouts)
        for stakeout in server.faction_stakeouts:
            stakeout = Stakeout(int(stakeout), user=False, key=current_user.key)
            stakeouts.append(
                [stakeout.tid, stakeout.guilds[guildid]['keys'], utils.rel_time(datetime.datetime.fromtimestamp(stakeout.last_update))]
            )
    else:
        filtered = 0

    stakeouts = stakeouts[start:start+length]
    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': len(server.user_stakeouts) + len(server.faction_stakeouts),
        'recordsFiltered': filtered,
        'data': stakeouts
    }
    return data


@mod.route('/bot/stakeouts/<string:guildid>/modal')
@login_required
def stakeout_data(guildid: str):
    if guildid not in current_user.servers:
        abort(404)

    faction = request.args.get('faction')
    user = request.args.get('user')

    if (not faction and not user) or (faction and user):
        raise Exception  # TODO: make exception more descriptive

    server = Server(guildid)

    if faction:
        if int(faction) not in server.faction_stakeouts:
            raise Exception

        stakeout = Stakeout(faction, user=False)

        return render_template('bot/factionstakeoutmodal.html',
                               faction=f'{Faction(faction, key=current_user.key).name} [{faction}]',
                               lastupdate=utils.rel_time(datetime.datetime.fromtimestamp(stakeout.last_update)),
                               keys=stakeout.guilds[guildid]['keys'],
                               guildid=guildid,
                               tid=faction)
    elif user:
        if int(user) not in server.user_stakeouts:
            raise Exception

        stakeout = Stakeout(user)
        return render_template('bot/userstakeoutmodal.html',
                               user=f'{User(user, key=current_user.key).name} [{user}]',
                               lastupdate=utils.rel_time(datetime.datetime.fromtimestamp(stakeout.last_update)),
                               keys=stakeout.guilds[guildid]['keys'],
                               guildid=guildid,
                               tid=user)


@mod.route('/bot/stakeouts/<string:guildid>/update', methods=['GET', 'POST'])
@login_required
def stakeout_update(guildid):
    action = request.args.get('action')
    faction = request.args.get('faction')
    user = request.args.get('user')
    value = request.args.get('value')

    if action not in ['remove', 'addkey', 'removekey', 'enable', 'disable', 'category']:
        return json.dumps({'success': True}), 400, {'ContentType': 'application/json'}
    elif faction and user:
        return json.dumps({'success': True}), 400, {'ContentType': 'application/json'}

    session = session_local

    if action == 'remove':
        server = session.query(ServerModel).filter_by(sid=guildid).first()

        if faction is not None:
            stakeouts = json.loads(server.factionstakeouts)
            stakeouts.remove(int(faction))
            server.factionstakeouts = json.dumps(stakeouts)

            stakeout = session.query(FactionStakeoutModel).filter_by(tid=faction).first()
            discorddelete(f'channels/{json.loads(stakeout.guilds)[guildid]["channel"]}')()
            session.delete(stakeout)
        elif user is not None:
            stakeouts = json.loads(server.userstakeouts)
            stakeouts.remove(int(user))
            server.userstakeouts = json.dumps(stakeouts)

            stakeout = session.query(UserStakeoutModel).filter_by(tid=user).first()
            discorddelete(f'channels/{json.loads(stakeout.guilds)[guildid]["channel"]}')()
            session.delete(stakeout)

        session.flush()
    elif action == 'addkey':
        if faction is not None and value not in ['territory', 'members', 'memberstatus', 'memberactivity']:
            return jsonify({'error': f'Faction is set to {faction} for a key that doesn\'t allow a faction '
                                     f'ID to be passed.'}), 400
        elif user is not None and value not in ['level', 'status', 'flyingstatus', 'online', 'offline']:
            return jsonify({'error': f'User is set to {user} for a key that doesn\'t allow a user '
                                     f'ID to be passed.'}), 400

        if user is not None:
            stakeout = session.query(UserStakeoutModel).filter_by(tid=user).first()
        else:
            stakeout = session.query(FactionStakeoutModel).filter_by(tid=faction).first()
        
        guilds = json.loads(stakeout.guilds)

        if value in guilds[guildid]['keys']:
            return jsonify({'error': f'Value {value} is already in {guildid}\'s list of keys.'}), 400

        guilds[guildid]['keys'].append(value)
        stakeout.guilds = json.dumps(guilds)
        session.flush()
    elif action == 'removekey':
        if faction is not None and value not in ['territory', 'members', 'memberstatus', 'memberactivity']:
            return jsonify({'error': f'Faction is set to {faction} for a key that doesn\'t allow a faction '
                                     f'ID to be passed.'}), 400
        elif user is not None and value not in ['level', 'status', 'flyingstatus', 'online', 'offline']:
            return jsonify({'error': f'User is set to {user} for a key that doesn\'t allow a user '
                                     f'ID to be passed.'}), 400

        if user is not None:
            stakeout = session.query(UserStakeoutModel).filter_by(tid=user).first()
        else:
            stakeout = session.query(FactionStakeoutModel).filter_by(tid=faction).first()

        guilds = json.loads(stakeout.guilds)

        if value not in guilds[guildid]['keys']:
            return jsonify({'error': f'Value {value} is not in {guildid}\'s list of keys.'}), 400

        guilds[guildid]['keys'].remove(value)
        stakeout.guilds = json.dumps(guilds)
        session.flush()
    elif action == 'enable':
        server = session.query(ServerModel).filter_by(sid=guildid).first()
        config = json.loads(server.config)
        config['stakeouts'] = 1
        server.config = json.dumps(config)
        session.flush()
    elif action == 'disable':
        server = session.query(ServerModel).filter_by(sid=guildid).first()
        config = json.loads(server.config)
        config['stakeouts'] = 0
        server.config = json.dumps(config)
        session.flush()
    elif action == 'category':
        server = session.query(ServerModel).filter_by(sid=guildid).first()
        config = json.loads(server.stakeoutconfig)
        config['category'] = int(value)
        server.stakeoutconfig = json.dumps(config)
        session.flush()

    if request.method == 'GET':
        return redirect(f'/bot/stakeouts/{guildid}')
    else:
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
