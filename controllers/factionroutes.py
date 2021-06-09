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

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models.faction import Faction
from models.user import User
import utils

mod = Blueprint('factionroutes', __name__)


@mod.route('/faction')
@login_required
def index():
    return render_template('faction/index.html')


@mod.route('/faction/members')
@login_required
def members():
    key = current_user.get_key()
    try:
        factionmembers = utils.tornget('faction/?selections=', key)
    except utils.TornError as e:
        error_code = int(str(e))
        return utils.handle_torn_error(error_code)

    members = []

    for member in factionmembers['members']:
        user = User(int(member))
        user.refresh(key=key)
        members.append(user)

    return render_template('faction/members.html', members=members)
