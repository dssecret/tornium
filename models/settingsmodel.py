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


def _read(file: str):
    """
    Reads the JSON file using _settingsfile as the root directory of the file
    """

    with open(f'{file}.json', 'r') as file:
        return json.load(file)


def _write(file: str, data):
    """
    Writes to the specified JSON file using the inputted (JSON formatted) data

    :param file: The name of the file to be written to (not including the .json file type)
    :param data: The JSON formatted data to be written to the specified file
    """

    with open(f'{file}.json', 'w') as file:
        json.dump(data, file, indent=4)


def initialize():
    """
    Initializes all necessary JSON files with base data if the file can't be found.
    """

    try:
        file = open('settings.json')
        file.close()
    except FileNotFoundError:
        data = {
            'jsonfiles': ['settings'],
            'dev': False,
            'banlist': [],
            'useragentlist': [],
            'bottoken': '',
            'secret': str(os.urandom(32)),
            'taskqueue': 'redis',
            'username': 'tornium',
            'password': ''
        }
        _write('settings', data)
    
    with open('settings.json', 'r') as file:
        data = json.load(file)
    
    redis = get_redis()
    redis.set('dev', data['dev'])
    redis.set('banlist', data['banlist'])
    redis.set('useragentlist', data['useragentlist'])
    redis.set('bottoken', data['bottoken'])
    redis.set('secret', data['secret'])
    redis.set('taskqueue', data['taskqueue'])
    redis.set('username', data['username'])
    redis.set('password', data['password'])


def get(key: str, redis=None):
    """
    Returns the value of the specified key from teh specified JSON file

    :param key: The key in the JSON file whose value is to be returned
    """
    if redis is None:
        redis = get_redis()
        redis.get(key)
    else:
        redis.get(key)
    


def update(key: str, value, redis=None):
    """
    Updates the value of the specified key in the specified JSON file

    :param key: The key in the JSON file whose value is to be updated
    :param value: The value the of the key in the JSON file shall be changed to
    """
    
    if redis is None:
        redis = get_redis()
        redis.set(key, value)
    else:
        redis.set(key, value)

    data = _read('settings')
    data[key] = value
    _write('settings', data)


def is_dev():
    redis = get_redis()
    return redis.get("dev")
