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
import random
import time

from gevent import monkey; monkey.patch_all()
from huey import crontab
import requests

from database import session_local
from models.factionmodel import FactionModel
from models.statmodel import StatModel
from models.user import User
from models.usermodel import UserModel, UserDiscordModel
from utils.tasks import tornget, huey, discordget
from utils import now
import utils


@huey.task(crontab(hour='1'))
def refresh_users():
    start = time.time()

    session = session_local()
    requests_session = requests.Session()
    users = []
    timestamp = now()

    for user in session.query(UserModel).all():
        if user.key == '':
            continue

        users.append(tornget(f'user/?selections=profile,battlestats,discord', user.key, session=requests_session))

    guilds = discordget('users/@me/guilds', session=requests_session)
    guilds = guilds.get()

    for user in users:
        try:
            user_data = user.get()
        except:
            continue
        user = session.query(UserModel).filter_by(tid=user_data['player_id']).first()
        user.factiontid = user_data['faction']['faction_id']
        user.name = user_data['name']
        user.last_refresh = timestamp
        user.status = user_data['last_action']['status']
        user.last_action = user_data['last_action']['relative']
        user.level = user_data['level']
        user.admin = False if user.tid != 2383326 else True
        user.discord_id = user_data['discord']['discordID']
        user.factiontid = user_data['faction']['faction_id']

        battlescore = math.sqrt(user_data['strength']) + math.sqrt(user_data['speed']) + \
                      math.sqrt(user_data['speed']) + math.sqrt(user_data['dexterity'])
        user.battlescore = json.dumps([battlescore, timestamp])

        discord_user = session.query(UserDiscordModel).filter_by(discord_id=user.discord_id).first()
        if discord_user is None:
            discord_user = UserDiscordModel(
                discord_id=user.discord_id,
                tid=user.tid
            )
            session.add(discord_user)
            session.flush()

        servers = []

        for guild in guilds:
            try:
                member = discordget(f'guilds/{guild["id"]}/members/{user.discord_id}', session=requests_session)
                member.get()
            except utils.DiscordError as e:
                if int(str(e)) == 10007:
                    break
                else:
                    return utils.handle_discord_error(int(str(e)))

            try:
                guild = discordget(f'guilds/{guild["id"]}', session=requests_session)
                guild = guild.get()
            except utils.DiscordError as e:
                return utils.handle_discord_error(int(str(e)))
            is_admin = False

            if guild['owner_id'] == user.discord_id:
                servers.append(guild['id'])
                is_admin = True
                break

            for role in member['roles']:
                for guild_role in guild['roles']:
                    # Checks if the user has the role and the role has the administrator permission
                    if guild_role['id'] == role and (int(guild_role['permissions']) & 0x0000000008) == 0x0000000008:
                        servers.append(guild['id'])
                        is_admin = True
                        break

                if is_admin:
                    break

        user.servers = json.dumps(servers)
        session.flush()
        utils.get_logger().debug(f'Users fetched in {time.time() - start} milliseconds.')


@huey.task(crontab(minute='5'))
def fetch_attacks():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    start = time.time()

    session = session_local()
    requests_session = requests.Session()
    faction_attacks = []
    timestamp = now()
    statid = session.query(StatModel).count()

    for faction in session.query(FactionModel).all():
        if len(json.loads(faction.keys)) == 0:
            continue

        faction_attacks.append(tornget('faction/?selections=basic,attacks',
                                       random.choice(json.loads(faction.keys)),
                                       tots=timestamp,
                                       fromts=timestamp - 300000,  # TODO: Adjust when the crontab timer is adjusted
                                       session=requests_session))  # TODO: Store last update per faction in DB

    for faction in faction_attacks:
        try:
            faction_data = faction.get()
        except:
            continue

        for attack in faction_data['attacks'].values():
            if attack['attacker_faction'] != faction_data['ID']:
                continue
            elif attack['result'] in ['Assist', 'Lost']:
                continue
            elif attack['defender_id'] in [4, 10, 15, 17, 19, 20, 21]:  # Checks if NPC fight (and you defeated NPC)
                continue

            try:
                if User(attack['attacker_id']).battlescore[1] - now() <= 10800000:  # Three hours
                    attacker_score = User(attack['attacker_id']).battlescore[0]
                else:
                    continue
            except IndexError:
                continue

            if attacker_score > 100000:
                continue

            defender_score = (attack['modifiers']['fair_fight'] - 1) * 0.375 * attacker_score
            stat_entry = StatModel(
                statid=statid,
                tid=attack['defender_id'],
                battlescore=defender_score,
                battlestats=json.dumps([0, 0, 0, 0]),
                timeadded=timestamp,
                addedid=attack['attacker_id']
            )
            session.add(stat_entry)
            statid += 1
        session.flush()
        utils.get_logger().debug(f'Attacks fetched in {time.time() - start} milliseconds.')
