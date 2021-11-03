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


class FactionModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField()
    respect = IntField()
    capacity = IntField()
    leader = IntField()
    coleader = IntField()

    keys = ListField(StringField(min_length=16, max_length=16))  # String of list of keys

    last_members = IntField()  # Time of last members update

    guild = IntField()  # Guild ID of the faction's guild
    config = DictField()  # Dictionary of faction's bot configuration
    vaultconfig = DictField()  # Dictionary of vault configuration

    targets = DictField()  # Dictionary of targets

    statconfig = DictField()  # Dictionary of target config

    chainconfig = DictField()  # Dictionary of chain config
    chainod = DictField()  # Dictionary of faction member overdoses
