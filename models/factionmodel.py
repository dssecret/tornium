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

from sqlalchemy import Column, Integer, String
from database import base


class FactionModel(base):
    __tablename__ = 'Factions'

    tid = Column(Integer, primary_key=True)
    name = Column(String)
    respect = Column(Integer)
    capacity = Column(Integer)
    leader = Column(Integer)
    coleader = Column(Integer)

    keys = Column(String)  # String of list of keys

    last_members = Column(Integer)  # Time of last members update

    withdrawals = Column(String)  # String of list of dictionary of requests

    guild = Column(Integer)  # Guild ID of the faction's guild
    config = Column(String)  # String of dictionary of faction's bot configuration
    vaultconfig = Column(String)  # String of dictionary of vault configuration

    targets = Column(String)  # String of dictionary of targets

    statconfig = Column(String)  # String of dictionary of target config
