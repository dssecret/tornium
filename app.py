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
import os

import flask
from flask_login import LoginManager
from sqlalchemy.orm import scoped_session

from controllers import mod as base_mod
from controllers.devroutes import mod as dev_mod
from controllers.authroutes import mod as auth_mod
from controllers.factionroutes import mod as faction_mod
from controllers.botroutes import mod as bot_mod
from controllers.errors import mod as error_mod
from controllers.adminroutes import mod as admin_mod
from controllers.statroutes import mod as stat_mod
from controllers.apiroutes import mod as api_mod
from database import session_local
from models import settingsmodel as settings
import utils

settings.initialize()

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='server.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

app = flask.Flask(__name__, instance_path=f'{os.getcwd()}/instance')  # Temp bug fix for https://youtrack.jetbrains.com/issue/PY-49984
app.secret_key = settings.get('secret')
app.session = scoped_session(session_local, scopefunc=flask._app_ctx_stack.__ident_func__)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'authroutes.login'
login_manager.refresh_view = 'authroutes.login'
login_manager.session_protection = 'basic'


@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User(user_id)


@app.template_filter('reltime')
def relative_time(s):
    return utils.rel_time(datetime.datetime.fromtimestamp(s))


if settings.get("dev") and __name__ == "__main__":
    app.register_blueprint(base_mod)
    app.register_blueprint(dev_mod)
    app.register_blueprint(auth_mod)
    app.register_blueprint(faction_mod)
    app.register_blueprint(bot_mod)
    app.register_blueprint(error_mod)
    app.register_blueprint(admin_mod)
    app.register_blueprint(stat_mod)
    app.register_blueprint(api_mod)

    app.run('localhost', 8000, debug=True)

if not settings.get("dev"):
    app.register_blueprint(base_mod)
    app.register_blueprint(auth_mod)
    app.register_blueprint(faction_mod)
    app.register_blueprint(bot_mod)
    app.register_blueprint(error_mod)
    app.register_blueprint(admin_mod)
    app.register_blueprint(dev_mod)
    app.register_blueprint(stat_mod)
    app.register_blueprint(api_mod)
