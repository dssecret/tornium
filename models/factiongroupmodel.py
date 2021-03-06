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


from mongoengine import DynamicDocument, IntField, StringField, ListField


class FactionGroupModel(DynamicDocument):
    tid = IntField(primary_key=True)
    name = StringField()
    creator = IntField()
    members = ListField()
    invite = StringField()

    sharestats = ListField(default=[])
