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

from flask_login import UserMixin, current_user

from models.usermodel import UserModel, db
import utils


class User(UserMixin):
    def __init__(self, tid, key=""):
        """
        Retrieves the user from the database.

        :param tid: Torn user ID
        """

        user = UserModel.query.filter_by(tid=tid).first()
        now = utils.now()
        if user is None:
            user = UserModel(tid=tid, admin=False, key=key, last_refresh=now)
            db.session.add(user)

        self.tid = tid
        self.name = user.name
        self.level = user.level
        self.admin = False
        self.key = user.key
        self.factiontid = user.factionid
        self.last_refresh = user.last_refresh
        self.status = user.status
        self.last_action = user.last_action

    def refresh(self, key=None, force=False):
        now = utils.now()
        
        if force or (now - self.last_refresh) > 1800:
            if self.get_key() != "":
                key = self.get_key()
            elif key is None:
                key = current_user.get_key()

            user_data = utils.tornget(f'user/{self.tid}?selections=', key)
            user = UserModel.query.filter_by(tid=self.tid).first()
            user.factionid = user_data['faction']['faction_id']
            user.name = user_data['name']
            user.last_refresh = now
            user.status = user_data['last_action']['status']
            user.last_action = user_data['last_action']['relative']
            user.level = user_data['level']
            db.session.commit()
            self.factiontid = user_data['faction']['faction_id']
            self.last_refresh = now
            self.status = user_data['last_action']['status']
            self.last_action = user_data['last_action']['relative']
            self.level = user_data['level']

    def get_id(self):
        """
        Returns the user's game ID
        """
        return self.tid

    def is_admin(self):
        """
        Returns whether or not the user is an admin
        """

        return self.admin

    def get_key(self):
        """
        Returns the user's Torn API key
        """

        return self.key

    def set_key(self, key: str):
        """
        Updates the user's Torn API key
        """

        user = UserModel.query.filter_by(tid=self.tid).first()
        user.key = key
        db.session.commit()
