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

from flask import Blueprint, render_template

from controllers.api import key
from controllers.api import stakeout
from controllers.api.faction import banking

mod = Blueprint('apiroutes', __name__)


# /api/key
mod.add_url_rule('/api/key', view_func=key.test_key, methods=['GET'])
mod.add_url_rule('/api/key', view_func=key.create_key, methods=['POST'])
mod.add_url_rule('/api/key', view_func=key.remove_key, methods=['DELETE'])

# /api/faction
mod.add_url_rule('/api/faction/banking', view_func=banking.banking_request, methods=['POST'])

# /api/stakeout
mod.add_url_rule('/api/stakeout/<string:stype>', view_func=stakeout.create_stakeout, methods=['POST'])


@mod.route('/api')
def index():
    return render_template('api/index.html')
