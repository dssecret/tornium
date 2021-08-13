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

from models import settingsmodel
import utils

huey = MiniHuey()  # Utilizes https://huey.readthedocs.io/en/latest/contrib.html#mini-huey


@huey.task()
def tornget(endpoint, key, tots=0, fromts=0, session=None):
    url = f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}' \
          f'{"" if tots == 0 else f"&to={tots}"}'

    if session is None:  # Utilizes https://docs.python-requests.org/en/latest/user/advanced/#session-objects
        request = requests.get(url)
    else:
        request = session.get(url)

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


@huey.task()
def discordget(endpoint, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'

    if session is None:
        request = requests.get(url, headers={'Authorization': f'Bot {settingsmodel.get("settings", "bottoken")}'})
    else:
        request = session.get(url, headers={'Authorization': f'Bot {settingsmodel.get("settings", "bottoken")}'})

    request_json = request.json()

    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a fill list of error code
        # explanations

        utils.get_logger().info(f'The Discord API has responded with error code {request_json["code"]} '
                                f'({request_json["message"]}) to {url}).')
        raise utils.DiscordError(request_json["code"])

    if request.status_code != 200:
        utils.get_logger().warning(f'The Discord API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    return request_json

