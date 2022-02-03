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

from celery import Celery
from celery.schedules import crontab
import requests

from redisdb import get_redis


celery_app: Celery


def make_celery(app):
    try:
        file = open('celery.json')
        file.close()
    except FileNotFoundError:
        data = {
            'honeybadger-site-checkin': {
                'task': 'tasks.honeybadger_site_checkin',
                'schedule': {
                    'type': 'cron',
                    'minute': '*',
                    'hour': '*'
                }
            }
        }

        with open('celery.json', 'w') as file:
            json.dump(data, file, indent=4)

    with open('celery.json', 'r') as file:
        data = json.load(file)

    global celery_app
    celery_app = Celery(
        app.import_name,
        backend='redis://localhost:6379/0',
        broker='redis://localhost:6379/0',
        include=['tasks', 'tasks.faction']
    )
    celery_app.conf.update(
        task_serializer='json',
        result_serializer='json'
    )
    celery_app.conf.timezone = 'UTC'
    celery_app.conf.beat_schedule = {
        'honeybadger-site-checkin': {
            'task': 'tasks.honeybadger_site_checkin',
            'schedule': crontab(
                minute=data['honeybadger-site-checkin']['schedule']['minute'],
                hour=data['honeybadger-site-checkin']['schedule']['hour']
            )
        }
    }

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


@celery_app.task
def honeybadger_site_checkin():
    redis = get_redis()

    if redis.get('honeysitecheckin') is None or redis.get('honeysitecheckin') == '':
        return
    elif redis.get('url') is None or redis.get('url') == '':
        return

    site = requests.get(redis.get('url'))

    if site.status_code != requests.codes.ok:
        return

    requests.get(redis.get("honeysitecheckin"))
