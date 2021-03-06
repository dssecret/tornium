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

import random

from flask_login import current_user
from mongoengine.queryset.visitor import Q

from models.factionmodel import FactionModel
from models.server import Server
from models.usermodel import UserModel
import tasks
import utils


class Faction:
    def __init__(self, tid, key=""):
        """
        Retrieves the faction from the database.

        :param tid: Torn faction ID
        :param key: Torn API Key to be utilized (uses current user's key if not passed)
        """

        faction = utils.first(FactionModel.objects(tid=tid))
        if faction is None:
            faction_data = tasks.tornget(f'faction/{tid}?selections=basic', key if key != "" else current_user.key)
            now = utils.now()

            faction = FactionModel(
                tid=tid,
                name=faction_data['name'],
                respect=faction_data['respect'],
                capacity=faction_data['capacity'],
                leader=faction_data['leader'],
                coleader=faction_data['co-leader'],
                last_members=now,
                guild=0,
                config={'vault': 0, 'stats': 1},
                vaultconfig={'banking': 0, 'banker': 0, 'withdrawal': 0},
                statconfig={'global': 0},
                chainconfig={'od': 0, 'odchannel': 0},
                chainod={}
            )

            try:
                tasks.tornget(f'faction/{tid}?selections=positions', key if key != "" else current_user.key)
            except:
                pass

            faction.save()

        self.tid = tid
        self.name = faction.name
        self.respect = faction.respect
        self.capacity = faction.capacity
        self.leader = faction.leader
        self.coleader = faction.coleader

        self.last_members = faction.last_members

        self.guild = faction.guild
        self.config = faction.config
        self.vault_config = faction.vaultconfig

        self.stat_config = faction.statconfig

        self.chain_config = faction.chainconfig
        self.chain_od = faction.chainod

        self.groups = faction.groups

    def rand_key(self):
        users = UserModel.objects(Q(factionaa=True) & Q(factionid=self.tid) & Q(key__ne=''))
        keys = []

        for user in users:
            if user.key == '':
                continue

            keys.append(user.key)

        keys = list(set(keys))
        return random.choice(keys)

    def get_config(self):
        if self.guild == 0:
            return {'vault': 0, 'stats': 1}

        server = Server(self.guild)
        if self.tid not in server.factions:
            raise Exception  # TODO: Make exception more descriptive

        return self.config
