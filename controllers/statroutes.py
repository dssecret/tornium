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

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user

import utils
from controllers.factionroutes import aa_required
from database import session_local
from models.faction import Faction
from models.factionmodel import FactionModel
from models.statmodel import StatModel
from models.user import User

mod = Blueprint('statroutes', __name__)


@mod.route('/stats')
@login_required
def index():
    return render_template('stats/index.html')


@mod.route('/stats/db')
@login_required
def stats():
    return render_template('stats/db.html', battlescore=int(current_user.battlescore[0]))


@mod.route('/stats/dbdata')
@login_required
def stats_data():
    start = int(request.args.get('start'))
    length = int(request.args.get('length'))
    search_value = request.args.get('search[value]')
    session = session_local()

    stats = []
    users = []

    if utils.get_tid(search_value):
        stat_entries = session.query(StatModel).filter_by(tid=utils.get_tid(search_value)).all()
    else:
        stat_entries = session.query(StatModel).all()

    for stat_entry in stat_entries:
        if Faction(User(stat_entry.addedid).factiontid).stat_config['global'] != 1 and \
                User(stat_entry.addedid).factiontid != current_user.factiontid:
            continue
        elif stat_entry.tid in users:
            continue

        stats.append([stat_entry.tid, 'NYI', int(stat_entry.battlescore),
                      utils.rel_time(datetime.datetime.fromtimestamp(stat_entry.timeadded))])
        users.append(stat_entry.tid)

    data = {
        'draw': request.args.get('draw'),
        'recordsTotal': session.query(StatModel).count(),
        'recordsFiltered': len(stats),
        'data': stats[start:start+length]
    }

    return data


@mod.route('/stats/chain')
@login_required
def chain():
    return render_template('stats/chain.html')


@mod.route('/stats/config', methods=['GET', 'POST'])
@login_required
@aa_required
def config():
    faction = Faction(current_user.factiontid)
    session = session_local()

    if request.method == 'POST':
        faction_model = session.query(FactionModel).filter_by(tid=current_user.factiontid).first()

        if (request.form.get('enabled') is not None) ^ (request.form.get('disabled') is not None):
            config = faction.get_stat_config()

            if request.form.get('enabled') is not None:
                config['global'] = 1
                faction_model.statconfig = json.dumps(config)
            else:
                config['global'] = 0
                faction_model.statconfig = json.dumps(config)

            session.flush()

    return render_template('stats/config.html', config=faction.get_stat_config())
