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

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, TEXT, BIT, VARCHAR, MEDIUMTEXT

from database import base
from redisdb import get_redis


class UserModel(base):
    __tablename__ = 'Users'

    if get_redis().get('dev'):
        tid = Column(Integer, primary_key=True)
        name = Column(String)
        level = Column(Integer)
        last_refresh = Column(Integer)
        admin = Column(Boolean)
        key = Column(String(16))
        battlescore = Column(String)  # String of list of battlescore, last update timestamp

        discord_id = Column(Integer)
        servers = Column(String)  # String of list of discord servers where user is admin

        factionid = Column(Integer)
        factionaa = Column(Boolean)

        status = Column(String)
        last_action = Column(String)
    else:
        tid = Column(INTEGER, primary_key=True)
        name = Column(TEXT)
        level = Column(INTEGER)
        last_refresh = Column(INTEGER)
        admin = Column(BIT(1))
        key = Column(VARCHAR(16))
        battlescore = Column(MEDIUMTEXT)  # String of list of battlescore, last update timestamp

        discord_id = Column(BIGINT)
        servers = Column(MEDIUMTEXT)  # String of list of discord servers where user is admin

        factionid = Column(INTEGER)
        factionaa = Column(BIT(1))

        status = Column(TEXT)
        last_action = Column(TEXT)


class UserDiscordModel(base):
    __tablename__ = 'DiscordUsers'

    if get_redis().get('dev'):
        discord_id = Column(Integer, primary_key=True)
        tid = Column(Integer)
    else:
        discord_id = Column(BIGINT, primary_key=True)
        tid = Column(INTEGER)
