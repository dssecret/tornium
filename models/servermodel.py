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
from sqlalchemy.dialects.mysql import BIGINT, TEXT, MEDIUMTEXT, TINYTEXT

from database import base
from models.settingsmodel import is_dev


class ServerModel(base):
    __tablename__ = 'Servers'

    if is_dev():
        sid = Column(Integer, primary_key=True)
        name = Column(String)
        admins = Column(String)  # String of list of admin ids
        prefix = Column(String)
        config = Column(String)  # String of dictionary of server configurations

        factions = Column(String)  # String of list of factions in server

        stakeoutconfig = Column(String)  # String of dictionary of stakeout configurations for the server
        userstakeouts = Column(String)  # String of list of staked-out users
        factionstakeouts = Column(String)  # String of list of staked-out factions
    else:
        sid = Column(BIGINT, primary_key=True)
        name = Column(TEXT)
        admins = Column(MEDIUMTEXT)  # String of list of admin ids
        prefix = Column(TINYTEXT)
        config = Column(TEXT)  # String of dictionary of server configurations

        factions = Column(MEDIUMTEXT)  # String of list of factions in server

        stakeoutconfig = Column(TEXT)  # String of dictionary of stakeout configurations for the server
        userstakeouts = Column(MEDIUMTEXT)  # String of list of staked-out users
        factionstakeouts = Column(MEDIUMTEXT)  # String of list of staked-out factions
