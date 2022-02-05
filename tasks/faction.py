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

import datetime
import logging
import random
from shutil import ExecError
from urllib import request

import honeybadger
import requests

from models.factionmodel import FactionModel
from models.usermodel import UserModel
from tasks import celery_app, discordpost, logger, tornget
import utils

logger: logging.Logger


@celery_app.task
def refresh_factions():
    requests_session = requests.Session()

    faction: FactionModel
    for faction in FactionModel.objects():
        if len(faction.keys) == 0:
            continue

        try:
            faction_data = tornget.delay(
                'faction/?selections=',
                key=random.choice(faction.keys),
                session=requests_session
            )
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        if faction_data is None:
            continue

        faction = utils.first(FactionModel.objects(tid=faction.tid))
        faction.name = faction_data['name']
        faction.respect = faction_data['respect']
        faction.capacity = faction_data['capacity']
        faction.leader = faction_data['leader']
        faction.coleader = faction_data['co-leader']
        faction.last_members = utils.now()
        faction.save()

        keys = []

        leader = utils.first(UserModel.objects(tid=faction.leader))
        coleader = utils.first(UserModel.objects(tid=faction.coleader))

        if leader is not None and leader.key != '':
            keys.append(leader.key)
        if coleader is not None and coleader.key != '':
            keys.append(coleader.key)

        if faction.chainconfig['od'] == 1:
            try:
                faction_od = tornget.delay(
                    'faction/?selections=contributors',
                    stat='drugoverdoses',
                    key=random.choice(faction.keys),
                    session=requests_session
                )
            except Exception as e:
                logger.exception(e)
                continue
            
            if len(faction.chainod) > 0:
                for tid, user_od in faction_od['contributors']['drugoverdoses'].items():
                    if user_od != faction.chainod.get(tid):
                        overdosed_user = utils.first(UserModel.objects(tid=tid))
                        payload = {
                            'embeds': [
                                {
                                    'title': 'User Overdose',
                                    'description': f'User {tid if overdosed_user is None else overdosed_user.name} of '
                                                   f'faction {faction.name} has overdosed.',
                                    'timestamp': datetime.datetime.utcnow().isoformat(),
                                    'footer': {
                                        'text': utils.torn_timestamp()
                                    }
                                }
                            ]
                        }

                        try:
                            discordpost.delay(
                                f'channels/{faction.chainconfig["odchannel"]}/messages',
                                payload=payload
                            )
                        except Exception as e:
                            logger.exception(e)
                            honeybadger.notify(e)
                            continue
            
            faction.chainod = faction_od['contributors']['drugoverdoses']
        
        faction.save()
