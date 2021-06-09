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

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class FactionModel(db.Model):
    tid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    respect = db.Column(db.Integer)
    capacity = db.Column(db.Integer)

    keys = db.Column(db.String)  # String of list of keys

    last_members = db.Column(db.Integer)  # Time of last members update
