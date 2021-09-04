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


class UserStakeoutModel(base):
    __tablename__ = 'UserStakeouts'

    tid = Column(Integer, primary_key=True)  # The user ID of the stakeout
    data = Column(String)  # String of data from the Torn API
    guilds = Column(String)  # String of list of guilds to be watched
    lastupdate = Column(Integer)
