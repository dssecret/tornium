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

from sqlalchemy import Column, Integer, String
from database import base


class ServerModel(base):
    __tablename__ = 'Servers'

    sid = Column(Integer, primary_key=True)
    name = Column(String)
    admins = Column(String)  # String of list of admin ids
    prefix = Column(String)

    factions = Column(String)  # String of list of factions in server
