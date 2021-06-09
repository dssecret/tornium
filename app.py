# This file is part of torn-command.
#
# torn-command is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# torn-command is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with torn-command.  If not, see <https://www.gnu.org/licenses/>.

import logging
import os

import flask
from flask_login import LoginManager
from flask_migrate import Migrate

from controllers import mod as base_mod
from controllers.devroutes import mod as dev_mod
from controllers.authroutes import mod as auth_mod
from controllers.factionroutes import mod as faction_mod
from controllers.botroutes import mod as bot_mod
from models import settingsmodel as settings
from models.usermodel import db as userdb
from models.factionmodel import db as factiondb

settings.initialize()

logger = logging.getLogger('server')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=f'{settings.settingsdir()}server.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

app = flask.Flask(__name__)
app.secret_key = settings.get("settings", "secret")
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'authroutes.login'
login_manager.session_protection = 'strong'

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(settings.settingsdir(), "data.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
userdb.init_app(app)
factiondb.init_app(app)
usermigrate = Migrate(app, userdb)
factionmigrate = Migrate(app, factiondb)

with app.app_context():
    userdb.create_all()
    factiondb.create_all()


@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User(user_id)


if settings.get("settings", "dev") and __name__ == "__main__":
    app.register_blueprint(base_mod)
    app.register_blueprint(dev_mod)
    app.register_blueprint(auth_mod)
    app.register_blueprint(faction_mod)
    app.register_blueprint(bot_mod)
    app.run('localhost', 8000, debug=True)

if not settings.get("settings", "dev"):
    app.register_blueprint(base_mod)
    app.register_blueprint(auth_mod)
    app.register_blueprint(faction_mod)
    app.register_blueprint(bot_mod)
