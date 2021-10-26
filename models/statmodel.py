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

from sqlalchemy import Column, Integer, Float, String, Boolean
from sqlalchemy.dialects.mysql import INTEGER, FLOAT, TEXT, BOOLEAN

from database import base
from redisdb import get_redis


class StatModel(base):
    __tablename__ = 'Stats'

    if get_redis().get('dev'):
        statid = Column(Integer, primary_key=True)
        tid = Column(Integer)
        battlescore = Column(Float)
        timeadded = Column(Integer)
        addedid = Column(Integer)
        addedfactiontid = Column(Integer)
        globalstat = Column(Boolean)
    else:
        statid = Column(INTEGER, primary_key=True)
        tid = Column(INTEGER)
        battlescore = Column(FLOAT)
        timeadded = Column(INTEGER)
        addedid = Column(INTEGER)
        addedfactiontid = Column(INTEGER)
        globalstat = Column(BOOLEAN)
