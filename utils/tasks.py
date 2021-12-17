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
import json
import math
import os
import random
import time

from huey import SqliteHuey, RedisHuey, crontab
from mongoengine import connect
import requests

from redisdb import get_redis

try:
    file = open('settings.json')
    file.close()
except FileNotFoundError:
    data = {
        'jsonfiles': ['settings'],
        'dev': False,
        'bottoken': '',
        'secret': str(os.urandom(32)),
        'taskqueue': 'redis',
        'username': 'tornium',
        'password': '',
        'host': ''
    }
    with open(f'settings.json', 'w') as file:
        json.dump(data, file, indent=4)

with open('settings.json', 'r') as file:
    data = json.load(file)

redis = get_redis()
redis.set('dev', str(data['dev']))
redis.set('bottoken', data['bottoken'])
redis.set('secret', data['secret'])
redis.set('taskqueue', data['taskqueue'])
redis.set('username', data['username'])
redis.set('password', data['password'])
redis.set('host', data['host'])

connect(
    db='Tornium',
    username=redis.get('username'),
    password=redis.get('password'),
    host=f'mongodb://{redis.get("host")}',
    connect=False
)

from models.factionmodel import FactionModel
from models.factionstakeoutmodel import FactionStakeoutModel
from models.servermodel import ServerModel
from models.statmodel import StatModel
from models.usermodel import UserModel
from models.userstakeoutmodel import UserStakeoutModel
import utils

if redis.get('taskqueue') == 'sqlite':
    huey = SqliteHuey()
else:
    huey = RedisHuey(host='localhost', port=6379)


@huey.task()
def tornget(endpoint, key, tots=0, fromts=0, stat='', session=None):
    url = f'https://api.torn.com/{endpoint}&key={key}&comment=Tornium{"" if fromts == 0 else f"&from={fromts}"}' \
          f'{"" if tots == 0 else f"&to={tots}"}{stat if stat == "" else f"stat={stat}"}'
    utils.get_logger().info(f'The API call has been made to {url}).')

    if key is None or key == '':
        raise Exception

    redis = get_redis()
    if redis.setnx(key, 100):
        redis.expire(key, 60 - datetime.datetime.utcnow().second)
    if redis.ttl(key) < 0:
        redis.expire(key, 1)

    try:
        if redis.get(key) and int(redis.get(key)) > 0:
            redis.decrby(key, 1)
        else:
            time.sleep(60 - datetime.datetime.utcnow().second)
    except TypeError:
        utils.get_logger().info(f'Error raised on API key {key}')

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
        if request['error']['code'] == 13 or request['error']['code'] == 10 or request['error']['code'] == 2:
            user = utils.first(UserModel.objects(key=key))
            if user is not None:
                user.key = ''
                user.save()
                faction = utils.first(FactionModel.objects(tid=user.factionid))

                if key in faction.keys:
                    faction.keys.remove(key)

                faction.save()

                for server in user.servers:
                    server = utils.first(ServerModel.objects(sid=server))

                    if server is not None and user.tid in server.admins:
                        server.admins.remove(user.tid)
                    server.save()
            else:
                for faction in FactionModel.objects():
                    if key in faction.keys:
                        faction.keys.remove(key)
                    faction.save()
        elif request['error']['code'] == 7:
            user: UserModel = utils.first(UserModel.objects(key=key))
            user.factionaa = False
            user.save()

            faction: FactionModel = utils.first(FactionModel.objects(tid=user.factionid))
            if faction is not None and key in faction.keys:
                faction.keys.remove(key)
                faction.save()

        utils.get_logger().info(f'The Torn API has responded with error code {request["error"]["code"]} '
                                f'({request["error"]["error"]}) to {url}).')
        raise utils.TornError(request["error"]["code"])

    return request


@huey.task()
def discordget(endpoint, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'
    redis = get_redis()

    if session is None:
        request = requests.get(url, headers={'Authorization': f'Bot {redis.get("bottoken")}'})
    else:
        request = session.get(url, headers={'Authorization': f'Bot {redis.get("bottoken")}'})

    try:
        request_json = request.json()
    except:
        if str(request.status_code)[:1] != '2':
            utils.get_logger().warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint '
                f'"{endpoint}".')
            raise utils.NetworkingError(request.status_code)
        else:
            raise Exception

    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a fill list of error code
        # explanations

        utils.get_logger().info(f'The Discord API has responded with error code {request_json["code"]} '
                                f'({request_json["message"]}) to {url}).')
        if redis.get('dev'):
            utils.get_logger().debug(request_json)
        raise utils.DiscordError(request_json["code"])
    elif str(request.status_code)[:1] != '2':
        utils.get_logger().warning(f'The Discord API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    return request_json


@huey.task()
def discordpost(endpoint, payload, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'
    redis = get_redis()

    if session is None:
        request = requests.post(url, headers={'Authorization': f'Bot {redis.get("bottoken")}',
                                              'Content-Type': 'application/json'},
                                data=json.dumps(payload))
    else:
        request = session.post(url, headers={'Authorization': f'Bot {redis.get("bottoken")}',
                                             'Content-Type': 'application/json'},
                               data=json.dumps(payload))

    try:
        request_json = request.json()
    except:
        if str(request.status_code)[:1] != '2':
            utils.get_logger().warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint '
                f'"{endpoint}".')
            raise utils.NetworkingError(request.status_code)
        else:
            raise Exception

    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a fill list of error code
        # explanations

        utils.get_logger().info(f'The Discord API has responded with error code {request_json["code"]} '
                                f'({request_json["message"]}) to {url}).')
        if redis.get('dev'):
            utils.get_logger().debug(request_json)
        raise utils.DiscordError(request_json["code"])
    elif str(request.status_code)[:1] != '2':
        utils.get_logger().warning(f'The Discord API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    return request_json


@huey.task()
def discorddelete(endpoint, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'
    redis = get_redis()

    if session is None:
        request = requests.delete(url, headers={'Authorization': f'Bot {redis.get("bottoken")}',
                                                'Content-Type': 'application/json'})
    else:
        request = session.delete(url, headers={'Authorization': f'Bot {redis.get("bottoken")}',
                                               'Content-Type': 'application/json'})

    try:
        request_json = request.json()
    except:
        if str(request.status_code)[:1] != '2':
            utils.get_logger().warning(
                f'The Discord API has responded with status code {request.status_code} to endpoint '
                f'"{endpoint}".')
            raise utils.NetworkingError(request.status_code)
        else:
            raise Exception

    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a fill list of error code
        # explanations

        utils.get_logger().info(f'The Discord API has responded with error code {request_json["code"]} '
                                f'({request_json["message"]}) to {url}).')
        if redis.get('dev'):
            utils.get_logger().debug(request_json)
        raise utils.DiscordError(request_json["code"])
    elif str(request.status_code)[:1] != '2':
        utils.get_logger().warning(f'The Discord API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    return request_json


def torn_stats_get(endpoint, key, session=None):
    url = f'https://www.tornstats.com/api/v1/{key}/{endpoint}'

    redis = get_redis()
    if redis.get(f'ts-{key}') is None:
        redis.set(f'ts-{key}', 15)
        redis.expire(f'ts-{key}', 60 - datetime.datetime.utcnow().second)
    if redis.ttl(f'ts-{key}') < 0:
        redis.expire(f'ts-{key}', 1)

    if int(redis.get(f'ts-{key}')) > 0:
        redis.decrby(f'ts-{key}', 1)
    else:
        time.sleep(60 - datetime.datetime.utcnow().second)

    if session is None:  # Utilizes https://docs.python-requests.org/en/latest/user/advanced/#session-objects
        request = requests.get(url)
    else:
        request = session.get(url)

    if request.status_code != 200:
        utils.get_logger().warning(f'The Torn API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    request = request.json()
    return request


@huey.periodic_task(crontab(minute='0'))
def refresh_factions():
    requests_session = requests.Session()

    for faction in FactionModel.objects():
        if len(faction.keys) == 0:
            continue

        try:
            faction_data = tornget.call_local(f'faction/?selections=', random.choice(faction.keys),
                                              session=requests_session)
        except Exception as e:
            utils.get_logger().exception(e)
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

        keys = []

        leader = utils.first(UserModel.objects(tid=faction.leader))
        coleader = utils.first(UserModel.objects(tid=faction.coleader))

        if leader is not None and leader.key != '':
            keys.append(leader.key)
        if coleader is not None and coleader.key != '':
            keys.append(coleader.key)

        for member_id, member in faction_data['members'].items():
            user = utils.first(UserModel.objects(tid=int(member_id)))

            if user is None:
                user = UserModel(
                    tid=int(member_id),
                    name=member['name'],
                    level=member['level'],
                    last_refresh=utils.now(),
                    admin=False,
                    key='',
                    battlescore=0,
                    battlescore_update=utils.now(),
                    discord_id=0,
                    servers=[],
                    factionid=faction.tid,
                    factionaa=False,
                    chain_hits=0,
                    status=member['last_action']['status'],
                    last_action=member['last_action']['timestamp']
                )
                user.save()

            user.name = member['name']
            user.level = member['level']
            user.last_refresh = utils.now()
            user.factionid = faction.tid
            user.status = member['last_action']['status']
            user.last_action = member['last_action']['timestamp']
            user.save()

            if user.key == '' and len(keys) != 0:
                try:
                    user_data = torn_stats_get(f'spy/{user.tid}', random.choice(keys), session=requests_session)
                except Exception as e:
                    utils.get_logger().exception(e)
                    continue

                if not user_data['status']:
                    continue
                elif not user_data['spy']['status']:
                    continue
                elif user_data['spy']['type'] != 'faction-share':
                    continue

                user.battlescore = user_data['spy']['target_score']
                user.strength = user_data['spy']['strength']
                user.defense = user_data['spy']['defense']
                user.speed = user_data['spy']['speed']
                user.dexterity = user_data['spy']['dexterity']
                user.battlescore_update = utils.now()
                user.save()

        if faction.chainconfig['od'] == 1:
            try:
                faction_od = tornget.call_local('faction/?selections=contributors',
                                                stat='drugoverdoses',
                                                key=random.choice(faction.keys),
                                                session=requests_session)
            except Exception as e:
                utils.get_logger().exception(e)
                continue

            if len(faction.chainod) != 0:
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
                            discordpost.call_local(f'channels/{faction.chainconfig["odchannel"]}/messages', payload=payload)
                        except Exception as e:
                            utils.get_logger().exception(e)
                            continue

            faction.chainod = faction_od['contributors']['drugoverdoses']

        faction.save()


@huey.periodic_task(crontab(minute='30'))
def refresh_guilds():
    requests_session = requests.Session()

    try:
        guilds = discordget.call_local('users/@me/guilds', session=requests_session)
    except Exception as e:
        utils.get_logger().exception(e)
        return

    for guild in guilds:
        try:
            members = discordget.call_local(f'guilds/{guild["id"]}/members', session=requests_session)
        except utils.DiscordError as e:
            if int(str(e)) == 10007:
                continue
            else:
                utils.get_logger().exception(e)
                return
        except Exception as e:
            utils.get_logger().exception(e)
            continue

        try:
            guild = discordget.call_local(f'guilds/{guild["id"]}', session=requests_session)
        except Exception as e:
            utils.get_logger().exception(e)
            continue

        owner = utils.first(UserModel.objects(discord_id=guild['owner_id']))

        if owner is not None:
            owner.servers.append(guild['id'])
            owner.servers = list(set(owner.servers))
            owner.save()

        for member in members:
            user = utils.first(UserModel.objects(discord_id=member['user']['id']))

            if user is not None:
                for role in member['roles']:
                    for guild_role in guild['roles']:
                        # Checks if the user has the role and the role has the administrator permission
                        if guild_role['id'] == role and (int(guild_role['permissions']) & 0x0000000008) == 0x0000000008:
                            user.servers.append(guild['id'])

                user.servers = list(set(user.servers))
                user.save()


@huey.periodic_task(crontab(minute='0'))
def refresh_users():
    requests_session = requests.Session()
    timestamp = utils.now()

    for user in UserModel.objects(key__ne=''):
        if user.key == '':
            continue

        try:
            user_data = tornget.call_local(f'user/?selections=profile,battlestats,discord', user.key,
                                           session=requests_session)
        except Exception as e:
            utils.get_logger().exception(e)
            continue

        user: UserModel = utils.first(UserModel.objects(_id=user_data['player_id']))
        user.factionid = user_data['faction']['faction_id']
        user.name = user_data['name']
        user.last_refresh = timestamp
        user.status = user_data['last_action']['status']
        user.last_action = user_data['last_action']['timestamp']
        user.level = user_data['level']
        user.discord_id = user_data['discord']['discordID'] if user_data['discord']['discordID'] != '' else 0
        user.factiontid = user_data['faction']['faction_id']
        user.strength = user_data['strength']
        user.defense = user_data['defense']
        user.speed = user_data['speed']
        user.dexterity = user_data['dexterity']

        battlescore = math.sqrt(user_data['strength']) + math.sqrt(user_data['defense']) + \
                      math.sqrt(user_data['speed']) + math.sqrt(user_data['dexterity'])
        user.battlescore = battlescore
        user.battlescore_update = timestamp
        user.save()

    for user in UserModel.objects(key__ne=''):
        if user.key == '':
            continue

        try:
            tornget.call_local(f'faction/?selections=positions', user.key, session=requests_session)
        except Exception as e:
            utils.get_logger().exception(e)
            continue

        user.factionaa = True
        user.save()


@huey.periodic_task(crontab(minute='*/5'))
def fetch_attacks():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    requests_session = requests.Session()
    timestamp = utils.now()
    statid = StatModel.objects().count()
    try:
        last_timestamp = utils.first(StatModel.objects(statid=statid - 1)).timeadded
    except AttributeError:
        last_timestamp = 0

    for faction in FactionModel.objects():
        if len(faction.keys) == 0:
            continue
        elif faction.config['stats'] == 0:
            continue

        try:
            faction_data = tornget.call_local('faction/?selections=basic,attacks',
                                              random.choice(faction.keys),
                                              session=requests_session)
        except Exception as e:
            utils.get_logger().exception(e)
            continue

        for attack in faction_data['attacks'].values():
            if attack['defender_faction'] == faction_data['ID']:
                continue
            elif attack['result'] in ['Assist', 'Lost', 'Stalemate', 'Escape']:
                continue
            elif attack['defender_id'] in [4, 10, 15, 17, 19, 20, 21]:  # Checks if NPC fight (and you defeated NPC)
                continue
            elif attack['modifiers']['fair_fight'] == 3:  # 3x FF can be greater than the defender battlescore indicated
                continue
            elif attack['timestamp_ended'] < last_timestamp:
                continue

            user = utils.first(UserModel.objects(tid=attack['attacker_id']))

            if user is None:
                try:
                    user_data = tornget.call_local(f'user/{attack["attacker_id"]}/?selections=profile,discord',
                                                   random.choice(faction.keys),
                                                   session=requests_session)

                    user = UserModel(
                        tid=attack['attacker_id'],
                        name=user_data['name'],
                        level=user_data['level'],
                        admin=False,
                        key='',
                        battlescore=0,
                        battlescore_update=timestamp,
                        discord_id=user_data['discord']['discordID'] if user_data['discord']['discordID'] != '' else 0,
                        servers=[],
                        factionid=user_data['faction']['faction_id'],
                        factionaa=False,
                        last_refresh=timestamp,
                        chain_hits=0,
                        status=user_data['last_action']['status'],
                        last_action=user_data['last_action']['timestamp']
                    )
                    user.save()
                except Exception as e:
                    utils.get_logger().exception(e)
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

            stat_faction = utils.first(FactionModel.objects(tid=user.factionid))

            if stat_faction is None:
                globalstat = 1
            else:
                globalstat = stat_faction.statconfig['global']

            stat_entry = StatModel(
                statid=statid,
                tid=attack['defender_id'],
                battlescore=defender_score,
                timeadded=timestamp,
                addedid=attack['attacker_id'],
                addedfactiontid=user.factionid,
                globalstat=globalstat
            )
            stat_entry.save()
            statid += 1


@huey.periodic_task(crontab())
def update_user_stakeouts():
    requests_session = requests.Session()

    for stakeout in UserStakeoutModel.objects():
        user_stakeout(stakeout.tid, requests_session=requests_session)()


@huey.periodic_task(crontab())
def update_faction_stakeouts():
    requests_session = requests.Session()

    for stakeout in FactionStakeoutModel.objects():
        faction_stakeout(stakeout.tid, requests_session=requests_session)()


@huey.task()
def user_stakeout(stakeout, requests_session=None, key=None):
    # TODO: Add try and except to tornget, discordget, and discordpost
    stakeout = utils.first(UserStakeoutModel.objects(tid=stakeout))

    try:
        if key is not None:
            data = tornget.call_local(f'user/{stakeout.tid}?selections=', key=key, session=requests_session)
        else:
            guild = utils.first(ServerModel.objects(sid=int(random.choice(list(stakeout.guilds)))))
            if guild is None and len(list(stakeout.guild)) == 1:
                return
            elif guild is None and len(list(stakeout.guilds)) > 1:
                guilds = random.sample(list(stakeout.guilds), k=len(list(stakeout.guilds)))
                guild_discorvered = False
                for guild in guilds:
                    guild = utils.first(ServerModel.objects(sid=int(guild)))
                    if guild is not None and len(guild.admins) != 0:
                        guild_discorvered = True
                        break
                if not guild_discorvered:
                    return

            admin = utils.first(UserModel.objects(tid=random.choice(guild.admins)))
            data = tornget.call_local(f'user/{stakeout.tid}?selections=', key=admin.key, session=requests_session)
    except Exception as e:
        utils.get_logger().exception(e)
        return

    stakeout_data = stakeout.data
    stakeout.lastupdate = utils.now()
    stakeout.data = data
    stakeout.save()

    for guildid, guild_stakeout in stakeout.guilds.items():
        if len(guild_stakeout['keys']) == 0:
            continue

        server = utils.first(ServerModel.objects(sid=guildid))

        if server.config['stakeouts'] == 0:
            continue

        if 'level' in guild_stakeout['keys'] and data['level'] != stakeout_data['level']:
            payload = {
                'embeds': [
                    {
                        'title': 'Level Change',
                        'description': f'The level of staked out user {data["name"]} has changed from '
                                       f'{stakeout_data["level"]} to {data["level"]}.',
                        'timestamp': datetime.datetime.utcnow().isoformat(),
                        'footer': {
                            'text': utils.torn_timestamp()
                        }
                    }
                ]
            }
            try:
                discordpost.call_local(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)
            except Exception as e:
                utils.get_logger().exception(e)
                return

        if 'status' in guild_stakeout['keys'] and data['status']['state'] != stakeout_data['status']['state']:
            payload = {
                'embeds': [
                    {
                        'title': 'Status Change',
                        'description': f'The status of staked out user {data["name"]} has changed from '
                                       f'{stakeout_data["status"]["state"]} to {data["status"]["state"]}.',
                        'timestamp': datetime.datetime.utcnow().isoformat(),
                        'footer': {
                            'text': utils.torn_timestamp()
                        }
                    }
                ]
            }
            try:
                discordpost.call_local(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)
            except Exception as e:
                utils.get_logger().exception(e)
                return

        if 'flyingstatus' in guild_stakeout['keys'] and \
                (data['status']['state'] in ['Travelling', 'In'] or
                 stakeout_data['status']['state'] in ['Travelling', 'In']) \
                and data['status']['state'] != stakeout_data['status']['state']:
            payload = {
                'embeds': [
                    {
                        'title': 'Flying Status Change',
                        'description': f'The flying status of staked out user {data["name"]} has changed from '
                                       f'{stakeout_data["status"]["state"]} to {data["status"]["state"]}.',
                        'timestamp': datetime.datetime.utcnow().isoformat(),
                        'footer': {
                            'text': utils.torn_timestamp()
                        }
                    }
                ]
            }
            try:
                discordpost.call_local(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)
            except Exception as e:
                utils.get_logger().exception(e)
                return

        if 'online' in guild_stakeout['keys'] and data['last_action']['status'] == 'Online' \
                and stakeout_data['last_action']['status'] in ['Offline', 'Idle']:
            payload = {
                'embeds': [
                    {
                        'title': 'Activity Change',
                        'description': f'The activity of staked out user {data["name"]} has changed from '
                                       f'{stakeout_data["last_action"]["status"]} to {data["last_action"]["status"]}.',
                        'timestamp': datetime.datetime.utcnow().isoformat(),
                        'footer': {
                            'text': utils.torn_timestamp()
                        }
                    }
                ]
            }
            try:
                discordpost.call_local(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)
            except Exception as e:
                utils.get_logger().exception(e)
                return

        if 'offline' in guild_stakeout['keys'] and data['last_action']['status'] in ['Offline', 'Idle'] and \
                stakeout_data['last_action']['status'] in ['Online', 'Idle'] and \
                data['last_action']['status'] != stakeout_data['last_action']['status']:
            if data['last_action']['status'] == 'Idle' and datetime.datetime.utcnow().timestamp() - \
                    data['last_action']['timestamp'] < 300:
                continue
            elif data['last_action']['status'] == 'Idle' and stakeout_data['last_action']['status'] == 'Idle':
                continue

            payload = {
                'embeds': [
                    {
                        'title': 'Activity Change',
                        'description': f'The activity of staked out user {data["name"]} has changed from '
                                       f'{stakeout_data["last_action"]["status"]} to {data["last_action"]["status"]}.',
                        'timestamp': datetime.datetime.utcnow().isoformat(),
                        'footer': {
                            'text': utils.torn_timestamp()
                        }
                    }
                ]
            }
            try:
                discordpost.call_local(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)
            except Exception as e:
                utils.get_logger().exception(e)
                return


@huey.task()
def faction_stakeout(stakeout, requests_session=None, key=None):
    # TODO: Add try and except to tornget, discordget, and discordpost
    stakeout = utils.first(FactionStakeoutModel.objects(tid=stakeout))

    try:
        if key is not None:
            data = tornget.call_local(f'faction/{stakeout.tid}?selections=basic,territory', key=key,
                                      session=requests_session)
        else:
            guild = utils.first(ServerModel.objects(sid=int(random.choice(list(stakeout.guilds)))))
            if guild is None and len(list(stakeout.guild)) == 1:
                return
            elif guild is None and len(list(stakeout.guilds)) > 1:
                guilds = random.sample(list(stakeout.guilds), k=len(list(stakeout.guilds)))
                guild_discorvered = False
                for guild in guilds:
                    guild = utils.first(ServerModel.objects(sid=int(guild)))
                    if guild is not None and len(guild.admins) != 0:
                        guild_discorvered = True
                        break
                if not guild_discorvered:
                    return

            admin = utils.first(UserModel.objects(tid=random.choice(guild.admins)))
            data = tornget.call_local(f'faction/{stakeout.tid}?selections=basic,territory', key=admin.key,
                                      session=requests_session)
    except Exception as e:
        utils.get_logger().exception(e)
        return

    stakeout_data = stakeout.data
    stakeout.lastupdate = utils.now()
    stakeout.data = data
    stakeout.save()

    for guildid, guild_stakeout in stakeout.guilds.items():
        if len(guild_stakeout['keys']) == 0:
            continue

        server = utils.first(ServerModel.objects(sid=guildid))

        if server.config['stakeouts'] == 0:
            continue

        # stakeout_data: data from the previous minute
        # data: data from this minute

        if 'territory' in guild_stakeout['keys'] and data['territory'] != stakeout_data['territory']:
            for territoryid, territory in stakeout_data['territory'].items():
                if territoryid not in data['territory']:
                    payload = {
                        'embeds': [
                            {
                                'title': 'Territory Removed',
                                'description': f'The territory {territoryid} of faction {data["name"]} has '
                                               f'been dropped.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
                elif 'racket' in territory and 'racket' not in data['territory'][territoryid]:
                    payload = {
                        'embeds': [
                            {
                                'title': 'Racket Lost',
                                'description': f'A racket has been lost on {territoryid}, controlled by faction '
                                               f'{data["name"]}. The racket was {data["territory"]["racket"]["name"]} '
                                               f'and gave {territory["territory"]["racket"]["reward"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return

            for territoryid, territory in data['territory'].items():
                if territoryid not in stakeout_data['territory']:
                    payload = {
                        'embeds': [
                            {
                                'title': 'Territory Gained',
                                'description': f'The territory {territoryid} has been claimed by '
                                               f'faction {data["name"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
                if 'racket' in territory and 'racket' not in stakeout_data['territory'][territoryid]:
                    payload = {
                        'embeds': [
                            {
                                'title': 'Racket Gained',
                                'description': f'A racket on {territoryid} has been controlled by faction '
                                               f'{data["name"]}. The racket is '
                                               f'{data["territory"]["racket"]["name"]} and '
                                               f'gives {data["territory"]["racket"]["reward"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
                elif territory['racket']['level'] > stakeout_data['territory'][territoryid]['racket']['level']:
                    payload = {
                        'embeds': [
                            {
                                'title': 'Racket Leveled Up',
                                'description': f'A racket on {territoryid} controlled by faction {data["name"]}. '
                                               f'The racket is {territory["racket"]["name"]} and now '
                                               f'gives {territory["racket"]["reward"]} from '
                                               f'{stakeout_data["territory"][territoryid]["racket"]["reward"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
                elif territory['racket']['level'] > stakeout_data['territory'][territoryid]['racket']['level']:
                    payload = {
                        'embeds': [
                            {
                                'title': 'Racket Leveled Down',
                                'description': f'A racket on {territoryid} controlled by faction {data["name"]}. '
                                               f'The racket is {territory["racket"]["name"]} and now '
                                               f'gives {territory["racket"]["reward"]} from '
                                               f'{stakeout_data["territory"][territoryid]["racket"]["reward"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
        if 'members' in guild_stakeout['keys'] and data['members'] != stakeout_data['members']:
            for memberid, member in stakeout_data['members'].items():
                if memberid not in data['members']:
                    payload = {
                        'embeds': [
                            {
                                'title': 'Member Left',
                                'description': f'Member {member["name"]} has left faction {data["name"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return

            for memberid, member in data['members'].items():
                if memberid not in stakeout_data['members']:
                    payload = {
                        'embeds': [
                            {
                                'title': 'Member Joined',
                                'description': f'Member {member["name"]} has joined faction {data["name"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
        if 'memberstatus' in guild_stakeout['keys'] and data['members'] != stakeout_data['members']:
            for memberid, member in stakeout_data['members'].items():
                if memberid not in data['members']:
                    continue
                elif member['status']['description'] != data['members'][memberid]['status']['description'] \
                        or member["status"]["state"] != data["members"][memberid]["status"]["state"]:
                    if member['status']['details'] == data['members'][memberid]['status']['details']:
                        continue

                    payload = {
                        'embeds': [
                            {
                                'title': 'Member Status Change',
                                'description': f'Member {member["name"]} of faction {data["name"]} is now '
                                               f'{data["members"][memberid]["status"]["description"]} from '
                                               f'{member["status"]["description"]}'
                                               f'{"" if member["status"]["details"] == "" else " because " + utils.remove_html(member["status"]["details"])}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
        if 'memberactivity' in guild_stakeout['keys'] and data['members'] != stakeout_data['members']:
            for memberid, member in stakeout_data['members'].items():
                if memberid not in data['members']:
                    continue

                if member['last_action']['status'] in ('Offline', 'Idle') and data['members'][memberid]['last_action'][
                    'status'] == 'Online':
                    if data["members"][memberid]["last_action"]["status"] == "Idle" and \
                            datetime.datetime.now(datetime.timezone.utc).timestamp() - \
                            data["members"][memberid]["last_action"]["timestamp"] < 300:
                        continue

                    payload = {
                        'embeds': [
                            {
                                'title': 'Member Activity Change',
                                'description': f'Member {member["name"]} of faction {data["name"]} is now '
                                               f'{data["members"][memberid]["last_action"]["status"]} from '
                                               f'{member["last_action"]["status"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
                elif member['last_action']['status'] in ('Online', 'Idle') and \
                        data['members'][memberid]['last_action']['status'] in ('Offline', 'Idle'):
                    if data['members'][memberid]['last_action']['status'] == 'Idle' and \
                            datetime.datetime.now(datetime.timezone.utc).timestamp() - \
                            data["members"][memberid]["last_action"]["timestamp"] < 300:
                        continue
                    elif data["members"][memberid]["last_action"]["status"] == "Idle" \
                            and member["last_action"]["status"] == "Idle":
                        continue

                    payload = {
                        'embeds': [
                            {
                                'title': 'Member Activity Change',
                                'description': f'Member {member["name"]} of faction {data["name"]} is now '
                                               f'{data["members"][memberid]["last_action"]["status"]} from '
                                               f'{member["last_action"]["status"]}.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
        if 'assault' in guild_stakeout['keys'] and data['territory_wars'] != stakeout_data['territory_wars']:
            for war in data['territory_wars']:
                existing = False

                for old_war in stakeout_data['territory_wars']:
                    if old_war['territory'] == war['territory']:
                        existing = True
                        break

                if not existing:
                    defending = utils.first(FactionModel.objects(tid=war['defending_faction']))
                    assaulting = utils.first(FactionModel.objects(tid=war['assaulting_faction']))

                    payload = {
                        'embeds': [
                            {
                                'title': 'Territory Assaulted',
                                'description': f'Territory {war["territory"]} of faction '
                                               f'{war["defending_faction"] if defending is None else defending.name}'
                                               f' has been assaulted by faction '
                                               f'{war["assaulting_faction"] if assaulting is None else assaulting.name}.',
                                'timestamp': datetime.datetime.fromtimestamp(war["start_time"]).isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp(war["start_time"])
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
            for war in stakeout_data['territory_wars']:
                existing = False

                for new_war in data['territory_wars']:
                    if new_war['territory'] == war['territory']:
                        existing = True
                        break

                if not existing:
                    defending = utils.first(FactionModel.objects(tid=war['defending_faction']))
                    assaulting = utils.first(FactionModel.objects(tid=war['assaulting_faction']))
                    payload = {
                        'embeds': [
                            {
                                'title': 'Territory Assault Ended',
                                'description': f'The assault of territory {war["territory"]} of faction '
                                               f'{war["defending_faction"] if defending is None else defending.name}'
                                               f' by faction '
                                               f'{war["assaulting_faction"] if assaulting is None else assaulting.name}.'
                                               f'has ended.',
                                'timestamp': datetime.datetime.utcnow().isoformat(),
                                'footer': {
                                    'text': utils.torn_timestamp()
                                }
                            }
                        ]
                    }
                    try:
                        discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                    except Exception as e:
                        utils.get_logger().exception(e)
                        return
        if 'armory' in guild_stakeout['keys']:
            server = utils.first(ServerModel.objects(sid=guildid))
            faction = utils.first(FactionModel.objects(tid=stakeout.tid))

            if stakeout.tid in server.factions and faction.guild == int(guildid):
                try:
                    if key is not None:
                        data = tornget.call_local(f'faction/{stakeout.tid}?selections=armorynews',
                                                  key=key,
                                                  session=requests_session,
                                                  fromts=utils.now() - 60)
                    elif len(faction.keys) == 0:
                        break
                    else:
                        data = tornget.call_local(f'faction/{stakeout.tid}?selections=armorynews',
                                                  key=random.choice(faction.keys),
                                                  session=requests_session,
                                                  fromts=utils.now() - 60)
                except Exception as e:
                    utils.get_logger().exception(e)
                    break

                if len(data['armorynews']) == 0:
                    break

                for news in data['armorynews'].values():
                    timestamp = news['timestamp']
                    news = utils.remove_html(news['news'])

                    if any(word in news.lower() for word in ['loaned', 'returned', 'retrieved']):
                        payload = {
                            'embeds': [
                                {
                                    'title': 'Armory Change',
                                    'description': news,
                                    'timestamp': datetime.datetime.utcnow().isoformat(),
                                    'footer': {
                                        'text': utils.torn_timestamp(timestamp)
                                    }
                                }
                            ]
                        }

                        try:
                            discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                        except Exception as e:
                            utils.get_logger().exception(e)
                            return

                        pass
        if 'armorydeposit' in guild_stakeout['keys']:
            server = utils.first(ServerModel.objects(sid=guildid))
            faction = utils.first(FactionModel.objects(tid=stakeout.tid))
            if stakeout.tid in server.factions and faction.guild == int(guildid):
                try:
                    if key is not None:
                        data = tornget.call_local(f'faction/{stakeout.tid}?selections=armorynews',
                                                  key=key,
                                                  session=requests_session,
                                                  fromts=utils.now() - 60)
                    elif len(faction.keys) == 0:
                        break
                    else:
                        data = tornget.call_local(f'faction/{stakeout.tid}?selections=armorynews',
                                                  key=random.choice(faction.keys),
                                                  session=requests_session,
                                                  fromts=utils.now() - 60)
                except Exception as e:
                    utils.get_logger().exception(e)
                    break

                if len(data['armorynews']) == 0:
                    break

                for news in data['armorynews'].values():
                    timestamp = news['timestamp']
                    news = utils.remove_html(news['news'])

                    if any(word in news.lower() for word in ['deposited']):
                        payload = {
                            'embeds': [
                                {
                                    'title': 'Armory Deposit',
                                    'description': news,
                                    'timestamp': datetime.datetime.utcnow().isoformat(),
                                    'footer': {
                                        'text': utils.torn_timestamp(timestamp)
                                    }
                                }
                            ]
                        }

                        try:
                            discordpost(f'channels/{guild_stakeout["channel"]}/messages', payload=payload)()
                        except Exception as e:
                            utils.get_logger().exception(e)
                            return

                        pass
