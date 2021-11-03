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

from mongoengine import DynamicDocument, IntField, StringField, DictField, ListField


class ServerModel(DynamicDocument):
    sid = IntField(primary_key=True)
    name = StringField()
    admins = ListField(IntField)  # List of admin ids
    prefix = StringField()
    config = DictField()  # Dictionary of server configurations

    factions = ListField(IntField)  # List of factions in server

    stakeoutconfig = DictField()  # Dictionary of stakeout configurations for the server
    userstakeouts = ListField(IntField)  # List of staked-out users
    factionstakeouts = ListField(IntField)  # List of staked-out factions
