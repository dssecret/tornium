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

from flask import Blueprint

from controllers.api import faction
from controllers.api import key

mod = Blueprint('apiroutes', __name__)


# /api/key
mod.add_url_route('/api/key', view_func=key.test_key, methods=['GET'])
mod.add_url_route('/api/key', view_func=key.create_key, methods=['POST'])
mod.add_url_route('/api/key', view_func=key.delete_key, methods=['DELETE'])

# /api/faction
mod.add_url_route('/api/faction/banking', view_func=faction.banking_request, methods=['POST'])
