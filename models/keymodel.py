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
from sqlalchemy.dialects.mysql import VARCHAR, BIGINT, MEDIUMTEXT

from database import base
from models.settingsmodel import is_dev


class KeyModel(base):
    __tablename__ = 'Keys'

    if is_dev():
        key = Column(String, primary_key=True)
        ownertid = Column(Integer)
        scopes = Column(String)  # String of list of scopes
    else:
        key = Column(VARCHAR(70), primary_key=True)
        ownertid = Column(BIGINT)
        scopes = Column(MEDIUMTEXT)  # String of list of scopes
