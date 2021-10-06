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
import os

from database import session_local
from models.schedulemodal import ScheduleModel
import utils


class Schedule:
    def __init__(self, uuid, factiontid=None):
        session = session_local()
        schedule = session.query(ScheduleModel).filter_by(uuid=uuid).first()
        
        if schedule is None and factiontid is None:
            raise Exception
        elif schedule is None:
            schedule = ScheduleModel(
                uuid=uuid,
                factiontid=factiontid
            )

            if not os.path.exists(f'{os.getcwd()}/schedule'):
                os.makedirs(f'{os.getcwd()}/schedule')
            
            with open(f'{os.getcwd()}/schedule/{uuid}.json', 'x') as file:
                json.dump({
                    'uuid': uuid,
                    'name': uuid,
                    'factiontid': factiontid,
                    'timecreated': utils.now(),
                    'timeupdated': utils.now(),
                    'activity': [],
                    'schedule': []
                }, file)
            
            session.add(schedule)
            session.flush()
        
        self.uuid = uuid
        self.factiontid = schedule.factiontid
        
        with open(f'{os.getcwd()}/schedule/{uuid}.json') as file:
            self.file = json.load(file)

        self.name = self.file['name']
        self.time_created = self.file['timecreated']
        self.time_updated = self.file['timeupdated']
        self.activity = self.file['activity']
        self.schedule = self.file['schedule']
