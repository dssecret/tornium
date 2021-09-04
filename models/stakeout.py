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

from flask_login import current_user

from database import session_local
from models.factionstakeoutmodel import FactionStakeoutModel
from models.userstakeoutmodel import UserStakeoutModel
import utils
from utils.tasks import tornget


class Stakeout:
    def __init__(self, tid, guild=None, user=True, key=''):
        session = session_local()
        stakeout = session.query(UserStakeoutModel if user else FactionStakeoutModel).filter_by(tid=tid).first()

        if stakeout is None:
            now = utils.now()
            guilds = {} if guild is None else {guild: {'keys': [], 'channel': 0}}

            if user:
                try:
                    data = tornget(f'user/{tid}?selections=basic', key if key != '' else current_user.key)
                    data = data(blocking=True)
                except:
                    data = '{}'

                stakeout = UserStakeoutModel(
                    tid=tid,
                    data=json.dumps(data),
                    guilds=json.dumps(guilds),
                    lastupdate=now
                )

            else:
                try:
                    data = tornget(f'faction/{tid}?selections=basic', key if key != '' else current_user.key)
                    data = data(blocking=True)
                except:
                    data = '{}'

                stakeout = FactionStakeoutModel(
                    tid=tid,
                    data=json.dumps(data),
                    guilds=json.dumps(guilds),
                    lastupdate=now
                )

            session.add(stakeout)
            session.flush()
        elif guild not in json.loads(stakeout.guilds) and guild is not None:
            guilds = json.loads(stakeout.guilds)
            guilds[guild] = {
                'keys': [],
                'channel': 0
            }
            stakeout.guilds = json.dumps(guilds)
            session.flush()

        self.tid = tid
        self.stype = 0 if user else 1  # 0 = user; 1 = faction
        self.guilds = json.loads(stakeout.guilds)
        self.last_update = stakeout.lastupdate
        self.data = json.loads(stakeout.data)
