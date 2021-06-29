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

from flask import Blueprint, render_template, abort, request
from flask_login import login_required, current_user

from models import settingsmodel


mod = Blueprint('adminroutes', __name__)


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if (not current_user.is_authenticated or not current_user.is_admin()) and not settingsmodel.is_dev():
            return abort(403)
        else:
            return f(*args, **kwargs)

    return wrapper


@mod.route('/admin')
@login_required
@admin_required
def index():
    return render_template('admin/index.html')


@mod.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')


@mod.route('/admin/bot', methods=['GET', 'POST'])
@login_required
@admin_required
def bot():
    if request.method == 'POST':
        if request.form.get('bottoken') is not None:
            settingsmodel.update('settings', 'bottoken', request.form.get('bottoken'))

    return render_template('admin/bot.html', bottoken=settingsmodel.get('settings', 'bottoken'))
