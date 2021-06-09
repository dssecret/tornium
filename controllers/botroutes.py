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

from flask import Blueprint, render_template, abort
from flask_login import current_user, login_required

from models.settingsmodel import is_dev

mod = Blueprint('botroutes', __name__)


@mod.route('/bot')
@login_required
def index():
    return render_template('bot/index.html')


@mod.route('/bot/documentation')
@login_required
def documentation():
    if is_dev():  # TODO: Remove once documentation is completed
        return render_template('bot/documentation.html')
    else:
        abort(503)


@mod.route('/bot/host')
@login_required
def hosting():
    if is_dev():  # TODO: Remove once hosting is completed
        return render_template('bot/host.html')
    else:
        abort(503)


@mod.route('/bot/dashbaord')
@login_required
def dashboard():
    if is_dev():  # TODO: Remove once dashboard is completed
        return render_template('bot/dashboard.html')
    else:
        abort(503)
