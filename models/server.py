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
import json

from database import session_local
from models.servermodel import ServerModel
from utils.tasks import discordget


class Server:
    def __init__(self, sid):
        """
        Retrieves the server from the database.

        :param sid: Discord server ID
        """

        session = session_local()
        server = session.query(ServerModel).filter_by(sid=sid).first()
        if server is None:
            guild = discordget(f'guilds/{sid}')
            guild = guild(blocking=True)

            server = ServerModel(
                sid=sid,
                name=guild['name'],
                admins='[]',
                prefix='?',
                factions='[]',
                userstakeouts='[]',
                factionstakeouts='[]'
            )
            session.add(server)
            session.flush()

        self.sid = sid
        self.name = server.name
        self.admins = json.loads(server.admins)
        self.prefix = server.prefix

        self.factions = json.loads(server.factions)

        self.user_stakeouts = json.loads(server.userstakeouts)
        self.faction_stakeouts = json.loads(server.factionstakeouts)
