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
import math
import os

from flask_login import current_user

from database import session_local
from models.schedulemodel import ScheduleModel
from models.user import User
import utils


# 10-12 refers to starting at 10 ending at 12 or [10, 12) mathematically

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
                    'schedule': {},
                    'from': 0,
                    'to': 0
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
        self.fromts = self.file['from']
        self.tots = self.file['to']

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
        self.file['from'] = self.fromts
        self.file['to'] = self.tots

        with open(f'{os.getcwd()}/schedule/{self.uuid}.json', 'w') as file:
            json.dump(self.file, file, indent=4)

    def __calculate_weight(self, interval, tid):
        start = int(interval.split('-')[0])
        end = int(interval.split('-')[1])

        experience = math.log10(User(tid).chain_hits)  # TODO: Add support in tasks
        length = (end - start) / 3600
        normal_weight = math.pow(math.e, (- (length - 2) ** 2)/(2 * 0.5 ** 2))/(0.5 * math.sqrt(2 * math.pi))
        return experience * self.weight[tid] * normal_weight

    def greedy(self):
        interval = ''
        user = 0
        max_weight = 0

        for user in self.activity:
            for activity in user:
                if (max_weight == 0 or activity.split('-')[0] <= interval.split('-')[0]) and \
                        self.__calculate_weight(activity, user) > max_weight:
                    interval = activity
                    max_weight = self.__calculate_weight(activity, user)
                    user = user

        schedule = [[interval, user]]

    def annealing(self):
        pass

    def generate(self, tots, fromts, version='annealing'):
        pass
