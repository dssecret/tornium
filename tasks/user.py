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

import math

from honeybadger import honeybadger
import requests

from models.factionmodel import FactionModel
from models.factiongroupmodel import FactionGroupModel
from models.statmodel import StatModel
from models.usermodel import UserModel
from tasks import celery_app, logger, tornget
import utils


@celery_app.task
def refresh_users():
    requests_session = requests.Session()

    user: UserModel
    for user in UserModel.objects(key__ne=''):
        if user.key == '':
            continue

        try:
            user_data = tornget(f'user/?selections=profile,battlestats,discord', user.key, session=requests_session)
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        user.factionid = user_data['faction']['faction_id']
        user.name = user_data['name']
        user.last_refresh = utils.now()
        user.status = user_data['last_action']['status']
        user.last_action = user_data['last_action']['timestamp']
        user.level = user_data['level']
        user.discord_id = user_data['discord']['discordID'] if user_data['discord']['discordID'] != '' else 0
        user.strength = user_data['strength']
        user.defense = user_data['defense']
        user.speed = user_data['speed']
        user.dexterity = user_data['dexterity']

        battlescore = math.sqrt(user_data['strength']) + math.sqrt(user_data['defense']) + \
                      math.sqrt(user_data['speed']) + math.sqrt(user_data['dexterity'])
        user.battlescore = battlescore
        user.battlescore_update = utils.now()
        user.save()

        if user.factionid != 0:
            faction: FactionModel = utils.first(FactionModel.objects(tid=user.factionid))

            if faction is None:
                faction = FactionModel(
                    tid=user.factionid,
                    name=user_data['faction']['faction_name']
                )
                faction.save()

            try:
                tornget(f'faction/?selections=positions', user.key, session=requests_session)
            except utils.TornError as e:
                if e.code != 7:
                    logger.exception(e)
                    honeybadger.notify(e)
                    continue
                else:
                    if user.factionaa:
                        user.factionaa = False
                        user.save()

                    continue
            except Exception as e:
                logger.exception(e)
                honeybadger.notify(e)

                if user.factionaa:
                    user.factionaa = False
                    user.save()

                continue

            user.factionaa = True
            user.save()
        else:
            user.factionaa = False
            user.save()


@celery_app.task
def fetch_attacks_users():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    requests_session = requests.Session()

    try:
        last_timestamp = utils.last(StatModel.objects()).timeadded
    except AttributeError:
        last_timestamp = 0

    faction_shares = {}

    group: FactionGroupModel
    for group in FactionGroupModel.objects():
        for member in group.sharestats:
            if str(member) in faction_shares:
                faction_shares[str(member)].extend(group.members)
            else:
                faction_shares[str(member)] = group.members

    for factiontid, shares in faction_shares.items():
        faction_shares[factiontid] = list(set(shares))

    user: UserModel
    for user in UserModel.objects(key__ne=''):
        if user.key == '':
            continue

        faction: FactionModel = utils.first(FactionModel.objects(tid=user.factionid))

        if faction is not None and len(faction.keys) != 0:
            continue
        elif faction is not None and faction.config['stats'] == 1:
            continue

        try:
            user_data = tornget('user/?selections=basic,attacks', key=user.key, session=requests_session)
        except Exception as e:
            logger.exception(e)
            honeybadger.notify(e)
            continue

        for attack in user_data['attacks'].values():
            if attack['defender_faction'] == user.factionid and user.factionid != 0:
                continue
            elif attack['result'] in ['Assist', 'Lost', 'Stalemate', 'Escape']:
                continue
            elif attack['defender_id'] in [4, 10, 15, 17, 19, 20, 21]:  # Checks if NPC fight (and you defeated NPC)
                continue
            elif attack['modifiers']['fair_fight'] == 3:  # 3x FF can be greater than the defender battlescore indicated
                continue
            elif attack['timestamp_ended'] < last_timestamp:
                continue

            try:
                if user.battlescore_update - utils.now() <= 10800000:  # Three hours
                    attacker_score = user.battlescore
                else:
                    continue
            except IndexError:
                continue

            if attacker_score > 100000:
                continue

            defender_score = (attack['modifiers']['fair_fight'] - 1) * 0.375 * attacker_score

            if defender_score == 0:
                continue

            if faction is None:
                globalstat = 1

                if user.factionid == 0:
                    allowed_factions = []
                else:
                    allowed_factions = [user.factionid]
            else:
                globalstat = faction.statconfig['global']
                allowed_factions = [faction.tid]

                if str(faction.tid) in faction_shares:
                    allowed_factions.extend(faction_shares[str(faction.tid)])

                allowed_factions = list(set(allowed_factions))

            stat_entry = StatModel(
                statid=utils.last(StatModel.objects()).statid + 1 if StatModel.objects().count() != 0 else 0,
                tid=attack['defender_id'],
                battlescore=defender_score,
                timeadded=utils.now(),
                addedid=attack['attacker_id'],
                addedfactiontid=user.factionid,
                globalstat=globalstat,
                allowedfactions=allowed_factions
            )
            stat_entry.save()
