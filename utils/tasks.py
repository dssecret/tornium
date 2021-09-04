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
import random

from huey import SqliteHuey, crontab
import requests

from database import session_local
from models import settingsmodel
from models.factionmodel import FactionModel
from models.factionstakeoutmodel import FactionStakeoutModel
from models.servermodel import ServerModel
from models.statmodel import StatModel
from models.usermodel import UserModel, UserDiscordModel
from models.userstakeoutmodel import UserStakeoutModel
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

    if str(request.status_code)[:1] != '2':
        utils.get_logger().warning(f'The Discord API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    request_json = request.json()

    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a fill list of error code
        # explanations

        utils.get_logger().info(f'The Discord API has responded with error code {request_json["code"]} '
                                f'({request_json["message"]}) to {url}).')
        raise utils.DiscordError(request_json["code"])

    return request_json


@huey.task()
def discordpost(endpoint, payload, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'

    if session is None:
        request = requests.post(url, headers={'Authorization': f'Bot {settingsmodel.get("settings", "bottoken")}',
                                              'Content-Type': 'application/json'},
                                data=json.dumps(payload))
    else:
        request = session.post(url, headers={'Authorization': f'Bot {settingsmodel.get("settings", "bottoken")}',
                                             'Content-Type': 'application/json'},
                               data=json.dumps(payload))

    if str(request.status_code)[:1] != '2':
        utils.get_logger().warning(f'The Discord API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    request_json = request.json()

    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a fill list of error code
        # explanations

        utils.get_logger().info(f'The Discord API has responded with error code {request_json["code"]} '
                                f'({request_json["message"]}) to {url}).')
        raise utils.DiscordError(request_json["code"])

    return request_json


@huey.task()
def discorddelete(endpoint, session=None):
    url = f'https://discord.com/api/v9/{endpoint}'

    if session is None:
        request = requests.delete(url, headers={'Authorization': f'Bot {settingsmodel.get("settings", "bottoken")}',
                                                'Content-Type': 'application/json'})
    else:
        request = session.delete(url, headers={'Authorization': f'Bot {settingsmodel.get("settings", "bottoken")}',
                                               'Content-Type': 'application/json'})

    if str(request.status_code)[:1] != '2':
        utils.get_logger().warning(f'The Discord API has responded with status code {request.status_code} to endpoint '
                                   f'"{endpoint}".')
        raise utils.NetworkingError(request.status_code)

    request_json = request.json()

    if 'code' in request_json:
        # See https://discord.com/developers/docs/topics/opcodes-and-status-codes#json for a fill list of error code
        # explanations

        utils.get_logger().info(f'The Discord API has responded with error code {request_json["code"]} '
                                f'({request_json["message"]}) to {url}).')
        raise utils.DiscordError(request_json["code"])

    return request_json


@huey.periodic_task(crontab(minute='0'))
def refresh_factions():
    session = session_local()
    requests_session = requests.Session()
    factions = []
    timestamp = utils.now()

    for faction in session.query(FactionModel).all():
        if len(json.loads(faction.keys)) == 0:
            continue

        factions.append(tornget(f'faction/?selections=', random.choice(json.loads(faction.keys)),
                                session=requests_session))

    for faction in factions:
        try:
            faction_data = faction(blocking=True)
        except:
            continue

        if faction_data is None:
            continue

        faction = session.query(FactionModel).filter_by(tid=faction_data['ID']).first()
        faction.name = faction_data['name']
        faction.respect = faction_data['respect']
        faction.capacity = faction_data['capacity']
        faction.leader = faction_data['leader']
        faction.coleader = faction_data['co-leader']

        for member_id, member in faction_data['members'].items():
            print(member)
            user = session.query(UserModel).filter_by(tid=int(member_id))
            user.name = member['name']
            user.level = member['level']
            user.last_refresh = timestamp
            user.factiontid = faction_data['ID']
            user.status = member['last_action']['status']
            user.last_action = member['last_action']['relative']

    session.flush()


@huey.periodic_task(crontab(minute='0'))
def refresh_users():
    session = session_local()
    requests_session = requests.Session()
    users = []
    timestamp = utils.now()

    guilds = discordget('users/@me/guilds', session=requests_session)
    guilds = guilds(blocking=True)

    for user in session.query(UserModel).all():
        if user.key == '':
            continue

        users.append(tornget(f'user/?selections=profile,battlestats,discord', user.key, session=requests_session))

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
        if discord_user is None and user.discord_id != '':
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
                member(blocking=True)
            except utils.DiscordError as e:
                if int(str(e)) == 10007:
                    break
                else:
                    return utils.handle_discord_error(str(e))
            except:
                continue

            try:
                guild = discordget(f'guilds/{guild["id"]}', session=requests_session)
                guild = guild(blocking=True)
            except utils.DiscordError as e:
                return utils.handle_discord_error(str(e))
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


@huey.periodic_task(crontab(minute='*/5'))
def fetch_attacks():  # Based off of https://www.torn.com/forums.php#/p=threads&f=61&t=16209964&b=0&a=0&start=0&to=0
    session = session_local()
    requests_session = requests.Session()
    faction_attacks = []
    timestamp = utils.now()
    statid = session.query(StatModel).count()

    for faction in session.query(FactionModel).all():
        if len(json.loads(faction.keys)) == 0:
            continue
        elif json.loads(faction.config)['stat'] == 0:
            continue

        faction_attacks.append(tornget('faction/?selections=basic,attacks',
                                       random.choice(json.loads(faction.keys)),
                                       fromts=timestamp - 300,  # TODO: Adjust when the crontab timer is adjusted
                                       session=requests_session))  # TODO: Store last update per faction in DB

    for faction in faction_attacks:
        try:
            faction_data = faction(blocking=True)
        except:
            continue

        for attack in faction_data['attacks'].values():
            if attack['attacker_faction'] != faction_data['ID']:
                continue
            elif attack['result'] in ['Assist', 'Lost', 'Stalemate']:
                continue
            elif attack['defender_id'] in [4, 10, 15, 17, 19, 20, 21]:  # Checks if NPC fight (and you defeated NPC)
                continue
            elif attack['modifiers']['fair_fight'] == 3:  # 3x FF can be greater than the defender battlescore indicated
                continue

            user = session.query(UserModel).filter_by(tid=attack['attacker_id']).first()

            if user is None:
                user = UserModel(
                    tid=attack['attacker_id'],
                    name='',
                    level=0,
                    admin=False,
                    key='',
                    battlescore='[]',
                    discord_id=0,
                    servers='[]',
                    factionid=0,
                    factionaa=False,
                    last_refresh=timestamp,
                    status=''
                )
                session.add(user)
                session.flush()

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
            session.flush()
            statid += 1
        session.flush()


@huey.periodic_task(crontab())
def update_user_stakeouts():
    session = session_local()
    requests_session = requests.Session()

    for stakeout in session.query(UserStakeoutModel).all():
        user_stakeout(stakeout.tid, requests_session=requests_session)()


@huey.periodic_task(crontab())
def update_faction_stakeouts():
    session = session_local()
    requests_session = requests.Session()

    for stakeout in session.query(FactionStakeoutModel).all():
        faction_stakeout(stakeout.tid, requests_session=requests_session)()


@huey.task()
def user_stakeout(stakeout, requests_session=None, key=None):
    # TODO: Add try and except to tornget, discordget, and discordpost
    session = session_local()
    stakeout = session.query(UserStakeoutModel).filter_by(tid=stakeout).first()

    if key is not None:
        data = tornget(f'user/{stakeout.tid}?selections=', key=key, session=requests_session)
    else:
        guild = random.choice(list(json.loads(stakeout.guilds).keys()))
        guild = session.query(ServerModel).filter_by(sid=guild).first()
        admin = random.choice(json.loads(guild.admins))
        admin = session.query(UserModel).filter_by(tid=admin).first()
        data = tornget(f'user/{stakeout.tid}?selections=', key=admin.key, session=requests_session)

    data = data(blocking=True)
    stakeout_data = json.loads(stakeout.data)

    for guildid, guild_stakeout in json.loads(stakeout.guilds).items():
        if len(guild_stakeout['keys']) == 0:
            continue

        server = session.query(ServerModel).filter_by(sid=guildid).first()

        if json.loads(server.config)['stakeouts'] == 0:
            continue

        channels = discordget(f'guilds/{guildid}/channels', session=requests_session)
        channels = channels(blocking=True)

        for channel in channels:
            if channel['id'] == str(guild_stakeout['channel']):
                break
        else:
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
            discordpost(f'channels/{channel["id"]}/messages', payload=payload)()

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
            discordpost(f'channels/{channel["id"]}/messages', payload=payload)()

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
            discordpost(f'channels/{channel["id"]}/messages', payload=payload)()

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
            discordpost(f'channels/{channel["id"]}/messages', payload=payload)()

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
            discordpost(f'channels/{channel["id"]}/messages', payload=payload)()

    stakeout.lastupdate = utils.now()
    stakeout.data = json.dumps(data)
    session.flush()


@huey.task()
def faction_stakeout(stakeout, requests_session=None, key=None):
    # TODO: Add try and except to tornget, discordget, and discordpost
    session = session_local()
    stakeout = session.query(FactionStakeoutModel).filter_by(tid=stakeout).first()

    if key is not None:
        data = tornget(f'faction/{stakeout.tid}?selections=basic,territory', key=key, session=requests_session)
    else:
        guild = random.choice(list(json.loads(stakeout.guilds).keys()))
        guild = session.query(ServerModel).filter_by(sid=guild).first()
        admin = random.choice(json.loads(guild.admins))
        admin = session.query(UserModel).filter_by(tid=admin).first()
        data = tornget(f'faction/{stakeout.tid}?selections=basic,territory', key=admin.key, session=requests_session)

    data = data(blocking=True)
    stakeout_data = json.loads(stakeout.data)

    for guildid, guild_stakeout in json.loads(stakeout.guilds).items():
        if len(guild_stakeout['keys']) == 0:
            continue

        server = session.query(ServerModel).filter_by(sid=guildid).first()

        if json.loads(server.config)['stakeouts'] == 0:
            continue

        channels = discordget(f'guilds/{guildid}/channels', session=requests_session)
        channels = channels(blocking=True)

        for channel in channels:
            if channel['id'] == str(guild_stakeout['channel']):
                break
        else:
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()

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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()

            for memberid, member in data['members'].items():
                if memberid not in stakeout_data['members']:
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()
        if 'memberactivity' in guild_stakeout['keys'] and data['members'] != stakeout_data['members']:
            for memberid, member in stakeout_data['members'].items():
                if memberid not in data['members']:
                    continue

                if member['last_action']['status'] in ('Offline', 'Idle') and data['members'][memberid]['last_action']['status'] == 'Online':
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()
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
                    discordpost(f'channels/{channel["id"]}/messages', payload=payload)()

    stakeout.lastupdate = utils.now()
    stakeout.data = json.dumps(data)
    session.flush()
