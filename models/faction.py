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

import ast
import random

from flask_login import current_user

from models.factionmodel import FactionModel, db
from models.user import User
import utils


class Faction:
    def __init__(self, tid):
        """
        Retrieves the faction from the database.

        :param tid: Torn faction ID
        """

        faction = FactionModel.query.filter_by(tid=tid).first()
        if faction is None:
            faction_data = utils.tornget('/faction/?selections=basic,positions', current_user.key)
            now = utils.now()

            faction = FactionModel(
                tid=tid,
                name=faction_data['name'],
                respect=faction_data['respect'],
                capacity=faction_data['capacity'],
                keys='[]',
                last_members=now
            )

            position = faction_data['members'][str(current_user.get_id())]['position']
            if faction_data['positions'][position]['canAccessFactionApi'] == 1:
                faction.keys = str(ast.literal_eval(faction.keys).append(current_user.get_key()))

            db.session.add(faction)

        self.tid = tid
        self.name = faction.name
        self.respect = faction.respect
        self.capacity = faction.capacity
        self.keys = ast.literal_eval(faction.keys)
        self.last_members = faction.last_members

    def get_tid(self):
        """
        Returns the faction's game ID
        """
        return self.tid

    def get_keys(self):
        return self.keys

    def update_members(self, force=False, key=None):

        now = utils.now()

        if not force and (now - self.last_members) < 1800:
            utils.get_logger().info(f'Update members skipped since last update was at {self.last_members} and update '
                                    f'was not forced.')
            return

        if key is None:
            key = random.choice(self.get_keys())

        factionmembers = utils.tornget('faction/?selections=', key)

        for memberid, member in factionmembers['members'].values():
            user = User(memberid)

            if key is None:
                key = random.choice(self.get_keys())
            user.refresh(key, force)

