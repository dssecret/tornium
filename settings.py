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
        'host': '',
        'url': '',
        'honeyenv': 'production',
        'honeykey': '',
        'honeysitecheckin': '',
        'honeybotcheckin': '',
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
redis.set('url', data['url'])
redis.set('honeyenv', data['honeyenv'])
redis.set('honeykey', data['honeykey'])
redis.set('honeysitecheckin', data['honeysitecheckin'])
redis.set('honeybotcheckin', data['honeybotcheckin'])
