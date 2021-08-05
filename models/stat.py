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

from database import session_local
from models.statmodel import StatModel
import utils


class Stat:
    def __init__(self, tid, index=0):
        session = session_local()
        spy = session.query(StatModel).filter_by(tid=tid).all()[index]

        self.tid = spy.tid
        self.battlescore = spy.battlescore
        self.battlestats = json.loads(spy.battlestats)
        self.level = spy.level
        self.timeadded = spy.timeadded
        self.addedid = spy.addedid


# def mkspy(tid, level, addertid, battlescore=None, battlestats=None):
#     session = session_local
#     spy = SpyModel(
#         tid=tid,
#         battlescore=battlescore,
#         battlestats=json.dumps(battlestats),
#         level=level,
#         timeadded=utils.now(),
#         addedid=addertid
#     )
#     session.add(spy)
#     session.flush()
#
#     return Spy(tid, index=-1)
