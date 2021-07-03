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
import random

from flask_login import current_user

from database import session_local
from models.factionmodel import FactionModel
from models.server import Server
from models.user import User
import utils
from utils.tornget import tornget


class Faction:
    def __init__(self, tid, key=""):
        """
        Retrieves the faction from the database.

        :param tid: Torn faction ID
        :param key: Torn API Key to be utilized (uses current user's key if not passed)
        """

        session = session_local()
        faction = session.query(FactionModel).filter_by(tid=tid).first()
        if faction is None:
            faction_data = tornget(f'faction/{tid}?selections=basic', key if key != "" else current_user.key)
            now = utils.now()

            faction = FactionModel(
                tid=tid,
                name=faction_data['name'],
                respect=faction_data['respect'],
                capacity=faction_data['capacity'],
                keys='[]',
                last_members=now,
                withdrawals='[]',
                guild=0,
                vaultconfig='{"banking": 0, "banker": 0}'
            )

            try:
                tornget(f'faction/{tid}?selections=positions', key if key != "" else current_user.key)
                keys = json.loads(faction.keys)
                keys.append(key if key != "" else current_user.key)
                keys = json.dumps(keys)
                faction.keys = keys
            except utils.TornError:
                pass

            session.add(faction)

        self.tid = tid
        self.name = faction.name
        self.respect = faction.respect
        self.capacity = faction.capacity
        self.keys = json.loads(faction.keys)
        self.last_members = faction.last_members
        self.withdrawals = json.loads(faction.withdrawals)
        self.guild = faction.guild
        self.vault_config = json.loads(faction.vaultconfig)

    def get_tid(self):
        """
        Returns the faction's game ID
        """
        return self.tid

    def get_keys(self):
        return self.keys

    def rand_key(self):
        return random.choice(self.keys)

    def update_members(self, force=False, key=None):
        now = utils.now()

        if not force and (now - self.last_members) < 1800:
            utils.get_logger().info(f'Update members skipped since last update was at {self.last_members} and update '
                                    f'was not forced.')
            return

        if key is None:
            key = random.choice(self.get_keys())

        factionmembers = tornget('faction/?selections=', key)

        for memberid, member in factionmembers['members'].values():
            user = User(memberid)

            if key is None:
                key = random.choice(self.get_keys())
            user.refresh(key, force)

    def get_vault_config(self):
        if self.guild == 0:
            return {}

        server = Server(self.guild)
        if self.tid not in server.factions:
            raise Exception  # TODO: Make exception more descriptive

        return self.vault_config

