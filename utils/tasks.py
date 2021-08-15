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

from huey import SqliteHuey, crontab
import requests

from database import session_local
from models import settingsmodel
from models.factionmodel import FactionModel
from models.statmodel import StatModel
from models.usermodel import UserModel, UserDiscordModel
import utils

huey = SqliteHuey()


@huey.task()
def tornget(endpoint, key, tots=0, fromts=0, session=None):
    url = f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}' \
          f'{"" if tots == 0 else f"&to={tots}"}'

    if session is None:  # Utilizes https://docs.python-requests.org/en/latest/user/advanced/#session-objects
        request = requests.get(url)
    else:
        request = session.get(url)

    if request.status_code != 200:
        utils.get_logger().warning(f'The Torn API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    request = request.json()

    if 'error' in request:
        utils.get_logger().info(f'The Torn API has responded with error code {request["error"]["code"]} '
                                f'({request["error"]["error"]}) to {endpoint}).')
        raise utils.TornError(request["error"]["code"])

    return request


@huey.task()
def discordget(endpoint, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'

    if session is None:
        request = requests.get(url, headers={'Authorization': f'Bot {settingsmodel.get("settings", "bottoken")}'})
    else:
        request = session.get(url, headers={'Authorization': f'Bot {settingsmodel.get("settings", "bottoken")}'})

    request_json = request.json()

    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a fill list of error code
        # explanations

        utils.get_logger().info(f'The Discord API has responded with error code {request_json["code"]} '
                                f'({request_json["message"]}) to {url}).')
        raise utils.DiscordError(request_json["code"])

    if request.status_code != 200:
        utils.get_logger().warning(f'The Discord API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    return request_json


@huey.periodic_task(crontab(hour='1'))
def refresh_users():
    utils.get_logger().debug('Refresh Users started.')
    start = time.time()

    session = session_local()
    requests_session = requests.Session()
    users = []
    timestamp = utils.now()

    for user in session.query(UserModel).all():
        if user.key == '':
            continue

        users.append(tornget(f'user/?selections=profile,battlestats,discord', user.key, session=requests_session))

    guilds = discordget('users/@me/guilds', session=requests_session)
    guilds = guilds()

    for user in users:
        try:
            user_data = user(blocking=True)
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
                member()
            except utils.DiscordError as e:
                if int(str(e)) == 10007:
                    break
                else:
                    return utils.handle_discord_error(int(str(e)))

            try:
                guild = discordget(f'guilds/{guild["id"]}', session=requests_session)
                guild = guild()
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


@huey.periodic_task(crontab(minute='5'))
def fetch_attacks():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    utils.get_logger().debug('Fetch attacks started.')
    start = time.time()

    session = session_local()
    requests_session = requests.Session()
    faction_attacks = []
    timestamp = utils.now()
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
            faction_data = faction(blocking=True)
        except:
            continue

        for attack in faction_data['attacks'].values():
            if attack['attacker_faction'] != faction_data['ID']:
                continue
            elif attack['result'] in ['Assist', 'Lost']:
                continue
            elif attack['defender_id'] in [4, 10, 15, 17, 19, 20, 21]:  # Checks if NPC fight (and you defeated NPC)
                continue

            user = session.query(UserModel).filter_by(tid=attack['attacker_id']).first()

            try:
                if json.loads(user.battlescore)[1] - utils.now() <= 10800000:  # Three hours
                    attacker_score = json.loads(user.battlescore)[0]
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


@huey.periodic_task(crontab(minute='1'))
def test():
    utils.get_logger().debug('test')
