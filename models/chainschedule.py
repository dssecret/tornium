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

from database import session_local
from chainschedulemodel import ChainScheduleModel


class ChainSchedule:
    def __init__(self, uuid, factiontid=None):
        session = session_local()
        schedule = session.query(ChainScheduleModel).filter_by(uuid=uuid).first()
        
        if schedule is None and factiontid is None:
            raise Exception
        elif schedule is None:
            scheudle = ChainScheduleModel(
                uuid=uuid,
                factiontid=factiontid
            )
            
            with open(f'schedule/{uuid}, 'w') as file:
                json.dump({
                    'uuid': uuid,
                    'factiontid': factiontid,
                    'activity': [],
                    'schedule': []
                }, file)
            
            session.add(schedule)
            session.flush()
        
        self.uuid = uuid
        self.factiontid = schedule.factiontid
        
        with open(f'schedule/{uuid}) as file:
            self.file = json.load(file)
        
        self.activity = self.file['activity']
        self.schedule = self.file['schedule']
