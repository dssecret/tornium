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

from flask_login import current_user

from database import session_local
from models.schedulemodel import ScheduleModel
import utils


# All timestamps refer to a 30 minute interval starting at that timestamp

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
                    'activity': {},
                    'weight': {},
                    'schedule': {}
                }, file, indent=4)
            
            session.add(schedule)
            session.flush()
        
        self.uuid = uuid
        self.factiontid = schedule.factiontid

        if current_user.factiontid != self.factiontid and factiontid != self.factiontid:
            raise Exception
        
        with open(f'{os.getcwd()}/schedule/{uuid}.json') as file:
            self.file = json.load(file)

        self.name = self.file['name']
        self.time_created = self.file['timecreated']
        self.time_updated = self.file['timeupdated']
        self.activity = self.file['activity']
        self.weight = self.file['weight']
        self.schedule = self.file['schedule']

    def add_activity(self, tid, activity=None):
        if activity is None:
            if tid in self.activity:
                raise Exception
            self.activity[tid] = []
        else:
            if tid in self.activity:
                self.activity[tid].append(activity)
            else:
                self.activity[tid] = [activity]

        self.update_file()

    def remove_user(self, tid):
        self.activity.pop(tid, None)
        self.weight.pop(tid, None)
        self.update_file()

    def set_weight(self, tid, weight):
        self.weight[tid] = weight
        self.update_file()

    def delete(self):
        session = session_local()
        schedule = session.query(ScheduleModel).filter_by(uuid=self.uuid).first()
        session.delete(schedule)

        if os.path.isfile(f'{os.getcwd()}/schedule/{self.uuid}.json'):
            os.remove(f'{os.getcwd()}/schedule/{self.uuid}.json')
        else:
            raise Exception

        session.flush()

    def update_file(self):
        self.file['name'] = self.name
        self.file['timecreated'] = self.time_created
        self.file['timeupdated'] = utils.now()
        self.file['activity'] = self.activity
        self.file['weight'] = self.weight
        self.file['schedule'] = self.schedule

        with open(f'{os.getcwd()}/schedule/{self.uuid}.json', 'w') as file:
            json.dump(self.file, file, indent=4)
