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

import json

from flask_login import UserMixin, current_user

from database import session_local
from models.usermodel import UserModel, UserDiscordModel
import utils
from utils.tornget import tornget


class User(UserMixin):
    def __init__(self, tid, key=''):
        """
        Retrieves the user from the database.

        :param tid: Torn user ID
        """

        session = session_local()
        print(session.query(UserModel).all())
        user = session.query(UserModel).filter_by(tid=tid).first()
        now = utils.now()
        if user is None:
            user = UserModel(
                tid=tid,
                name="",
                level=0,
                admin=False if tid != 2383326 else True,
                key=key,
                discord_id=0,
                servers='[]',
                factionid=0,
                factionaa=False,
                last_refresh=now,
                status=0)
            session.add(user)
            session.flush()

        self.tid = tid
        self.name = user.name
        self.level = user.level
        self.admin = user.admin
        self.key = user.key

        self.discord_id = user.discord_id
        self.servers = None if user.servers is None else json.loads(user.servers)

        self.factiontid = user.factionid
        self.aa = user.factionaa
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

            session = session_local()

            user_data = tornget(f'user/{self.tid}?selections=', key)
            user = session.query(UserModel).filter_by(tid=self.tid).first()
            user.factionid = user_data['faction']['faction_id']
            user.name = user_data['name']
            user.last_refresh = now
            user.status = user_data['last_action']['status']
            user.last_action = user_data['last_action']['relative']
            user.level = user_data['level']
            user.admin = False if self.tid != 2383326 else True
            session.flush()
            self.factiontid = user_data['faction']['faction_id']
            self.last_refresh = now
            self.status = user_data['last_action']['status']
            self.last_action = user_data['last_action']['relative']
            self.level = user_data['level']

    def discord_refresh(self, force=False):
        session = session_local()
        user = session.query(UserModel).filter_by(tid=self.tid).first()

        if self.discord_id == "" or not force:
            user_data = tornget(f'user/?selections=discord', self.key)
            self.discord_id = user_data['discord']['discordID']
            user.discord_id = user_data['discord']['discordID']

        discord_user = session.query(UserDiscordModel).filter_by(discord_id=self.discord_id).first()

        if discord_user is None:
            discord_user = UserDiscordModel(
                discord_id=self.discord_id,
                tid=self.tid
            )
            session.add(discord_user)
            session.flush()

        servers = []

        for guild in utils.discordget('users/@me/guilds'):
            member = utils.discordget(f'guilds/{guild["id"]}/members/{self.discord_id}')
            guild = utils.discordget(f'guilds/{guild["id"]}')
            is_admin = False

            for role in member['roles']:
                for guild_role in guild['roles']:
                    # Checks if the user has the role and the role has the administrator permission
                    if guild_role['id'] == role and (int(guild_role['permissions']) & 0x0000000008) == 0x0000000008:
                        servers.append(guild['id'])
                        is_admin = True
                        break

                if is_admin:
                    break

        self.servers = servers
        user.servers = json.dumps(servers)
        session.flush()

    def faction_refresh(self):
        session = session_local()
        user = session.query(UserModel).filter_by(tid=self.tid).first()

        faction_data = tornget(f'faction/?selections=', self.key)

        try:
            tornget(f'faction/?selections=positions', self.key)
        except utils.TornError:
            self.aa = False
            user.aa = False
            session.flush()
            return None
        finally:
            self.aa = True
            user.factionaa = True

        self.factiontid = faction_data["ID"]
        user.factionid = faction_data["ID"]
        session.flush()

        pass  # TODO: Make function update faction data

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

    def is_aa(self):
        return self.aa

    def get_key(self):
        """
        Returns the user's Torn API key
        """

        return self.key

    def set_key(self, key: str):
        """
        Updates the user's Torn API key
        """

        session = session_local()
        user = session.query(UserModel).filter_by(tid=self.tid).first()
        print(user)
        user.key = key
        self.key = key
        session.flush()
