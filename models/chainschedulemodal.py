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
from sqlalchemy.dialects.mysql import BIGINT, INTEGER

from database import base
from models.settingsmodel import is_dev


class SchedulesModel(base):
    __tablename__ = 'Schedules'

    if is_dev():
        uuid = Column(Integer, primary_key=True)
        factiontid = Column(Integer)
    else:
        uuid = Column(BIGINT, primary_key=True)
        factiontid = Column(INTEGER)
        
        