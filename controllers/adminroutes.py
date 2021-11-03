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

from flask import Blueprint, render_template, abort, request
from flask_login import login_required, current_user

from redisdb import get_redis
import utils.tasks


mod = Blueprint('adminroutes', __name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if (not current_user.is_authenticated or not current_user.admin) and not get_redis().get('dev'):
            return abort(403)
        else:
            return f(*args, **kwargs)

    return wrapper


@mod.route('/admin')
@login_required
@admin_required
def index():
    return render_template('admin/index.html')


@mod.route('/admin/dashboard', methods=['GET', 'POST'])
@login_required
@admin_required
def dashboard():
    if request.method == 'POST':
        if request.form.get('refreshfactions') is not None:
            utils.tasks.refresh_factions()
        elif request.form.get('refreshguilds') is not None:
            utils.tasks.refresh_guilds()
        elif request.form.get('refreshusers') is not None:
            utils.tasks.refresh_users()
        elif request.form.get('fetchattacks') is not None:
            utils.tasks.fetch_attacks()
        elif request.form.get('refreshuserstakeouts') is not None:
            utils.tasks.update_user_stakeouts()
        elif request.form.get('refreshfactionstakeouts') is not None:
            utils.tasks.update_faction_stakeouts()

    return render_template('admin/dashboard.html')


@mod.route('/admin/bot', methods=['GET', 'POST'])
@login_required
@admin_required
def bot():
    redis = get_redis()

    if request.method == 'POST':
        if request.form.get('bottoken') is not None:
            redis.set('bottoken', request.form.get('bottoken'))

    return render_template('admin/bot.html', bottoken=redis.get('bottoken'))
