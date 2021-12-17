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

from functools import wraps
import os
import json

from flask import Blueprint, render_template, abort, request, flash, redirect, jsonify
from flask_login import login_required, current_user
from huey.exceptions import TaskException

from models.faction import Faction
from models.factionmodel import FactionModel
from models.schedule import Schedule
from models.schedulemodel import ScheduleModel
from models.user import User
from models.usermodel import UserModel
from models.withdrawalmodel import WithdrawalModel
import utils
from utils.tasks import tornget

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
def index():
    return render_template('faction/index.html')


@mod.route('/faction/members')
@login_required
def members():
    faction_members = UserModel.objects(factionid=current_user.factiontid)

    return render_template('faction/members.html', members=faction_members)


@mod.route('/faction/targets', methods=['GET', 'POST'])
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


@mod.route('/faction/targets/<int:tid>/remove')
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


@mod.route('/faction/targets/<int:tid>/refresh')
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


@mod.route('/faction/bot', methods=['GET', 'POST'])
@aa_required
@login_required
def bot():
    faction = Faction(current_user.factiontid)

    if request.method == 'POST':
        faction_model = utils.first(FactionModel.objects(tid=current_user.factiontid))

        if request.form.get('guildid') is not None:
            try:
                utils.tasks.discordget.call_local(f'guilds/{request.form.get("guildid")}')
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
            except utils.NetworkingError as e:
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code '
                                             f'{utils.remove_str(str(e))}.')
            except Exception as e:
                raise e

            faction.guild = request.form.get('guildid')
            faction_model.guild = request.form.get('guildid')
            faction_model.save()
        elif request.form.get('withdrawal') is not None:
            try:
                channel = utils.tasks.discordget.call_local(f'channels/{request.form.get("withdrawal")}')
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
            except utils.NetworkingError as e:
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code '
                                             f'{utils.remove_str(str(e))}.')
            except Exception as e:
                raise e

            faction_model.vaultconfig['withdrawal'] = int(channel['id'])
            faction_model.save()
        elif request.form.get('banking') is not None:
            try:
                channel = utils.tasks.discordget.call_local(f'channels/{request.form.get("banking")}')
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
            except utils.NetworkingError as e:
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code '
                                             f'{utils.remove_str(str(e))}.')
            except Exception as e:
                raise e

            faction_model.vaultconfig['banking'] = int(channel['id'])
            faction_model.save()
        elif request.form.get('banker') is not None:
            try:
                roles = utils.tasks.discordget.call_local(f'guilds/{faction.guild}/roles')
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
            except utils.NetworkingError as e:
                return render_template('errors/error.html', title='Discord Networking Error',
                                       error=f'The Discord API has responded with HTTP error code '
                                             f'{utils.remove_str(str(e))}.')
            except Exception as e:
                raise e

            for role in roles:  # TODO: Add error message for role not found in server
                if role['id'] == request.form.get('banker'):
                    faction_model.vaultconfig['banker'] = int(request.form.get('banker'))
                    faction_model.save()
        elif (request.form.get('enabled') is not None) ^ (request.form.get('disabled') is not None):
            if request.form.get('enabled') is not None:
                faction_model.config['vault'] = 1
            else:
                faction_model.config['vault'] = 0

            faction_model.save()

    return render_template('faction/bot.html', guildid=faction.guild, vault_config=faction.get_vault_config(),
                           config=faction.get_config())


@mod.route('/faction/bankingaa')
@aa_required
@login_required
def bankingaa():
    return render_template('faction/bankingaa.html')


@mod.route('/faction/bankingdata')
@aa_required
@login_required
def bankingdata():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    withdrawals = []

    for withdrawal in WithdrawalModel.objects(factiontid=current_user.factiontid):
        requester = f'{User(withdrawal.requester).name} [{withdrawal.requester}]'
        fulfiller = f'{User(withdrawal.fulfiller).name} [{withdrawal.fulfiller}]' if withdrawal.fulfiller != 0 else ''
        timefulfilled = withdrawal.time_fulfilled if withdrawal.time_fulfilled != 0 else ''

        withdrawals.append([withdrawal.wid, f'${withdrawal.amount:,}', requester,
                            utils.torn_timestamp(withdrawal.time_requested), fulfiller,
                            utils.torn_timestamp(timefulfilled)])

    withdrawals = withdrawals[start:start+length]
    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': WithdrawalModel.objects().count(),
        'recordsFiltered': WithdrawalModel.objects(factiontid=current_user.factiontid).count(),
        'data': withdrawals
    }
    return data


@mod.route('/faction/banking')
@login_required
def banking():
    return render_template('faction/banking.html', key=current_user.key)


@mod.route('/faction/userbankingdata')
@login_required
def userbankingdata():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    withdrawals = []

    for withdrawal in WithdrawalModel.objects(requester=current_user.tid):
        fulfiller = f'{User(withdrawal.fulfiller).name} [{withdrawal.fulfiller}]' if withdrawal.fulfiller != 0 else ''
        timefulfilled = utils.torn_timestamp(withdrawal.time_fulfilled) if withdrawal.time_fulfilled != 0 else ''

        withdrawals.append([withdrawal.wid, f'${withdrawal.amount:,}', utils.torn_timestamp(withdrawal.time_requested),
                            fulfiller, timefulfilled])

    withdrawals = withdrawals[start:start+length]
    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': WithdrawalModel.objects().count(),
        'recordsFiltered': WithdrawalModel.objects(factiontid=current_user.factiontid).count(),
        'data': withdrawals
    }
    return data


@mod.route('/faction/chain', methods=['GET', 'POST'])
@login_required
def chain():
    faction = Faction(current_user.factiontid)

    if request.method == 'POST':
        faction_model = utils.first(FactionModel.objects(tid=current_user.factiontid))

        if request.form.get('odchannel') is not None:
            try:
                channel = utils.tasks.discordget(f'channels/{request.form.get("odchannel")}')
                channel = channel(blocking=True)
            except TaskException as e:
                e = str(e)
                if 'DiscordError' in e:
                    return utils.handle_discord_error(e)
                elif 'NetworkingError' in e:
                    return render_template('errors/error.html', title='Discord Networking Error',
                                           error=f'The Discord API has responded with HTTP error code '
                                                 f'{utils.remove_str(e)}.')
                else:
                    raise e

            config = faction.get_chain_config()
            config['odchannel'] = int(channel['id'])
            faction_model.chainconfig = config
            faction_model.save()
        elif (request.form.get('odenabled') is not None) ^ (request.form.get('oddisabled') is not None):
            config = faction.chain_config

            if request.form.get('odenabled') is not None:
                config['od'] = 1
                faction_model.chainconfig = config
                faction_model.save()
            if request.form.get('oddisabled') is not None:
                config['od'] = 0
                faction_model.chainconfig = config
                faction_model.save()

    return render_template('faction/chain.html', faction=faction)


@mod.route('/faction/schedule', methods=['GET'])
@login_required
def schedule():
    if request.args.get('uuid') is not None and request.args.get('watchers') is None:
        schedule = Schedule(request.args.get('uuid'), factiontid=current_user.factiontid)
        return render_template('faction/schedulemodal.html', sid=schedule.name)
    elif request.args.get('uuid') is not None and request.args.get('watchers') is not None:
        schedule = Schedule(request.args.get('uuid'), factiontid=current_user.factiontid)
        data = []

        for tid, userdata in schedule.activity.items():
            modified_userdata = []

            for activity in userdata:
                activity = [int(activity.split('-')[0]), int(activity.split('-')[1])]
                activity[0] = utils.torn_timestamp(activity[0])
                activity[1] = utils.torn_timestamp(activity[1])
                modified_userdata.append(f'{activity[0]} to {activity[1]}')

            data.append([f'{User(tid).name} [{tid}]', modified_userdata, schedule.weight[tid]])

        return jsonify(data)
    
    return render_template('faction/schedule.html', key=current_user.key)


@mod.route('/faction/scheduledata')
@login_required
def schedule_data():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    faction = Faction(current_user.factiontid)
    schedules = []

    for schedule in ScheduleModel.objects(factiontid=faction.tid):
        with open(f'{os.getcwd()}/schedule/{schedule.uuid}.json') as file:
            data = json.load(file)
            schedules.append([
                schedule.uuid,
                data['name'],
                utils.torn_timestamp(data['timecreated']),
                utils.torn_timestamp(data['timeupdated'])
            ])

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': ScheduleModel.objects().count(),
        'recordsFiltered': len(schedules),
        'data': schedules[start:start + length]
    }
    return data
