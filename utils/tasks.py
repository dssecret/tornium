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

from huey.contrib.mini import MiniHuey
import requests

import utils

huey = MiniHuey()


@huey.task()
def tornget(endpoint, key, tots=0, fromts=0):
    url = f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}' \
          f'{"" if tots == 0 else f"&to={tots}"}'
    request = requests.get(url)

    if request.status_code != 200:
        utils.get_logger().warning(f'The Torn API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    request = request.json()

    if 'error' in request:
        utils.get_logger().info(f'The Torn API has responded with error code {request["error"]["code"]} '
                                f'({request["error"]["error"]}) to {endpoint}).')
        raise utils.TornError(request["error"]["code"])

    return request
